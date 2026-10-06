import ssl
import socket
import certifi
import requests
import tldextract
from datetime import datetime
from app.utils.timer import ExecutionTimer
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import rsa, ec, dsa
from app.utils.cache_manager import ScanCache

TRUSTED_CERTIFICATE_AUTHORITIES = [
    "R3", "R12", "R13", "R14", "Let's Encrypt", "ZeroSSL", "Buypass", "E7", "E6", "E5",
    "ISRG Root X1", "ISRG Root X2", "DST Root CA X3", "cPanel", "Cloudflare",
    "Cloudflare Inc ECC CA", "Cloudflare Inc RSA CA", "Google Trust Services", "GTS",
    "GTS CA 1C3", "GTS CA 1D4", "WR2", "WR3", "WE1", "Google Trust Services LLC",
    "Amazon", "Amazon Root CA 1", "Amazon Root CA 2", "Amazon Root CA 3",
    "Amazon Root CA 4", "Microsoft Azure TLS Issuing CA", "Microsoft RSA TLS CA",
    "DigiCert", "DigiCert Inc", "DigiCert SHA2", "DigiCert TLS RSA SHA256",
    "DigiCert Global Root", "Sectigo", "Sectigo Limited", "TrustAsia",
    "TrustAsia Technologies", "GlobalSign", "GlobalSign nv-sa",
    "GlobalSign Organization Validation CA", "Entrust", "Entrust Datacard",
    "IdenTrust", "Comodo", "Comodo CA", "COMODO RSA", "USERTrust", "GeoTrust",
    "RapidSSL", "Thawte", "SSL.com", "Certum", "SwissSign", "QuoVadis",
    "T-TeleSec GlobalRoot", "D-TRUST", "Actalis", "Trustwave", "Network Solutions",
]

FREE_DV_PROVIDERS = [
    "R3", "Let's Encrypt", "cPanel", "ZeroSSL", "TrustAsia", "Cloudflare",
    "Google Trust Services", "GTS", "Amazon", "Buypass", "Sectigo",
]

WEAK_CIPHERS = ["RC4", "3DES", "NULL", "EXPORT", "anon", "DES", "RC2", "IDEA"]


def is_trusted_ca(issuer_cn: str) -> bool:
    issuer_lower = issuer_cn.lower()
    return any(ca.lower() in issuer_lower for ca in TRUSTED_CERTIFICATE_AUTHORITIES)


def is_free_dv_provider(issuer_cn: str) -> bool:
    issuer_lower = issuer_cn.lower()
    return any(provider.lower() in issuer_lower for provider in FREE_DV_PROVIDERS)


def check_hsts(hostname: str) -> dict:
    result = {
        "hsts_enabled": False,
        "hsts_max_age": 0,
        "hsts_includes_subdomains": False,
        "hsts_preload": False,
    }
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.head(
            f"https://{hostname}",
            timeout=4,
            allow_redirects=True,
            verify=certifi.where(),
            headers=headers,
        )
        hsts_header = resp.headers.get("Strict-Transport-Security", "")
        if hsts_header:
            result["hsts_enabled"] = True
            for directive in hsts_header.lower().split(";"):
                directive = directive.strip()
                if directive.startswith("max-age="):
                    try:
                        result["hsts_max_age"] = int(directive.split("=")[1])
                    except ValueError:
                        pass
                elif directive == "includesubdomains":
                    result["hsts_includes_subdomains"] = True
                elif directive == "preload":
                    result["hsts_preload"] = True
    except Exception:
        pass
    return result


def fetch_ct_logs(hostname: str) -> dict:
    with ExecutionTimer("CT Log Lookup"):
        extracted = tldextract.extract(hostname)
        base_domain = f"{extracted.domain}.{extracted.suffix}"

        cached = ScanCache.get_ct_cache(base_domain)
        if cached:
            print(f"[CACHE] CT CACHE HIT - Skipping crt.sh for {base_domain}")
            return cached

        result = {
            "ct_log_count": 0,
            "ct_earliest_seen": None,
            "ct_check_failed": False,
        }
        try:
            resp = requests.get(
                f"https://crt.sh/?q=%.{base_domain}&output=json",
                timeout=15,
            )
            if resp.status_code == 200:
                entries = resp.json()
                result["ct_log_count"] = len(entries)
                if entries:
                    dates = []
                    for e in entries:
                        date_str = e.get("not_before") or e.get("entry_timestamp")
                        if date_str:
                            try:
                                dates.append(datetime.fromisoformat(date_str[:19]))
                            except ValueError:
                                pass
                    if dates:
                        result["ct_earliest_seen"] = min(dates).strftime("%Y-%m-%d")
        except Exception:
            result["ct_check_failed"] = True

        if not result["ct_check_failed"]:
            ScanCache.set_ct_cache(base_domain, result)

        return result

