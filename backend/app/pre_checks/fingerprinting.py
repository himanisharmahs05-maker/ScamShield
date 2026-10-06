# ABOUT THIS FILE
# pre_checks/fingerprinting.py (The Identifier): 
# This file answerS the question: "What kind of infrastructure is hosting this link?" (Shorteners, IP addresses, DDNS, Cloud Storage, App Deep Links).

import ipaddress
import tldextract
import re
import requests
from urllib.parse import urlparse

SHORTENER_DOMAINS = {"bit.ly", "t.co", "goo.gl", "is.gd", "buff.ly", "tinyurl.com", "ow.ly", "cutt.ly", "shorturl.at", "rebrand.ly"}

DDNS_DOMAINS = {
    "duckdns.org", "ngrok.io", "no-ip.com", "no-ip.org", "dyndns.org", 
    "ddns.net", "serveo.net", "localtunnel.me"
}

CLOUD_STORAGE_DOMAINS = {
    "raw.githubusercontent.com", "s3.amazonaws.com", "drive.google.com", 
    "dl.dropboxusercontent.com", "firebasestorage.googleapis.com"
}

def check_obfuscated_ip(hostname: str):
    try: return ipaddress.ip_address(hostname)
    except ValueError: pass
    try:
        if hostname.startswith('0x') or hostname.startswith('0X'): ip_int = int(hostname, 16)
        elif hostname.startswith('0') and not hostname.isdigit():
            try: ip_int = int(hostname, 8) 
            except ValueError: ip_int = int(hostname)
        else: ip_int = int(hostname)
        return ipaddress.ip_address(ip_int)
    except (ValueError, OverflowError): return None

def is_link_shortener(url: str, domain_only: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    
    if domain_only in SHORTENER_DOMAINS:
        return True
        
    ext = tldextract.extract(url)
    if len(ext.domain) <= 6 and 0 < len(path) <= 10:
        if re.match(r"^[a-zA-Z0-9_-]+$", path):
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                response = requests.head(url, headers=headers, allow_redirects=False, timeout=3)
                
                if response.status_code in [301, 302, 303, 307, 308]:
                    return True
            except requests.RequestException:
                return False
    return False

def identify_link_type(url: str, hostname: str):
    results = {
        "is_ip_based": False,
        "is_shortened": False,
        "is_app_deep_link": False,
        "tags": []
    }

    parsed_url = urlparse(url)
    ext = tldextract.extract(url)
    domain_only = f"{ext.domain}.{ext.suffix}"

    # 1. IP-Based Links
    ip_obj = check_obfuscated_ip(hostname)
    if ip_obj:
        results["is_ip_based"] = True
        results["tags"].append("IP-Based Link")

    # 2. Shortened URLs
    if is_link_shortener(url, domain_only):
        results["is_shortened"] = True
        results["tags"].append("Shortened URL")

    # 3. DDNS and Cloud Storage
    if domain_only in DDNS_DOMAINS:
        results["tags"].append("Dynamic DNS (Disposable)")
    
    if hostname.lower() in CLOUD_STORAGE_DOMAINS:
        results["tags"].append("Cloud Storage / Raw File Host")

    # 4. App Deep Links (Mobile Intents)
    scheme = parsed_url.scheme.lower()
    if scheme not in ["http", "https", "", "data", "javascript"]:
        results["is_app_deep_link"] = True
        if scheme == "intent":
            pkg_match = re.search(r'package=([^;]+)', parsed_url.fragment)
            if pkg_match:
                results["tags"].append(f"Launches App ({pkg_match.group(1)})")
            else:
                results["tags"].append("App Deep Link (Android Intent)")
        else:
            results["tags"].append(f"App Deep Link ({scheme})")

    if not results["tags"]:
        results["tags"].append("Standard Website")

    return results