import socket
import ipaddress
import asyncio
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from urllib.parse import urlparse
from datetime import datetime

# SQLAlchemy Imports

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

# ML Model Imports
from app.ml.features import vectorize
from app.ml.model import phishing_ml_model

# Utilities
from app.utils.timer import ExecutionTimer
from app.utils.cache_manager import ScanCache

# Core and Models
from app.core.database import get_db
from app.core.models import User, ScanHistory, ScanResponseSchema
from app.core.security import verify_password, get_password_hash, create_access_token

# pre-checks
from app.pre_checks.pre_flight import safe_classify_url
from app.pre_checks.normalization import normalize_url
from app.pre_checks.fingerprinting import identify_link_type
from app.pre_checks.tracing import trace_redirects

# Analyzers
from app.analyzers.ssl_check import inspect_ssl, fetch_ct_logs, merge_ct_results
from app.analyzers.reputation import check_domain_reputation
from app.analyzers.lexical import check_lexical_risk
from app.analyzers.content_scan import inspect_content
from app.analyzers.ip_intel import check_ip_intel

# --- Utilities ---
from app.utils.scoring import calculate_risk_score
from app.services.ai_advisor import generate_security_explanation

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login", auto_error=False)


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class ScanRequest(BaseModel):
    url: str


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    from app.core.security import SECRET_KEY, ALGORITHM
    from jose import jwt, JWTError

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def validate_target_ip(hostname):
    try:
        ip = socket.gethostbyname(hostname)
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.is_private or ip_obj.is_loopback:
            raise HTTPException(
                status_code=400, detail="Scanning internal IPs is prohibited."
            )
        return True
    except socket.gaierror:
        pass
    except ValueError:
        pass
    return True


@router.post("/register")
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = get_password_hash(user.password)

    new_user = User(email=user.email, hashed_password=hashed_pw, full_name=user.full_name)
    db.add(new_user)
    await db.commit()
    return {"message": "User registered successfully"}


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token = create_access_token(data={"sub": user.email})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            # If full_name is None, send a default string instead to prevent React from crashing
            "name": user.full_name or "ScamShield User",
            "picture": user.profile_pic or "",
            # Force it to be a True/False boolean instead of null
            "is_admin": bool(user.is_admin),
        },
    }


