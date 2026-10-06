import whois
import tldextract
import asyncio
from datetime import datetime
from app.utils.timer import ExecutionTimer

SUSPICIOUS_TLDS = {".xyz", ".top", ".tk", ".gq", ".zip", ".bid", ".casa"}


def _perform_whois_lookup(domain: str):
    try:
        return whois.whois(domain)
    except Exception as e:
        return None


async def check_domain_reputation(url: str):
    with ExecutionTimer("WHOIS / Reputation Module"):
        report = {
            "domain_age_days": None,
            "registrar": None,
            "is_suspicious_tld": False,
            "warning_flags": [],
        }

        try:
            extracted = tldextract.extract(url)
            domain = f"{extracted.domain}.{extracted.suffix}"
            tld = f".{extracted.suffix}"

            if tld in SUSPICIOUS_TLDS:
                report["is_suspicious_tld"] = True
                report["warning_flags"].append(f"Suspicious TLD detected ({tld})")

            try:
                # This will strictly enforce a 5-second max waiting time!
                w = await asyncio.wait_for(
                    asyncio.to_thread(_perform_whois_lookup, domain), timeout=5.0
                )
            except asyncio.TimeoutError:
                report["warning_flags"].append("WHOIS Lookup Timed Out")
                return report

            if not w:
                report["warning_flags"].append("WHOIS Lookup Failed or Empty")
                return report

            creation_date = w.creation_date
            if isinstance(creation_date, list):
                creation_date = creation_date[0]

            if creation_date:
                if creation_date.tzinfo is not None:
                    creation_date = creation_date.replace(tzinfo=None)
                now = datetime.utcnow()
                age_days = (now - creation_date).days
                report["domain_age_days"] = age_days
                report["registrar"] = w.registrar

                if age_days < 7:
                    report["warning_flags"].append(
                        "Critical Risk: New Domain (< 1 week)"
                    )
                elif age_days < 30:
                    report["warning_flags"].append(
                        "High Risk: Fresh Domain (< 1 month)"
                    )
            else:
                report["warning_flags"].append("Indeterminate: Creation date redacted")

        except Exception as e:
            report["warning_flags"].append(f"Reputation Check Error: {str(e)}")

        return report
