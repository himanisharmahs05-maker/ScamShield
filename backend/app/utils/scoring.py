import ipaddress
import urllib.parse
from app.core.trust_manager import trust_manager

# Comprehensive list of well-known, safe public IPs 
# (Major DNS resolvers, security filters, and Anycast services)
KNOWN_SAFE_IPS = {
    # --- Cloudflare ---
    "1.1.1.1", "1.0.0.1", "1.1.1.2", "1.0.0.2", "1.1.1.3", "1.0.0.3",
    "2606:4700:4700::1111", "2606:4700:4700::1001",
    # --- Google ---
    "8.8.8.8", "8.8.4.4", "2001:4860:4860::8888", "2001:4860:4860::8844",
    # --- Quad9 ---
    "9.9.9.9", "149.112.112.112", "9.9.9.10", "149.112.112.10", 
    "9.9.9.11", "149.112.114.114", "2620:fe::fe", "2620:fe::9",
    # --- OpenDNS (Cisco) ---
    "208.67.222.222", "208.67.220.220", "208.67.222.123", "208.67.220.123",
    "2620:119:35::35", "2620:119:53::53",
    # --- AdGuard ---
    "94.140.14.14", "94.140.15.15", "94.140.14.15", "94.140.15.16",
    # --- CleanBrowsing ---
    "185.228.168.9", "185.228.169.9", "185.228.168.168", "185.228.169.168",
    # --- NextDNS & Control D ---
    "45.90.28.0", "45.90.30.0", "76.76.2.0", "76.76.10.0"
}

def evaluate_ip_risk(hostname: str) -> dict:
    """Evaluates the risk of a raw IP address being used as a hostname."""
    if not hostname:
        return {"score": 0, "msg": None}
    try:
        ip = ipaddress.ip_address(hostname)
        if str(ip) in KNOWN_SAFE_IPS:
            return {"score": 0, "msg": None}
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return {"score": 10, "msg": "Local or private network IP address used"}
        return {"score": 45, "msg": "Public IP address used instead of a domain name (Common in malware/phishing)"}
    except ValueError:
        return {"score": 0, "msg": None}

