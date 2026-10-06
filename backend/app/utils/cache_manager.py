import json
import redis
from datetime import timedelta
import os

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")

redis_client = redis.Redis(
    host=REDIS_HOST, port=6379, db=0, decode_responses=True, socket_connect_timeout=0.5
)

try:
    redis_client.ping()
    REDIS_AVAILABLE = True
    print("[INFO] Redis Cache Connected Successfully!")
except Exception:
    REDIS_AVAILABLE = False
    print("[WARNING] Redis is offline. Running without cache.")


class ScanCache:
    @staticmethod
    def get_url_cache(url: str):
        if not REDIS_AVAILABLE:
            return None
        try:
            data = redis_client.get(f"url_scan:{url}")
            return json.loads(data) if data else None
        except Exception:
            return None

    @staticmethod
    def set_url_cache(url: str, scan_results: dict):
        if not REDIS_AVAILABLE:
            return
        try:
            redis_client.setex(f"url_scan:{url}", timedelta(hours=24), json.dumps(scan_results))
        except Exception:
            pass

    @staticmethod
    def get_domain_cache(domain: str):
        if not REDIS_AVAILABLE:
            return None
        try:
            data = redis_client.get(f"domain_scan:{domain}")
            return json.loads(data) if data else None
        except Exception:
            return None

    @staticmethod
    def set_domain_cache(domain: str, ip_data: dict, ssl_data: dict, reputation_data: dict):
        if not REDIS_AVAILABLE:
            return
        try:
            cache_data = {
                "ip_intel": ip_data,
                "ssl_data": ssl_data,
                "reputation": reputation_data,
            }
            redis_client.setex(f"domain_scan:{domain}", timedelta(hours=24), json.dumps(cache_data))
        except Exception:
            pass

    @staticmethod
    def get_ct_cache(domain: str):
        if not REDIS_AVAILABLE:
            return None
        try:
            data = redis_client.get(f"ct_logs:{domain}")
            return json.loads(data) if data else None
        except Exception:
            return None

    @staticmethod
    def set_ct_cache(domain: str, ct_data: dict):
        if not REDIS_AVAILABLE:
            return
        try:
            redis_client.setex(f"ct_logs:{domain}", timedelta(hours=48), json.dumps(ct_data))
        except Exception:
            pass