def analyze_public_key(cert_obj) -> dict:
    result = {
        "key_type": "Unknown",
        "key_bits": 0,
        "key_is_weak": False,
    }
    try:
        pub_key = cert_obj.public_key()
        if isinstance(pub_key, rsa.RSAPublicKey):
            result["key_type"] = "RSA"
            result["key_bits"] = pub_key.key_size
            result["key_is_weak"] = pub_key.key_size < 2048
        elif isinstance(pub_key, ec.EllipticCurvePublicKey):
            result["key_type"] = "EC"
            result["key_bits"] = pub_key.key_size
            result["key_is_weak"] = pub_key.key_size < 256
        elif isinstance(pub_key, dsa.DSAPublicKey):
            result["key_type"] = "DSA"
            result["key_bits"] = pub_key.key_size
            result["key_is_weak"] = pub_key.key_size < 2048
    except Exception:
        pass
    return result


def analyze_san_pattern(sans: list) -> list:
    warnings = []
    dns_names = [v for t, v in sans if t == "DNS"]
    if not dns_names:
        return warnings
    base_domains = set(".".join(d.lstrip("*.").split(".")[-2:]) for d in dns_names)
    if len(base_domains) > 3:
        warnings.append(f"SANs span {len(base_domains)} unrelated base domains (phishing kit signal)")
    return warnings