@router.post("/scan")
async def analyze_url(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not request.url:
        raise HTTPException(status_code=400, detail="URL is required")
    target_url_raw = str(request.url)
    cached_result = ScanCache.get_url_cache(target_url_raw)
    if cached_result:
        print(f"[CACHE] URL CACHE HIT - Skipping all analysis for {target_url_raw}!")
        return cached_result

    try:
        normalized_url, hostname, norm_flags = normalize_url(request.url)
        validate_target_ip(hostname)

        trace = trace_redirects(normalized_url)
        target_url = trace.get("final_destination", normalized_url)
        target_hostname = urlparse(target_url).hostname or hostname

        if target_hostname != hostname:
            validate_target_ip(target_hostname)

        original_fingerprint = identify_link_type(normalized_url, hostname)
        fingerprint = identify_link_type(target_url, target_hostname)

        if original_fingerprint.get("is_shortened"):
            fingerprint["is_shortened"] = True
            fingerprint["provider"] = original_fingerprint.get("provider")

        cached_domain = ScanCache.get_domain_cache(target_hostname)

        if cached_domain:
            print(f" DOMAIN CACHE HIT - Using saved Network Data for {target_hostname}")

            ssl_data = cached_domain["ssl_data"]
            ip_intel = cached_domain["ip_intel"]
            reputation = cached_domain["reputation"]

            lexical, content_data = await asyncio.gather(
                asyncio.to_thread(check_lexical_risk, target_url, target_hostname),
                asyncio.to_thread(
                    inspect_content,
                    trace.get("html_content"),
                    target_url,
                    target_hostname,
                ),
            )
        else:
            print(
                f"[SCAN] FULL SCAN - Running all network modules CONCURRENTLY for {target_hostname}"
            )

            ct_data = ScanCache.get_ct_cache(target_hostname)
            if not ct_data:

                background_tasks.add_task(background_fetch_ct, target_hostname)
                ct_data = {
                    "status": "pending_background_fetch",
                    "ct_log_count": 0,
                    "ct_earliest_seen": "Pending background fetch...",
                    "ct_latest_seen": "Pending background fetch...",
                    "ct_check_failed": False,
                    "logs": [],
                }
            else:
                print(f"[CACHE] CT CACHE HIT - Loaded background logs for {target_hostname}")

            with ExecutionTimer("Total Concurrent Module Execution"):

                ssl_data, lexical, content_data, reputation, ip_intel = (
                    await asyncio.gather(
                        asyncio.to_thread(inspect_ssl, target_hostname),
                        asyncio.to_thread(
                            check_lexical_risk, target_url, target_hostname
                        ),
                        asyncio.to_thread(
                            inspect_content,
                            trace.get("html_content"),
                            target_url,
                            target_hostname,
                        ),
                        check_domain_reputation(target_url),
                        check_ip_intel(target_url),
                    )
                )

            ssl_data = merge_ct_results(ssl_data, ct_data)

            ScanCache.set_domain_cache(target_hostname, ip_intel, ssl_data, reputation)

    except socket.gaierror:
        return {
            "url": request.url,
            "risk_score": 0,
            "risk_level": "Unreachable",
            "details": {"error": "Domain does not exist"},
            "scan_time": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        print(f"Scan Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    ml_result = phishing_ml_model.score(lexical)
    print(f"[ML DEBUG] model loaded: {phishing_ml_model.loaded}")
    print(f"[ML DEBUG] raw probability: {ml_result['phishing_probability']}")
    print(f"[ML DEBUG] features: {vectorize(lexical)}")
    is_typosquat = lexical.typosquat_target is not None
    brand_detected = lexical.typosquat_target if is_typosquat else "None"
    suspicious_kw = bool(lexical.found_keywords)
    is_homograph = lexical.homograph_detected

    dom_age = reputation.get("domain_age_days")
    if dom_age is None:
        dom_status = "Unknown"
        dom_age_display = "Unknown"
    else:
        dom_status = "New (< 30 Days)" if dom_age < 30 else "Established"
        dom_age_display = f"{dom_age} days"

    is_sus_tld = reputation.get("is_suspicious_tld", False)
    whois_privacy = True

    link_cat = "Standard"
    if fingerprint.get("is_shortened"):
        link_cat = "Shortened"
    elif fingerprint.get("is_ip_based"):
        link_cat = "IP Address"
    elif fingerprint.get("is_download"):
        link_cat = "File/App"

    tags = fingerprint.get("tags", [])
    service_type = tags[0].title() if tags else "General Website"
    short_provider = fingerprint.get("provider")
    short_provider = short_provider.title() if short_provider else "None"
    is_obfuscated = "%" in request.url or "0x" in request.url

    hops = trace.get("hop_count", 0)
    parsed_start = urlparse(normalized_url)
    parsed_end = urlparse(target_url)
    start_domain = parsed_start.netloc
    end_domain = parsed_end.netloc
    cross_domain = start_domain != end_domain

    combined_scan_data = {
        "url": target_url,
        "has_ip_in_domain": lexical.has_ip_in_host,
        "url_length": lexical.url_length,
        "num_subdomains": lexical.subdomain_depth,
        "tld": f".{target_hostname.split('.')[-1]}" if "." in target_hostname else "",
        "ssl": ssl_data,
        "ip_intel": ip_intel,
        "is_blacklisted": reputation.get("is_blacklisted", False),
        "domain_age_days": reputation.get("domain_age_days", 999),
        "has_obfuscated_scripts": is_obfuscated,
        "entropy": lexical.entropy,
        "is_dga_candidate": lexical.is_dga_candidate,
        "typosquat_target": lexical.typosquat_target,
        "found_keywords": lexical.found_keywords,
        "homograph_detected": lexical.homograph_detected,
        "digit_ratio": lexical.digit_ratio,
        "special_char_count": lexical.special_char_count,
        "subdomain_depth": lexical.subdomain_depth,
        "has_at_symbol": lexical.has_at_symbol,
        "lexical_risk_score": lexical.risk_score_contribution,
        "content_category": content_data.content_category,
        "content_subcategory": content_data.content_subcategory,
        "dynamic_content_detected": content_data.dynamic_content_detected,
        "is_insecure_login_form": content_data.form.is_insecure_login_form,
        "form_action_is_external": content_data.form.form_action_is_external,
        "brand_impersonation_signals": content_data.brand_impersonation_signals,
        "content_risk_score": content_data.risk_score_contribution,
        "content_warning_flags": content_data.warning_flags,
        "ml_phishing_probability": ml_result["phishing_probability"],
        "ml_risk_bucket": ml_result["phishing_risk_bucket"],
    }

    risk_assessment = calculate_risk_score(combined_scan_data)

    details = {
        "ssl_security": ssl_data,
        "ip_intelligence": {
            "ip_address": ip_intel.get("ip_address", "Unknown"),
            "hosting_country": f"{ip_intel.get('hosting_country', 'Unknown')} {ip_intel.get('hosting_flag', '') or ''}".strip(),
            "isp": ip_intel.get("isp", "Unknown"),
            "asn_org": ip_intel.get("asn_org", "Unknown"),
            "is_vpn_or_proxy": "Yes" if ip_intel.get("is_vpn_or_proxy") else "No",
            "registrant_country": f"{ip_intel.get('registrant_country', 'Unknown')} {ip_intel.get('registrant_flag', '') or ''}".strip(),
            "country_mismatch": "Yes" if ip_intel.get("country_mismatch") else "No",
        },
        "phishing_checks": {
            "typosquatting": "Yes" if is_typosquat else "No",
            "brand_similarity": (
                brand_detected.title() if brand_detected != "None" else "None"
            ),
            "suspicious_keywords": "Yes" if suspicious_kw else "No",
            "homograph_attack": "Yes" if is_homograph else "No",
            "ml_phishing_probability": ml_result["phishing_probability"],
            "ml_risk_bucket": ml_result["phishing_risk_bucket"],
        },
        "domain_reputation": {
            "domain_age": dom_age_display,
            "domain_status": dom_status,
            "suspicious_tld": "Yes" if is_sus_tld else "No",
            "registrar_trust": "Normal",
            "whois_privacy": "Yes" if whois_privacy else "No",
        },
        "link_structure": {
            "platform": fingerprint.get("platform", "Unknown").title(),
            "service_type": service_type,
            "link_category": link_cat,
            "short_provider": short_provider,
            "original_domain": start_domain,
            "is_ip_based": "Yes" if fingerprint.get("is_ip_based") else "No",
            "obfuscation": "Yes" if is_obfuscated else "No",
        },
        "redirect_analysis": {
            "hop_count": hops,
            "cross_domain": "Yes" if cross_domain else "No",
            "final_destination": trace.get("final_url", normalized_url),
            "redirect_loop": "No",
        },
        "content_analysis": {
            "category": content_data.content_category,
            "subcategory": content_data.content_subcategory or "None",
            "page_title": content_data.page_title or "Unknown",
            "insecure_login_form": (
                "Yes" if content_data.form.is_insecure_login_form else "No"
            ),
            "external_form_action": (
                "Yes" if content_data.form.form_action_is_external else "No"
            ),
            "dynamic_content": "Yes" if content_data.dynamic_content_detected else "No",
            "brand_impersonation": content_data.brand_impersonation_signals or [],
            "warning_flags": content_data.warning_flags,
        },
    }

    ai_payload = {
        "url": target_url,
        "risk_score": risk_assessment["final_score"],
        "risk_level": risk_assessment["risk_level"],
        "details": details,
        "risk_factors": risk_assessment.get("risk_factors", []),
    }
    ai_summary = await asyncio.to_thread(generate_security_explanation, ai_payload)
    details["ai_summary"] = ai_summary

    scan_time = datetime.utcnow()
    has_ssl_issue = (
        not ssl_data.get("is_valid", True) or len(ssl_data.get("warning_flags", [])) > 0
    )

    new_scan = ScanHistory(
        url=normalized_url,
        risk_score=risk_assessment["final_score"],
        risk_level=risk_assessment["risk_level"],
        has_ssl_issue=has_ssl_issue,
        details=details,
        reasoning=risk_assessment["risk_factors"],
        scan_time=scan_time,
        user_email=user.email,
        is_guest=False,
    )

    db.add(new_scan)
    await db.commit()
    await db.refresh(new_scan)

    final_json_response = {
        "id": str(new_scan.id),
        "url": normalized_url,
        "risk_score": risk_assessment["final_score"],
        "risk_level": risk_assessment["risk_level"],
        "details": details,
        "ai_summary": ai_summary,
        "category_breakdown": risk_assessment["category_breakdown"],
        "risk_factors": risk_assessment["risk_factors"],
        "ssl_details": ssl_data,
        "scan_time": scan_time.isoformat(),
        "user_email": user.email,
        "is_guest": False,
    }
    ScanCache.set_url_cache(target_url_raw, final_json_response)

    return final_json_response


async def deep_scan(request: ScanRequest, user: User = Depends(get_current_user)):
    return {
        "status": "Deep Scan Initiated",
        "user": user.email,
        "message": "Dynamic sandbox analysis started (Phase 2 feature)",
    }


@router.get("/history")
async def get_scan_history(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    try:
        query = (
            select(ScanHistory)
            .where(ScanHistory.user_email == user.email)
            .order_by(desc(ScanHistory.scan_time))
            .limit(20)
        )

        result = await db.execute(query)
        history = result.scalars().all()

        cleaned_history = []
        for item in history:
            cleaned_history.append(
                {
                    "id": str(item.id),
                    "url": item.url,
                    "risk_score": item.risk_score,
                    "risk_level": item.risk_level,
                    "has_ssl_issue": item.has_ssl_issue,
                    "details": item.details,
                    "reasoning": item.reasoning,
                    "scan_time": item.scan_time.isoformat(),
                    "user_email": item.user_email,
                }
            )

        return cleaned_history
    except Exception as e:
        print(f"History Error: {e}")
        raise HTTPException(status_code=500, detail="Could not fetch history")


async def background_fetch_ct(hostname: str):
    """
    Fired by FastAPI BackgroundTasks to fetch heavy crt.sh logs asynchronously.
    Does not block the user's API response.
    """
    try:
        print(f"[BACKGROUND] Starting heavy CT log fetch for {hostname}...")
        # Push to thread so the background worker doesn't freeze the event loop
        ct_data = await asyncio.to_thread(fetch_ct_logs, hostname)

        if ct_data and ct_data.get("status") != "failed":
            ScanCache.set_ct_cache(hostname, ct_data)
            print(f"[BACKGROUND OK] Successfully cached massive CT logs for {hostname}")
        else:
            print(f"[BACKGROUND FAIL] crt.sh returned no data or failed for {hostname}")

    except Exception as e:
        print(f"[BACKGROUND ERROR] Failed to fetch CT logs for {hostname}: {e}")


@router.get("/admin/users")
async def get_all_users(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    # REAL WORLD WAY: Check the database role, not a hardcoded email
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(select(User))
    users = result.scalars().all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "name": u.full_name,
            "picture": u.profile_pic,
            "is_admin": u.is_admin,
        }
        for u in users
    ]
