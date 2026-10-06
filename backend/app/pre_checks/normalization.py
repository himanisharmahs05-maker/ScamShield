import urllib.parse
import posixpath
import unicodedata
import idna
import re

def normalize_url(url: str):
    # Initialize threat flags for the scoring engine
    flags = {
        "is_invalid": False,
        "mixed_script": False,
        "was_defanged": False
    }

    # 1. DoS Mitigation: Strict length limit (e.g., 2048 characters)
    if len(url) > 2048:
        flags["is_invalid"] = True
        return url, "", flags

    try:
        # --- ADVANCED: Refanging ---
        # Convert hxxp:// to http:// and [.] to .
        if 'hxxp' in url.lower() or '[.]' in url:
            url = re.sub(r'^hxxps?://', lambda m: 'https://' if 's' in m.group(0).lower() else 'http://', url, flags=re.IGNORECASE)
            url = url.replace('[.]', '.')
            flags["was_defanged"] = True

        # --- ADVANCED: Zero-Width Character Stripping ---
        # ASCII 0-31 + Unicode Zero-Width characters
        zero_width_chars = ['\u200b', '\u200c', '\u200d', '\ufeff']
        for zwc in zero_width_chars:
            url = url.replace(zwc, '')
        url = "".join(char for char in url.strip() if ord(char) > 31)
        
        # 3. Recursive Percent-Decoding (Max 5 iterations)
        for _ in range(5):
            decoded = urllib.parse.unquote(url)
            if decoded == url:
                break
            url = decoded

        # 4. Standardize Scheme and Hostname
        parsed = urllib.parse.urlsplit(url)
        scheme = parsed.scheme.lower() if parsed.scheme else "http"
        
        # --- ADVANCED: Path Normalization ---
        # Resolves /a/b/../c to /a/c
        normalized_path = parsed.path
        if normalized_path:
            normalized_path = posixpath.normpath(normalized_path)
            # Ensure root paths aren't accidentally stripped to '.'
            if normalized_path == '.':
                normalized_path = '/'
                
        hostname = ""
        if parsed.hostname:
            # 5. Mixed-Script Homoglyph Detection
            scripts = set()
            for char in parsed.hostname:
                if char.isalpha():
                    try:
                        script = unicodedata.name(char).split()[0]
                        scripts.add(script)
                    except ValueError:
                        pass
            
            if len(scripts) > 1:
                flags["mixed_script"] = True

            # 6. Punycode Conversion for Homograph Defense
            try:
                hostname = idna.encode(parsed.hostname).decode('ascii')
            except idna.IDNAError:
                hostname = parsed.hostname.lower()
                
            # --- ADVANCED: Port Stripping ---
            # Remove redundant default ports to improve cache hits
            netloc = hostname
            if parsed.port:
                if (scheme == 'http' and parsed.port == 80) or \
                   (scheme == 'https' and parsed.port == 443):
                    netloc = hostname 
                else:
                    netloc = f"{hostname}:{parsed.port}" 

            # Reconstruct the truly normalized URL
            normalized_url = parsed._replace(
                scheme=scheme, 
                netloc=netloc,
                path=normalized_path
            ).geturl()
            return normalized_url, hostname, flags
            
        return url, "", flags

    except ValueError:
        # Gracefully handle malformed parsing errors (e.g., bad IPv6)
        flags["is_invalid"] = True
        return url, "", flags