def inspect_ssl(hostname: str):
    with ExecutionTimer("SSL Inspection Module"):
        report = {
            "is_valid": False,
            "is_https": False,
            "issuer": "Unknown",
            "resolved_ip": None,
            "cert_age_days": 0,
            "days_to_expire": 0,
            "cert_total_lifespan_days": 0,
            "tls_version": "Unknown",
            "cipher_suite": "Unknown",
            "cipher_bits": 0,
            "validation_type": "Unknown",
            "is_self_signed": False,
            "is_wildcard": False,
            "san_count": 0,
            "key_type": "Unknown",
            "key_bits": 0,
            "is_free_dv": False,
            "cert_is_new": False,
            "hsts_enabled": False,
            "hsts_max_age": 0,
            "hsts_includes_subdomains": False,
            "hsts_preload": False,
            "ct_log_count": 0,
            "ct_earliest_seen": None,
            "ct_check_failed": False,
            "org_name": None,
            "org_country": None,
            "org_locality": None,
            "warning_flags": [],
        }

        context = ssl.create_default_context(cafile=certifi.where())

        try:
            with socket.create_connection((hostname, 443), timeout=5) as sock:
                sock.settimeout(5)
                report["resolved_ip"] = sock.getpeername()[0]
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    der_cert = ssock.getpeercert(binary_form=True)

                    report["is_https"] = True
                    report["is_valid"] = True

                    report["tls_version"] = ssock.version()
                    if report["tls_version"] in ["TLSv1", "TLSv1.1"]:
                        report["warning_flags"].append(f"Deprecated/Weak TLS Version ({report['tls_version']})")

                    cipher = ssock.cipher()
                    if cipher:
                        report["cipher_suite"] = cipher[0]
                        report["cipher_bits"] = cipher[2] or 0
                        if any(w in cipher[0] for w in WEAK_CIPHERS):
                            report["warning_flags"].append(f"Weak Cipher Suite: {cipher[0]}")

                    issuer_info = {k: v for item in cert.get("issuer", []) for k, v in item}
                    subject_info = {k: v for item in cert.get("subject", []) for k, v in item}

                    common_name = issuer_info.get("commonName", "Unknown")
                    subject_cn = subject_info.get("commonName", "Unknown")
                    report["issuer"] = common_name

                    report["org_name"] = subject_info.get("organizationName")
                    report["org_country"] = subject_info.get("countryName")
                    report["org_locality"] = subject_info.get("localityName")

                    if common_name == subject_cn and common_name != "Unknown":
                        report["is_self_signed"] = True
                        report["warning_flags"].append("Self-Signed Certificate (High Risk)")

                    if not report["is_self_signed"] and not is_trusted_ca(common_name):
                        report["warning_flags"].append(f"Unknown/Untrusted CA: {common_name}")

                    report["is_free_dv"] = is_free_dv_provider(common_name)

                    if subject_cn.startswith("*."):
                        report["is_wildcard"] = True
                        report["warning_flags"].append("Wildcard Certificate")

                    not_before_str = cert.get("notBefore")
                    not_after_str = cert.get("notAfter")

                    if not_before_str and not_after_str:
                        not_before = datetime.strptime(not_before_str, "%b %d %H:%M:%S %Y %Z")
                        not_after = datetime.strptime(not_after_str, "%b %d %H:%M:%S %Y %Z")
                        now = datetime.utcnow()

                        age = (now - not_before).days
                        days_to_expire = (not_after - now).days
                        total_lifespan = (not_after - not_before).days

                        report["cert_age_days"] = age
                        report["days_to_expire"] = days_to_expire
                        report["cert_total_lifespan_days"] = total_lifespan
                        report["cert_is_new"] = age < 30

                        if age < 2:
                            report["warning_flags"].append("Very New Certificate (< 48h)")

                        if report["is_free_dv"] and age < 2 and not report["org_name"]:
                            report["warning_flags"].append("New Free DV Cert on Unverified Domain (Suspicious)")

                        if days_to_expire < 0:
                            report["warning_flags"].append("Certificate Expired")
                            report["is_valid"] = False
                        elif days_to_expire < 7:
                            report["warning_flags"].append("Certificate Expires Soon (< 7 days)")

                        if total_lifespan < 10:
                            report["warning_flags"].append(f"Abnormally Short Cert Lifespan ({total_lifespan} days)")
                        elif total_lifespan > 825:
                            report["warning_flags"].append(f"Cert Lifespan Exceeds CAB Forum Max ({total_lifespan} days)")

                    if report["org_name"]:
                        report["validation_type"] = "OV/EV (High Trust)"
                    else:
                        report["validation_type"] = "DV (Standard)"

                    sans = cert.get("subjectAltName", [])
                    report["san_count"] = len(sans)

                    if len(sans) > 10:
                        report["warning_flags"].append(f"High number of SANs ({len(sans)})")

                    san_warnings = analyze_san_pattern(sans)
                    report["warning_flags"].extend(san_warnings)

                    try:
                        cert_obj = x509.load_der_x509_certificate(der_cert)
                        key_info = analyze_public_key(cert_obj)
                        report["key_type"] = key_info["key_type"]
                        report["key_bits"] = key_info["key_bits"]
                        if key_info["key_is_weak"]:
                            report["warning_flags"].append(f"Weak Public Key: {key_info['key_type']} {key_info['key_bits']}-bit")
                    except Exception:
                        pass

        except ssl.SSLError as e:
            report["warning_flags"].append(f"SSL Verification Error: {str(e)}")
        except socket.timeout:
            report["warning_flags"].append("SSL Handshake Timed Out")
        except Exception as e:
            report["warning_flags"].append(f"SSL Check Failed: {str(e)}")

        if report["is_https"]:
            hsts = check_hsts(hostname)
            report.update(hsts)

            if not hsts["hsts_enabled"]:
                report["warning_flags"].append("HSTS Not Configured")
            elif hsts["hsts_max_age"] < 31536000:
                report["warning_flags"].append(f"HSTS max-age Too Low ({hsts['hsts_max_age']}s, recommend ≥ 31536000)")

        return report


def merge_ct_results(ssl_report: dict, ct: dict) -> dict:
    ssl_report["ct_log_count"] = ct["ct_log_count"]
    ssl_report["ct_earliest_seen"] = ct["ct_earliest_seen"]
    ssl_report["ct_check_failed"] = ct["ct_check_failed"]

    if not ct["ct_check_failed"]:
        if ct["ct_log_count"] == 0:
            ssl_report["warning_flags"].append("No CT Log Entries Found (Suspicious)")
        elif ct["ct_earliest_seen"]:
            try:
                first_seen = datetime.strptime(ct["ct_earliest_seen"], "%Y-%m-%d")
                if (datetime.utcnow() - first_seen).days < 3:
                    ssl_report["warning_flags"].append(
                        f"CT Log: Certificate First Seen Very Recently ({ct['ct_earliest_seen']})"
                    )
            except ValueError:
                pass

    return ssl_report