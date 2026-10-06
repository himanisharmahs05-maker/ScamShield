import socket
import asyncio
import requests
import tldextract
from datetime import datetime

from app.utils.timer import ExecutionTimer

MAJOR_HOSTING_ASNS = {
    "AS16509": "Amazon Web Services",
    "AS14618": "Amazon Web Services",
    "AS15169": "Google Cloud",
    "AS396982": "Google Cloud",
    "AS8075": "Microsoft Azure",
    "AS13335": "Cloudflare",
    "AS209242": "Cloudflare",
    "AS20940": "Akamai",
    "AS16625": "Akamai",
    "AS54113": "Fastly",
    "AS2635": "Automattic (WordPress)",
    "AS19527": "Google (Corp)",
    "AS32934": "Meta / Facebook",
    "AS714": "Apple",
    "AS46489": "Twitch / Amazon",
    "AS24940": "Hetzner",
    "AS51167": "Contabo",
    "AS9009": "M247 (common bulletproof host)",  # flag this one
    "AS60068": "CDN77",
    "AS200651": "DDoS-Guard",  # flag this one
}

# ASNs commonly associated with bulletproof hosting / abuse
SUSPICIOUS_ASNS = {
    "AS9009",  # M247 — heavily abused for phishing
    "AS200651",  # DDoS-Guard — used to shield illegal sites
    "AS60068",  # CDN77 — frequently abused
    "AS57523",  # Chang Way Technologies
    "AS206312",  # Maxko
    "AS47583",  # Hostinger (high abuse ratio)
}

# Country codes considered higher risk for phishing infrastructure
# Not a judgment on the country — purely statistical abuse rates
HIGH_RISK_HOSTING_COUNTRIES = {"RU", "CN", "KP", "IR", "NG", "UA", "BY"}


# ─────────────────────────────────────────────
#  RDAP LOOKUP — registrant country + registrar
#  Modern replacement for WHOIS, works on new
#  gTLDs (.aws, .io, .app, .dev) where WHOIS fails
# ─────────────────────────────────────────────


def _fetch_rdap_bootstrap():
    """Fetch IANA RDAP bootstrap to find the right server for a TLD."""
    try:
        resp = requests.get("https://data.iana.org/rdap/dns.json", timeout=5)
        return resp.json()
    except Exception:
        return None


def _get_rdap_url(tld: str, bootstrap: dict) -> str | None:
    """Find the RDAP base URL for a given TLD from IANA bootstrap data."""
    if not bootstrap:
        return None
    for service in bootstrap.get("services", []):
        if tld in service[0]:
            return service[1][0]
    return None


def _parse_rdap_registrar(entities: list) -> str | None:
    """Extract registrar name from RDAP entity list."""
    for entity in entities:
        if "registrar" in entity.get("roles", []):
            vcard = entity.get("vcardArray", [[], []])[1]
            for field in vcard:
                if field[0] == "fn":
                    return field[3]
    return None


def _parse_rdap_registrant_country(entities: list) -> str | None:
    """Extract registrant country code from RDAP entity list."""
    for entity in entities:
        if "registrant" in entity.get("roles", []):
            vcard = entity.get("vcardArray", [[], []])[1]
            for field in vcard:
                if field[0] == "adr":
                    country = field[1].get("country")
                    if country:
                        return country
    return None


def _lookup_rdap(domain: str) -> dict:
    """
    Full RDAP lookup for a domain.
    Returns registrar, registrant_country, registration_date.
    Falls back gracefully — never raises.
    """
    result = {
        "registrar": None,
        "registrant_country": None,
        "registration_date": None,
    }
    try:
        extracted = tldextract.extract(domain)
        tld = extracted.suffix  # e.g. "aws", "com", "co.uk"

        bootstrap = _fetch_rdap_bootstrap()
        rdap_url = _get_rdap_url(tld, bootstrap)
        if not rdap_url:
            return result

        # Query RDAP for the domain
        resp = requests.get(
            f"{rdap_url}domain/{extracted.domain}.{extracted.suffix}", timeout=5
        ).json()

        # Registrar + registrant country
        entities = resp.get("entities", [])
        result["registrar"] = _parse_rdap_registrar(entities)
        result["registrant_country"] = _parse_rdap_registrant_country(entities)

        # Registration date from events
        for event in resp.get("events", []):
            if event.get("eventAction") == "registration":
                date_str = event.get("eventDate", "")
                try:
                    result["registration_date"] = datetime.fromisoformat(
                        date_str[:19]
                    ).strftime("%Y-%m-%d")
                except ValueError:
                    pass
                break

    except Exception:
        pass  # Non-fatal — partial data is fine

    return result


