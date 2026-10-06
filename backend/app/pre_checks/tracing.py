import requests
import re
import socket
from urllib.parse import urlparse

# Common Web Application Firewall (WAF) / Anti-bot server headers
WAF_HEADERS = {"cloudflare", "sucuri", "imperva", "akamai", "ddos-guard"}

def trace_redirects(url: str, max_redirects: int = 10):
    results = {
        "initial_url": url,
        "final_url": url,
        "hop_count": 0,
        "is_cross_domain": False,
        "has_client_side_redirect": False,
        "redirect_loop_detected": False,
        "hit_captcha_or_waf": False, 
        "chain": [],
        "error": None,
        "hop_ips": [],
        "warning_flags": []
    }

    # 1. User-Agent Masquerading
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5"
    }

    initial_domain = urlparse(url).netloc
    
    # Configure a session to handle the redirects automatically
    session = requests.Session()
    session.max_redirects = max_redirects

    try:
        # 2. Request Execution with stream=True (Saves bandwidth & prevents Tarpits)
        response = session.get(url, headers=headers, allow_redirects=True, stream=True, timeout=(3.0, 5.0))
        
        # 3. Chain Analysis
        if response.history:
            results["hop_count"] = len(response.history)
            for resp in response.history:
                hop_url = resp.url
                results["chain"].append(hop_url)
                
                # Cross-Domain Check
                hop_domain = urlparse(hop_url).netloc
                if hop_domain != initial_domain:
                    results["is_cross_domain"] = True
                try:
                    hop_ip = socket.gethostbyname(hop_domain.split(':')[0]) # Split in case of ports
                    if hop_ip not in results["hop_ips"]:
                        results["hop_ips"].append(hop_ip)
                except Exception:
                    pass    
            
            # Add the final landing URL
            results["final_url"] = response.url
            results["chain"].append(response.url)
            
            # Final cross-domain check on the landing page
            if urlparse(response.url).netloc != initial_domain:
                results["is_cross_domain"] = True

        # --- ALWAYS CAPTURE FINAL DESTINATION IP ---
        # Runs whether there were redirects or not
        try:
            final_domain = urlparse(response.url).netloc
            final_ip = socket.gethostbyname(final_domain.split(':')[0])
            if final_ip not in results["hop_ips"]:
                results["hop_ips"].append(final_ip)
        except Exception:
            pass

        # ADVANCED: Detect WAFs / CAPTCHAs blocking the scanner
        server_header = response.headers.get("Server", "").lower()
        if response.status_code in [403, 503] and any(waf in server_header for waf in WAF_HEADERS):
            results["hit_captcha_or_waf"] = True

        # 4. Mitigation: Detect JS & Meta-Refresh Redirects
        content_chunk = next(response.iter_content(chunk_size=2048), b"").decode('utf-8', errors='ignore')
        
        if re.search(r'http-equiv=["\']?refresh["\']?', content_chunk, re.IGNORECASE) or \
           re.search(r'window\.location\s*=', content_chunk, re.IGNORECASE):
            results["has_client_side_redirect"] = True

    except requests.exceptions.TooManyRedirects:
        # Loop / Black Hole Detection
        results["redirect_loop_detected"] = True
        results["hop_count"] = max_redirects
    except requests.exceptions.Timeout:
        results["error"] = "Connection Timeout (Possible Tarpit)"
    except requests.exceptions.RequestException as e:
        results["error"] = type(e).__name__

    # Explicit Safety Check: 0 Hops means no loop is logically possible
    if results["hop_count"] == 0:
        results["redirect_loop_detected"] = False

    return results