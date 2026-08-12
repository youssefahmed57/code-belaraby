import math
import time
from collections import defaultdict
from typing import DefaultDict, Optional, Tuple

from fastapi import HTTPException, Request, status

from app.core.cache import get_redis_client
from app.core.config import settings


_local_rate_limit_store: DefaultDict[str, list[float]] = defaultdict(list)


class RateLimitRule:
    def __init__(self, key: str, limit: int, window_seconds: int):
        self.key = key
        self.limit = limit
        self.window_seconds = window_seconds


ROUTE_LIMITS: list[tuple[str, str, RateLimitRule]] = [
    ("POST", "/api/v1/auth/login", RateLimitRule("auth_login", 30, 60)),
    ("POST", "/api/v1/auth/register", RateLimitRule("auth_register", 10, 60)),
    ("POST", "/api/v1/auth/forgot-password", RateLimitRule("auth_forgot_password", 5, 300)),
    ("POST", "/api/v1/auth/reset-password", RateLimitRule("auth_reset_password", 5, 300)),
    ("POST", "/api/v1/coding-problems/run", RateLimitRule("code_run", 30, 60)),
    ("POST", "/api/v1/coding-problems/submit", RateLimitRule("code_submit", 20, 60)),
    ("POST", "/api/v1/quizzes/", RateLimitRule("quiz_mutation", 20, 60)),
    ("POST", "/api/v1/payments/upload-receipt", RateLimitRule("receipt_upload", 6, 300)),
    ("GET", "/api/v1/videos/token/", RateLimitRule("video_token", 30, 60)),
    ("POST", "/api/v1/videos/progress", RateLimitRule("video_progress", 30, 60)),
]


def _redis_key(rule: RateLimitRule, scope_key: str) -> str:
    return f"rate_limit:{rule.key}:{scope_key}"


def _scope_key(request: Request) -> str:
    client_ip = request.client.host if request.client else "unknown"
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip() or client_ip
    return client_ip


def _match_rule(request: Request) -> Optional[RateLimitRule]:
    path = request.url.path
    method = request.method.upper()
    for rule_method, prefix, rule in ROUTE_LIMITS:
        if method != rule_method:
            continue
        if prefix.endswith("/") and path.startswith(prefix):
            return rule
        if path == prefix:
            return rule
    return None


def _check_local_limit(rule: RateLimitRule, scope_key: str) -> Tuple[bool, int]:
    now = time.time()
    store_key = _redis_key(rule, scope_key)
    history = [stamp for stamp in _local_rate_limit_store[store_key] if now - stamp < rule.window_seconds]
    if len(history) >= rule.limit:
        retry_after = max(1, math.ceil(rule.window_seconds - (now - history[0])))
        _local_rate_limit_store[store_key] = history
        return False, retry_after
    history.append(now)
    _local_rate_limit_store[store_key] = history
    return True, rule.window_seconds


def _check_redis_limit(rule: RateLimitRule, scope_key: str) -> Tuple[bool, int]:
    redis_client = get_redis_client()
    if redis_client is None:
        if settings.requires_isolated_code_execution():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="خدمة الحماية من الإساءة غير متاحة حالياً.",
            )
        return _check_local_limit(rule, scope_key)

    key = _redis_key(rule, scope_key)
    current = redis_client.incr(key)
    if current == 1:
        redis_client.expire(key, rule.window_seconds)

    ttl = redis_client.ttl(key)
    retry_after = ttl if ttl and ttl > 0 else rule.window_seconds
    if current > rule.limit:
        return False, retry_after
    return True, retry_after


def enforce_request_rate_limit(request: Request) -> None:
    rule = _match_rule(request)
    if rule is None:
        return

    allowed, retry_after = _check_redis_limit(rule, _scope_key(request))
    if allowed:
        return

    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="تم تجاوز الحد الأقصى للطلبات لهذه العملية. يرجى المحاولة لاحقاً.",
        headers={"Retry-After": str(retry_after)},
    )
