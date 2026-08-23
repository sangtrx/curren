from __future__ import annotations

import hashlib
import threading
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    limit: int
    remaining: int
    retry_after_seconds: int


@dataclass
class _Bucket:
    window_started_at: float
    count: int


class FixedWindowRateLimiter:
    """Small single-process fixed-window limiter.

    This is intentionally dependency-free for Curren's initial single-process API.
    A distributed/global limit still belongs at ingress when the service scales to
    multiple workers or replicas.
    """

    def __init__(self, *, window_seconds: int = 60) -> None:
        self.window_seconds = max(1, int(window_seconds))
        self._buckets: dict[tuple[str, str], _Bucket] = {}
        self._lock = threading.Lock()

    def check(self, *, scope: str, identity: str, limit: int, now: float | None = None) -> RateLimitDecision:
        resolved_limit = max(1, int(limit))
        timestamp = time.monotonic() if now is None else float(now)
        key = (scope, identity)

        with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None or timestamp - bucket.window_started_at >= self.window_seconds:
                bucket = _Bucket(window_started_at=timestamp, count=0)
                self._buckets[key] = bucket

            elapsed = max(0.0, timestamp - bucket.window_started_at)
            retry_after = max(1, int(self.window_seconds - elapsed + 0.999))
            if bucket.count >= resolved_limit:
                return RateLimitDecision(
                    allowed=False,
                    limit=resolved_limit,
                    remaining=0,
                    retry_after_seconds=retry_after,
                )

            bucket.count += 1
            return RateLimitDecision(
                allowed=True,
                limit=resolved_limit,
                remaining=max(0, resolved_limit - bucket.count),
                retry_after_seconds=retry_after,
            )


def token_identity(token: str) -> str:
    """Return a non-secret stable identifier suitable for limiter bucket keys."""

    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:24]