def calculate_risk_score(scan_results: dict) -> dict:
    total_score = 0
    risk_factors = []

    category_scores = {
        "lexical": 0,
        "ssl": 0,
        "reputation": 0,
        "content": 0
    }
    
    def add_risk(points: int, message: str, category: str):
        nonlocal total_score
        total_score += points
        category_scores[category] += points
        risk_factors.append(f"{message} (+{points})")
        
    # --- GLOBAL CONTEXT FOR GUARDS ---
    ip_data = scan_results.get("ip_intel", {})
    
    # --- 1. Lexical / URL Checks ---
    url = scan_results.get('url', '').lower()
    
    # ==========================================
    # 🚨 NEW: CRITICAL THREAT PENALTIES
    # ==========================================
    # Use fallback .get() in case the dictionary is flat or nested
    lexical_data = scan_results.get("lexical", scan_results)
    
    if lexical_data.get("has_dangerous_scheme"):
        add_risk(80, "Dangerous Scheme (Code Execution Risk)", "lexical")
        
    if lexical_data.get("has_embedded_credentials"):
        add_risk(60, "Embedded Credentials Detected (Spoofing Risk)", "lexical")
        
    if lexical_data.get("is_suspicious_download"):
        add_risk(50, "Direct File Download Detected (.exe, .apk, etc.)", "lexical")
    # ==========================================
    
    # 🚀 ENTERPRISE UPGRADE: Dynamically check the Top 100k memory cache
    is_major = trust_manager.is_major_domain(url)

    # 2. 🚀 NEW: Academic Trust Bypass
    # Hackers cannot easily register .edu or .ac.* domains.
    hostname = urllib.parse.urlparse(url).hostname or ""
    is_academic = hostname.endswith('.edu') or '.edu.' in hostname or '.ac.' in hostname
    
    # 3. Create a combined Master Trust variable
    is_highly_trusted = is_major or is_academic

    if is_highly_trusted and "ssl" in scan_results:
        warnings = scan_results["ssl"].get("warning_flags", [])
        scan_results["ssl"]["warning_flags"] = [
            w for w in warnings 
            if "SANs" not in w and "phishing kit signal" not in w and "CT Log" not in w
        ]
        
    # Contextual IP Evaluation
    hostname = urllib.parse.urlparse(url).hostname or ""
    ip_eval = evaluate_ip_risk(hostname)
    if ip_eval["score"] > 0:
        add_risk(ip_eval["score"], ip_eval["msg"], "lexical")
        
    url_len = scan_results.get('url_length', 0)
    if url_len > 100:
        add_risk(15, "Abnormally long URL length (>100 chars)", "lexical")
    elif url_len > 75:
        add_risk(5, "Unusually long URL length (>75 chars)", "lexical")

    if scan_results.get('num_subdomains', 0) > 3:
        add_risk(20, "Excessive number of subdomains (often used in phishing)", "lexical")

    # Check for social engineering keywords in the URL
    suspicious_keywords = ['login', 'secure', 'account', 'update', 'verify', 'bank', 'paypal', 'signin', 'support']
    found_keywords = [kw for kw in suspicious_keywords if kw in url]
    if found_keywords and not is_highly_trusted:
        add_risk(10 * len(found_keywords), f"Suspicious keywords in URL ({', '.join(found_keywords)})", "lexical")
        
    # Abuse-heavy TLDs
    suspicious_tlds = ['.xyz', '.top', '.pw', '.cc', '.info', '.club', '.online', '.tk', '.ml', '.ga', '.cf', '.gq']
    if scan_results.get('tld') in suspicious_tlds:
        add_risk(25, f"Highly abused Top-Level Domain ({scan_results.get('tld')})", "lexical")

    # --- 2. ADVANCED SSL/TLS Checks ---
    ssl_data = scan_results.get('ssl', scan_results)
    ssl_warnings = ssl_data.get('warning_flags', [])

    if not ssl_data.get('is_valid', True):
        add_risk(65, "Invalid, expired, or missing SSL certificate", "ssl")    
    if ssl_data.get('is_self_signed', False):
        add_risk(65, "Self-signed certificate detected (Highly suspicious for public sites)", "ssl")
        
    ssl_age = ssl_data.get('cert_age_days', 999)
    if ssl_age < 2:
        add_risk(40, "SSL certificate is incredibly new (< 48 hours old)", "ssl")
    elif ssl_age < 14:
        add_risk(25, "SSL certificate is very new (< 14 days old)", "ssl")

    if any("Automated/Free DV" in flag for flag in ssl_warnings):
        add_risk(10, "Domain uses a free/automated SSL issuer (common in phishing)", "ssl")    
    if any("Deprecated/Weak TLS" in flag for flag in ssl_warnings):
        add_risk(25, "Server uses deprecated or weak TLS protocol", "ssl")    
    if any("Weak Cipher" in flag for flag in ssl_warnings):
        add_risk(15, "Server negotiated a weak cipher suite", "ssl")
        
    # SAN Pattern Guards
    san_flag = any("phishing kit signal" in flag for flag in ssl_warnings)
    if san_flag and not is_highly_trusted:
        add_risk(35, "Suspicious Subject Alternative Name (SAN) pattern (Phishing kit signal)", "ssl")
    
    if any("High number of SANs" in flag for flag in ssl_warnings) and not san_flag and not is_highly_trusted:
         add_risk(10, "High number of domains packed onto a single certificate", "ssl")
         
    if any("No CT Log Entries" in flag for flag in ssl_warnings):
        # Guard: crt.sh database lag
        if not is_highly_trusted and ssl_age >= 2:
            add_risk(15, "CT logs missing (Hidden cert or crt.sh API lag)", "ssl")    
            
    if any("Abnormally Short" in flag for flag in ssl_warnings):
        add_risk(15, "Certificate lifespan is abnormally short", "ssl")  

    # --- 3. IP Intelligence & Reputation ---
    if scan_results.get('is_blacklisted', False):
        add_risk(100, "Domain is explicitly flagged on a threat blacklist", "reputation")
    
    ip_warnings = ip_data.get("warning_flags", [])
 
    if any("VPN / Proxy" in f for f in ip_warnings):
        if not is_highly_trusted: 
            add_risk(30, "IP flagged as VPN / Proxy / Tor Exit Node", "reputation")
 
    if any("High-Risk Country" in f for f in ip_warnings):
        add_risk(20, "Site hosted in a country with high phishing infrastructure abuse", "reputation")
 
    if any("Suspicious Hosting ASN" in f for f in ip_warnings):
        add_risk(35, "Site hosted on ASN frequently associated with phishing/bulletproof hosting", "reputation")
 
    if ip_data.get("country_mismatch", False):
        add_risk(15, "Domain registered in a different country than its hosting location", "reputation")
 
    if ip_data and ip_data.get("ip_address") is None:
        add_risk(20, "Could not resolve domain to an IP address (DNS failure or non-existent domain)", "reputation")

    domain_age = scan_results.get('domain_age_days')
    if domain_age is None:
        domain_age = 999 
        
    if domain_age < 30:
        add_risk(45, "Domain was registered very recently (< 30 days ago)", "reputation")
    elif domain_age < 90:
        add_risk(20, "Domain is relatively new (< 90 days ago)", "reputation")

    # --- 4. Content / Fingerprinting ---
    if scan_results.get('has_obfuscated_scripts', False):
        add_risk(40, "Heavily obfuscated or packed JavaScript detected", "content")
        
    if scan_results.get('requests_external_executables', False):
        add_risk(70, "Page attempts to download executable payloads (.exe, .apk, .bat)", "content")
        
    if scan_results.get('has_hidden_iframes', False):
        add_risk(35, "Hidden iframes detected (often used for cryptojacking or drive-by downloads)", "content")

    if scan_results.get('forms_post_to_external_domain', False):
        add_risk(30, "HTML forms submit user data to an external/different domain", "content")

    # --- Final Score Normalization ---
    final_score = min(total_score, 100)
    
    if final_score >= 75:
        risk_level = "CRITICAL"
    elif final_score >= 50:
        risk_level = "HIGH"
    elif final_score >= 25:
        risk_level = "WARNING"
    else:
        risk_level = "SAFE"
        
    return {
        "final_score": final_score,
        "risk_level": risk_level,
        "category_breakdown": category_scores,
        "risk_factors": risk_factors
    }