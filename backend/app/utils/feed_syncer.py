# code for updating the top domains list. 
import os
import requests
import zipfile
import io

# We will use Cisco Umbrella's daily top 1 million domains list (free & highly reliable) 
FEED_URL = "http://s3-us-west-1.amazonaws.com/umbrella-static/top-1m.csv.zip"
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "top-100k.txt")

def sync_top_domains_feed(limit=100000):
    """
    Downloads the daily top 1M domains feed, extracts the top N, 
    and saves them cleanly to a local text file.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    print("[FeedSyncer] Syncing enterprise top domains list...")
    
    try:
        response = requests.get(FEED_URL, timeout=15)
        response.raise_for_status()
        
        # Extract the ZIP in memory
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            # Cisco's file inside the zip is 'top-1m.csv'
            with z.open("top-1m.csv") as f:
                domains = []
                for line in f:
                    # CSV format: rank,domain (e.g., 1,google.com)
                    parts = line.decode("utf-8").strip().split(",")
                    if len(parts) == 2:
                        domains.append(parts[1].lower())
                    if len(domains) >= limit:
                        break
                        
        # Write out our optimized local cache file
        with open(OUTPUT_FILE, "w") as out:
            out.write("\n".join(domains))
            
        print(f"[FeedSyncer] Successfully synced top {limit} domains!")
    except Exception as e:
        print(f"[FeedSyncer] Sync failed: {e}. Falling back to old list if exists.")