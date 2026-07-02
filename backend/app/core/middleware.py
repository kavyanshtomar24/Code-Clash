"""
Request logging middleware.

Logs method, path, response status code, and duration in milliseconds
for every HTTP request that passes through the application.
"""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("app.middleware")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs request method, path, status, and latency."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process the request, measure timing, and log the result."""
        start_time = time.perf_counter()

        response: Response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info(
            "%s %s → %d (%.1f ms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        return response
