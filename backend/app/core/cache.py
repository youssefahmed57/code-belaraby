import json
import time
import logging
from typing import Optional, Any
import redis
from app.core.config import settings

logger = logging.getLogger("cache")

_redis_client: Optional[redis.Redis] = None
_redis_retry_after: float = 0.0
_local_cache = {} # key -> (expiration_timestamp, value_dict_or_json)


def reset_cache_state() -> None:
    global _redis_client, _redis_retry_after
    _redis_client = None
    _redis_retry_after = 0.0
    _local_cache.clear()

def get_redis_client() -> Optional[redis.Redis]:
    global _redis_client, _redis_retry_after
    if _redis_client is not None:
        return _redis_client
    now = time.time()
    if _redis_retry_after > now:
        return None
    if settings.REDIS_URL:
        try:
            r = redis.Redis.from_url(
                settings.REDIS_URL,
                socket_timeout=1.5,
                socket_connect_timeout=0.5,
                decode_responses=True,
            )
            if r.ping():
                _redis_client = r
                return _redis_client
        except Exception as e:
            _redis_retry_after = now + 30
            logger.warning(f"Redis connection unavailable for caching: {e}")
    return None

def cache_get(key: str) -> Optional[Any]:
    r = get_redis_client()
    if r:
        try:
            val = r.get(f"cache:{key}")
            if val:
                return json.loads(val)
        except Exception as e:
            logger.warning(f"Redis get failed for {key}: {e}")
    
    # Local fallback
    now = time.time()
    if key in _local_cache:
        exp, val = _local_cache[key]
        if now < exp:
            return val
        else:
            del _local_cache[key]
    return None

def cache_set(key: str, value: Any, ttl_seconds: int = 300):
    r = get_redis_client()
    if r:
        try:
            r.setex(f"cache:{key}", ttl_seconds, json.dumps(value))
            return
        except Exception as e:
            logger.warning(f"Redis set failed for {key}: {e}")
            
    # Local fallback
    exp = time.time() + ttl_seconds
    _local_cache[key] = (exp, value)

def cache_invalidate(pattern: str):
    r = get_redis_client()
    if r:
        try:
            keys = r.keys(f"cache:{pattern}")
            if keys:
                r.delete(*keys)
        except Exception as e:
            logger.warning(f"Redis invalidate failed for pattern {pattern}: {e}")
            
    # Local fallback clear
    keys_to_del = [k for k in _local_cache if pattern.replace("*", "") in k]
    for k in keys_to_del:
        del _local_cache[k]
