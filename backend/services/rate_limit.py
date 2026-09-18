"""Small in-memory rate limiter for authentication endpoints.

For multi-instance production deployments, replace this with a shared store
such as Redis. It still protects a single local/server process from repeated
password-guessing attempts without adding another deployment dependency.
"""
import asyncio
import time
from collections import defaultdict, deque
from fastapi import HTTPException


class LoginRateLimiter:
    def __init__(self, max_attempts: int = 5, window_seconds: int = 15 * 60):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempts = defaultdict(deque)
        self._lock = asyncio.Lock()

    def _prune(self, key: str, now: float):
        attempts = self._attempts[key]
        while attempts and now - attempts[0] >= self.window_seconds:
            attempts.popleft()
        return attempts

    async def check(self, key: str):
        async with self._lock:
            now = time.monotonic()
            attempts = self._prune(key, now)
            if len(attempts) >= self.max_attempts:
                retry_after = max(1, int(self.window_seconds - (now - attempts[0])) + 1)
                raise HTTPException(
                    status_code=429,
                    detail="Too many failed sign-in attempts. Please try again later.",
                    headers={"Retry-After": str(retry_after)},
                )

    async def record_failure(self, key: str):
        async with self._lock:
            now = time.monotonic()
            attempts = self._prune(key, now)
            attempts.append(now)

    async def reset(self, key: str):
        async with self._lock:
            self._attempts.pop(key, None)


login_rate_limiter = LoginRateLimiter()
