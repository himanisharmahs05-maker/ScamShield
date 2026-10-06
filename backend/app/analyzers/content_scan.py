from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse
from app.utils.timer import ExecutionTimer
from bs4 import BeautifulSoup, Tag

_SCRIPT_HEAVY_THRESHOLD: int = 5
_IFRAME_SUSPICIOUS_THRESHOLD: int = 3
_HIDDEN_INPUT_SUSPICIOUS_THRESHOLD: int = 5

_FINANCIAL_KEYWORDS: frozenset[str] = frozenset(
    {
        "bank",
        "banking",
        "payment",
        "wallet",
        "crypto",
        "bitcoin",
        "ethereum",
        "transfer",
        "wire",
        "iban",
        "routing",
        "account number",
        "credit card",
        "debit card",
        "cvv",
        "paypal",
        "stripe",
        "invoice",
    }
)
_LOGIN_KEYWORDS: frozenset[str] = frozenset(
    {
        "login",
        "log in",
        "sign in",
        "signin",
        "authenticate",
        "password",
        "username",
        "credentials",
        "forgot password",
        "reset password",
    }
)
_ECOMMERCE_KEYWORDS: frozenset[str] = frozenset(
    {
        "add to cart",
        "buy now",
        "checkout",
        "shopping cart",
        "order",
        "shop",
        "product",
        "price",
        "discount",
        "sale",
        "shipping",
    }
)
_SCAM_KEYWORDS: frozenset[str] = frozenset(
    {
        "you have won",
        "congratulations",
        "claim your prize",
        "free gift",
        "limited time offer",
        "act now",
        "winner",
        "lottery",
        "selected",
        "verify your account immediately",
        "your account has been suspended",
        "urgent action required",
    }
)
_TECH_SUPPORT_KEYWORDS: frozenset[str] = frozenset(
    {
        "call microsoft",
        "call apple",
        "tech support",
        "your computer is infected",
        "virus detected",
        "call now",
        "toll free",
        "1-800",
    }
)
_ADULT_KEYWORDS: frozenset[str] = frozenset(
    {
        "adult",
        "18+",
        "xxx",
        "porn",
        "nude",
        "explicit",
        "onlyfans",
    }
)
_GAMBLING_KEYWORDS: frozenset[str] = frozenset(
    {
        "casino",
        "poker",
        "slots",
        "betting",
        "wager",
        "odds",
        "sportsbook",
        "blackjack",
        "roulette",
    }
)
_DOWNLOAD_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".exe",
        ".msi",
        ".bat",
        ".ps1",
        ".sh",
        ".apk",
        ".ipa",
        ".dmg",
        ".iso",
        ".img",
        ".zip",
        ".rar",
        ".7z",
        ".tar",
        ".gz",
        ".docm",
        ".xlsm",
    }
)


@dataclass(slots=True)
class FormReport:
    has_password_input: bool = False
    form_action: Optional[str] = None
    form_action_is_http: bool = False
    form_action_is_external: bool = False
    hidden_input_count: int = 0
    is_insecure_login_form: bool = False


@dataclass(slots=True)
class ContentReport:
    content_category: str = "Unknown"
    content_subcategory: Optional[str] = None
    page_title: Optional[str] = None
    dynamic_content_detected: bool = False
    script_count: int = 0
    iframe_count: int = 0
    external_resource_count: int = 0
    form: FormReport = field(default_factory=FormReport)
    brand_impersonation_signals: list[str] = field(default_factory=list)
    warning_flags: list[str] = field(default_factory=list)
    risk_score_contribution: int = 0


def _extract_visible_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "meta", "head"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True).lower()


def _classify_content(
    text: str, soup: BeautifulSoup, parsed_url
) -> tuple[str, Optional[str]]:
    has_password = bool(soup.find("input", {"type": "password"}))

    if any(k in text for k in _SCAM_KEYWORDS):
        return "Scam / Fraud Page", None

    if any(k in text for k in _TECH_SUPPORT_KEYWORDS):
        return "Tech Support Scam", None

    if any(k in text for k in _ADULT_KEYWORDS):
        return "Adult Content", None

    if any(k in text for k in _GAMBLING_KEYWORDS):
        return "Gambling / Betting", None

    if has_password and any(k in text for k in _FINANCIAL_KEYWORDS):
        return "Login / Authentication Page", "Financial Service"

    if has_password and any(k in text for k in _LOGIN_KEYWORDS):
        return "Login / Authentication Page", None

    if any(k in text for k in _FINANCIAL_KEYWORDS):
        return "Financial Service", None

    if any(k in text for k in _ECOMMERCE_KEYWORDS):
        return "E-commerce / Shopping", None

    path = parsed_url.path.lower()
    if any(path.endswith(ext) for ext in _DOWNLOAD_EXTENSIONS):
        return "Direct Download", None

    if not text.strip():
        return "Parked Domain / No Content", None

    return "Standard Website", None


