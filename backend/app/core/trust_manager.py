import os
from tldextract import extract

class TrustManager:
    def __init__(self):
        self.top_domains = set()
        self.file_path = os.path.join(os.path.dirname(__file__), "..", "data", "top-100k.txt")

    def load_cache(self):
        """Loads the saved text file into an ultra-fast in-memory lookup Set."""
        if not os.path.exists(self.file_path):
            print("[TrustManager] Cache file missing. Attempting emergency sync...")
            from app.utils.feed_syncer import sync_top_domains_feed
            sync_top_domains_feed()

        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as f:
                self.top_domains = {line.strip() for line in f if line.strip()}
            print(f"[TrustManager] Successfully loaded {len(self.top_domains)} major domains into RAM.")
        else:
            print("[TrustManager] Critical: No lookup database available.")

    def is_major_domain(self, url: str) -> bool:
        """
        Parses any URL down to its registered domain (e.g., 'sub.wikipedia.org/page' -> 'wikipedia.org')
        and checks it against the top 100k list in memory.
        """
        try:
            ext = extract(url)
            registered_domain = ext.registered_domain.lower() # Extracts "wikipedia.org" safely
            return registered_domain in self.top_domains
        except Exception:
            return False

# Single global instance (Singleton pattern used by enterprise engines)
trust_manager = TrustManager()