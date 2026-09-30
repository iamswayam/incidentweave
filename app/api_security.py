"""Shared-secret protection and an in-process API rate limiter.

This is NOT production-grade authentication (no user accounts, no key rotation,
no per-user quotas); real auth remains deferred.
The limiter is in memory: its counters reset on restart and are not shared across
multiple workers or instances.
"""

from __future__ import annotations

import secrets
from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import Header, HTTPException, Request

from app.config import settings

RATE_LIMIT_REQUESTS = 10
RATE_LIMIT_WINDOW_SECONDS = 60.0


class SlidingWindowRateLimiter:
    """Limit requests per client IP using an in-memory sliding window."""

    def __init__(self, max_requests: int, window_seconds: float) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests_by_client: dict[str, deque[float]] = defaultdict(deque)
        self.lock = Lock()

    def check(self, client_ip: str) -> None:
        now = monotonic()
        cutoff = now - self.window_seconds
        with self.lock:
            requests = self.requests_by_client[client_ip]
            while requests and requests[0] <= cutoff:
                requests.popleft()
            if len(requests) >= self.max_requests:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "code": "rate_limit_exceeded",
                        "message": "Request limit exceeded. Try again later.",
                    },
                )
            requests.append(now)

    def reset(self) -> None:
        """Clear counters for deterministic tests and process shutdown."""

        with self.lock:
            self.requests_by_client.clear()


rate_limiter = SlidingWindowRateLimiter(
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
)


def require_api_access(
    request: Request,
    x_api_secret: str | None = Header(default=None, alias="X-API-Secret"),
) -> None:
    """Validate the shared secret, then enforce the per-IP request limit."""

    configured_secret = settings.api_protection_secret
    if not configured_secret or not x_api_secret or not secrets.compare_digest(
        configured_secret, x_api_secret
    ):
        raise HTTPException(
            status_code=401,
            detail={
                "code": "unauthorized",
                "message": "A valid X-API-Secret header is required.",
            },
        )

    client_ip = request.client.host if request.client is not None else "unknown"
    rate_limiter.check(client_ip)