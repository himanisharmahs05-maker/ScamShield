import requests
from bs4 import BeautifulSoup
import json

def safe_classify_url(url: str) -> str:
    try:
        # Create a session to handle redirects and cookies efficiently
        session = requests.Session()
        headers = {'User-Agent': 'ScamShield-Security-Scanner/1.0'}
        
        # 1. RESOLUTION LAYER (Redirect Tracing)
        # This will resolve bit.ly, t.co, etc., to the final target URL.
        # max_redirects=5 prevents infinite loop attacks.
        print(f"Tracing URL: {url}")
        response = session.get(url, headers=headers, timeout=10, stream=True, allow_redirects=True)
        response.raise_for_status()
        
        # The final URL after all redirects are followed
        final_url = response.url
        print(f"Resolved to: {final_url}")

        # 2. THE PRE-FLIGHT CHECK (Using the resolved URL)
        content_type = response.headers.get('Content-Type', '').lower()

        # ==========================================
        # ROUTE 1: STANDARD WEB PAGES
        # ==========================================
        if any(t in content_type for t in ['text/html', 'text/plain']):
            # Now safe to download the body since it's an HTML page
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            for script in soup(["script", "style"]):
                script.extract()
            clean_text = soup.get_text(separator=' ', strip=True)[:3000]
            return "Webpage (LLM Classified)"

        
        # ==========================================

        # ROUTE 2: DATA & APIs (Safe to parse)

        # ==========================================

        elif any(t in content_type for t in ['application/json', 'application/xml', 'text/xml', 'text/csv']):

            # For JSON, convert to string. For XML/CSV, just read the text.

            clean_text = response.text[:3000]

            # ---> Send to LLM

            return "API Data (LLM Classified)"





        # ==========================================

        # ROUTE 3: DOCUMENTS (Needs special parsers)

        # ==========================================

        elif any(t in content_type for t in [

            'application/pdf', 

            'application/msword', # .doc

            'application/vnd.openxmlformats-officedocument', # .docx, .xlsx, .pptx

            'application/vnd.ms-excel', 

            'application/rtf'

        ]):

            response.close()

            # Note: Hackers hide macro-viruses in Office docs.

            return "Document (PDF/Office) - Potential Macro Risk"





        # ==========================================

        # ROUTE 4: ARCHIVES & COMPRESSION (High Risk)

        # ==========================================

        elif any(t in content_type for t in [

            'application/zip', 

            'application/x-rar-compressed', 

            'application/x-7z-compressed', 

            'application/x-tar', 

            'application/gzip',

            'application/x-bzip2'

        ]):

            response.close()

            return "Archive File (ZIP/RAR) - Requires Deep Scan"





        # ==========================================

        # ROUTE 5: EXECUTABLES & BINARIES (Critical Risk)

        # ==========================================

        elif any(t in content_type for t in [

            'application/x-msdownload', # .exe, .dll, .msi

            'application/x-executable', # Linux binaries

            'application/x-mach-binary', # Mac binaries

            'application/vnd.android.package-archive', # Android .apk

            'application/x-apple-diskimage', # Mac .dmg

            'application/octet-stream' # Generic raw binary / forced download

        ]):

            response.close()

            return "CRITICAL: Direct Executable Download"





        # ==========================================

        # ROUTE 6: MEDIA (Visual/Audio)

        # ==========================================

        elif any(t in content_type for t in ['image/', 'video/', 'audio/']):

            response.close()

            return "Media File (Image/Video/Audio)"





        # ==========================================

        # ROUTE 7: SCRIPTS & STYLES (Code files)

        # ==========================================

        elif any(t in content_type for t in ['application/javascript', 'text/javascript', 'text/css']):

            response.close()

            return "Web Asset (JavaScript/CSS)"





        # ==========================================

        # ROUTE 8: UNKNOWN / EDGE CASES

        # ==========================================

        else:

            response.close()

            return f"Unknown Content Type: {content_type}"
        
        # Add a fallback closure for remaining routes
        response.close()
        return f"Unknown Content Type: {content_type}"

    except requests.exceptions.TooManyRedirects:
        return "CRITICAL: Infinite Redirect Loop / Too many hops"
    except requests.exceptions.RequestException as e:
        return f"Network Error: {e}"