# ─────────────────────────────────────────────
#  IP GEOLOCATION — hosting country, ISP, ASN
#  Uses ip-api.com (free, no key, 45 req/min)
# ─────────────────────────────────────────────


def _resolve_ip(hostname: str) -> str | None:
    """DNS resolve hostname → IP address."""
    try:
        return socket.gethostbyname(hostname)
    except Exception:
        return None


def _lookup_ip_geo(ip: str) -> dict:
    """
    Query ip-api.com for geolocation, ISP, ASN, proxy/VPN flag.
    Returns raw dict or empty dict on failure.
    """
    try:
        fields = (
            "status,country,countryCode,regionName," "city,isp,org,as,proxy,hosting"
        )
        resp = requests.get(
            f"http://ip-api.com/json/{ip}?fields={fields}", timeout=5
        ).json()
        if resp.get("status") == "success":
            return resp
    except Exception:
        pass
    return {}


#  COUNTRY CODE → FLAG EMOJI


def country_flag(country_code: str) -> str:
    """Convert ISO 3166-1 alpha-2 code to flag emoji. e.g. 'US' → '🇺🇸'"""
    if not country_code or len(country_code) != 2:
        return ""
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in country_code.upper())


async def check_ip_intel(url: str) -> dict:
    with ExecutionTimer("IP Intelligence API"):
        report = {
            "ip_address": None,
            "hosting_country": None,
            "hosting_country_code": None,
            "hosting_flag": None,
            "hosting_city": None,
            "hosting_region": None,
            "isp": None,
            "asn": None,
            "asn_org": None,
            "is_major_host": False,
            "is_vpn_or_proxy": False,
            "registrant_country": None,
            "registrant_flag": None,
            "registrar": None,
            "registration_date": None,
            "country_mismatch": False,
            "warning_flags": [],
        }

        try:
            extracted = tldextract.extract(url)
            hostname = (
                f"{extracted.subdomain}.{extracted.domain}.{extracted.suffix}".lstrip(
                    "."
                )
            )
            base_domain = f"{extracted.domain}.{extracted.suffix}"
        except Exception:
            report["warning_flags"].append("IP Intel: Could not parse URL")
            return report

        try:
            ip, rdap_data = await asyncio.gather(
                asyncio.to_thread(_resolve_ip, hostname),
                asyncio.to_thread(_lookup_rdap, base_domain),
            )
        except Exception:
            ip, rdap_data = None, {}

        if ip:
            report["ip_address"] = ip
            geo = await asyncio.to_thread(_lookup_ip_geo, ip)

            if geo:
                cc = geo.get("countryCode")
                report["hosting_country"] = geo.get("country")
                report["hosting_country_code"] = cc
                report["hosting_flag"] = country_flag(cc) if cc else None
                report["hosting_city"] = geo.get("city")
                report["hosting_region"] = geo.get("regionName")
                report["isp"] = geo.get("isp")
                report["is_vpn_or_proxy"] = geo.get("proxy", False)

                asn_raw = geo.get("as", "")
                if asn_raw:
                    parts = asn_raw.split(" ", 1)
                    report["asn"] = parts[0]
                    report["asn_org"] = MAJOR_HOSTING_ASNS.get(
                        parts[0], parts[1] if len(parts) > 1 else None
                    )
                    report["is_major_host"] = parts[0] in MAJOR_HOSTING_ASNS

                if report["is_vpn_or_proxy"]:
                    report["warning_flags"].append(
                        "IP flagged as VPN / Proxy / Tor Exit Node"
                    )

                if cc in HIGH_RISK_HOSTING_COUNTRIES:
                    report["warning_flags"].append(
                        f"Hosted in High-Risk Country: {report['hosting_country']} ({cc})"
                    )

                asn = report["asn"]
                if asn in SUSPICIOUS_ASNS:
                    report["warning_flags"].append(
                        f"Suspicious Hosting ASN: {asn} ({report['asn_org']})"
                    )
        else:
            report["warning_flags"].append("IP Intel: Could not resolve hostname to IP")

        if rdap_data:
            reg_cc = rdap_data.get("registrant_country")
            report["registrant_country"] = reg_cc
            report["registrant_flag"] = country_flag(reg_cc) if reg_cc else None
            report["registrar"] = rdap_data.get("registrar")
            report["registration_date"] = rdap_data.get("registration_date")

        hcc = report["hosting_country_code"]
        rcc = report["registrant_country"]
        if hcc and rcc and hcc != rcc:
            report["country_mismatch"] = True
            report["warning_flags"].append(
                f"Country Mismatch: Registered in {rcc} {country_flag(rcc)} but hosted in {hcc} {country_flag(hcc)}"
            )

        return report