def _inspect_forms(soup: BeautifulSoup, base_url: str, parsed_url) -> FormReport:
    report = FormReport()
    password_input = soup.find("input", {"type": "password"})

    if not password_input:
        return report

    report.has_password_input = True
    parent_form = password_input.find_parent("form")

    if not isinstance(parent_form, Tag):
        return report

    action: str = parent_form.get("action", "") or ""
    report.form_action = action or None
    report.hidden_input_count = len(parent_form.find_all("input", {"type": "hidden"}))

    if action:
        if action.startswith("http://"):
            report.form_action_is_http = True
        try:
            action_host = urlparse(action).netloc
            base_host = parsed_url.netloc
            if action_host and action_host != base_host:
                report.form_action_is_external = True
        except Exception:
            pass

    base_is_http = base_url.startswith("http://")
    if base_is_http or report.form_action_is_http or report.form_action_is_external:
        report.is_insecure_login_form = True

    return report


def _detect_brand_impersonation(
    text: str,
    soup: BeautifulSoup,
    hostname: str,
) -> list[str]:
    from .data.brands import BRAND_TARGETS

    signals: list[str] = []
    title_tag = soup.find("title")
    title_text = title_tag.get_text().lower() if title_tag else ""
    og_site = soup.find("meta", property="og:site_name")
    og_site_name = og_site.get("content", "").lower() if og_site else ""

    for brand in BRAND_TARGETS:
        brand_in_content = brand in text or brand in title_text or brand in og_site_name
        brand_not_in_domain = brand not in hostname.lower()
        if brand_in_content and brand_not_in_domain:
            signals.append(f"References '{brand}' but domain does not match")

    return signals


def _count_external_resources(soup: BeautifulSoup, base_host: str) -> int:
    count = 0
    for tag in soup.find_all(["script", "link", "img", "iframe"]):
        src = tag.get("src") or tag.get("href") or ""
        if src.startswith("http"):
            try:
                if urlparse(src).netloc != base_host:
                    count += 1
            except Exception:
                pass
    return count


def _score_contribution(report: ContentReport) -> int:
    score = 0
    if report.form.is_insecure_login_form:
        score += 100
    if report.form.form_action_is_external:
        score += 40
    if report.brand_impersonation_signals:
        score += len(report.brand_impersonation_signals) * 20
    if report.form.hidden_input_count > _HIDDEN_INPUT_SUSPICIOUS_THRESHOLD:
        score += 15
    if report.iframe_count > _IFRAME_SUSPICIOUS_THRESHOLD:
        score += 15
    if report.content_category in (
        "Scam / Fraud Page",
        "Tech Support Scam",
        "Malware Distribution",
    ):
        score += 50
    return min(score, 100)


def inspect_content(
    html_content: str, base_url: str, hostname: str = ""
) -> ContentReport:
    with ExecutionTimer("HTML Content Parsing"):
        report = ContentReport()

        if not html_content or not html_content.strip():
            report.warning_flags.append(
                "Empty Response Body — possible bot detection or parked domain"
            )
            return report

        try:
            soup = BeautifulSoup(html_content, "html.parser")
        except Exception as exc:
            report.warning_flags.append(f"HTML Parse Failure: {exc}")
            return report

        parsed_url = urlparse(base_url)
        base_host = parsed_url.netloc

        title_tag = soup.find("title")
        report.page_title = title_tag.get_text(strip=True) if title_tag else None

        report.script_count = len(soup.find_all("script"))
        report.iframe_count = len(soup.find_all("iframe"))
        report.external_resource_count = _count_external_resources(soup, base_host)

        if report.script_count > _SCRIPT_HEAVY_THRESHOLD:
            report.dynamic_content_detected = True
            report.warning_flags.append(
                f"Heavy Dynamic Content ({report.script_count} scripts) — analysis limited to static layer"
            )

        if report.iframe_count > _IFRAME_SUSPICIOUS_THRESHOLD:
            report.warning_flags.append(
                f"Suspicious Iframe Count ({report.iframe_count}) — possible clickjacking or content injection"
            )

        visible_text = _extract_visible_text(soup)
        report.content_category, report.content_subcategory = _classify_content(
            visible_text, soup, parsed_url
        )

        report.form = _inspect_forms(soup, base_url, parsed_url)

        if report.form.is_insecure_login_form:
            report.warning_flags.append(
                "Insecure Login Form — credentials submitted over HTTP or to an external domain"
            )

        if report.form.form_action_is_external:
            report.warning_flags.append(
                f"Form Submits to External Domain: {report.form.form_action}"
            )

        if hostname:
            report.brand_impersonation_signals = _detect_brand_impersonation(
                visible_text, soup, hostname
            )
            for signal in report.brand_impersonation_signals:
                report.warning_flags.append(f"Brand Impersonation Signal: {signal}")

        report.risk_score_contribution = _score_contribution(report)

        return report
