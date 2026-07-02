"""
Redis-backed rate limiting middleware per architecture blueprint.
"""

from __future__ import annotations

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Apply per-IP and per-route rate limits using Redis counters."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"

        if path.endswith("/auth/login") and request.method == "POST":
            key = f"ratelimit:login:{client_ip}"
            count = await cache_service.incr_with_ttl(
                key, settings.RATE_LIMIT_LOGIN_WINDOW_SEC
            )
            if count > settings.RATE_LIMIT_LOGIN_PER_IP:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many login attempts. Try again later."},
                )

        if path.endswith("/submissions") and request.method == "POST":
            auth = request.headers.get("Authorization", "")
            if auth.startswith("Bearer "):
                key = f"ratelimit:submit:{auth[-16:]}"
                count = await cache_service.incr_with_ttl(
                    key, settings.RATE_LIMIT_SUBMIT_WINDOW_SEC
                )
                if count > settings.RATE_LIMIT_SUBMIT_PER_USER:
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Submission rate limit exceeded."},
                    )

        return await call_next(request)
