"""Simple in-memory rate limiter middleware"""
import time
from collections import defaultdict
from fastapi import Request, HTTPException


class RateLimiter:
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._clients: dict = defaultdict(list)

    def _clean(self, client_id: str, now: float):
        cutoff = now - self.window
        self._clients[client_id] = [t for t in self._clients[client_id] if t > cutoff]

    def check(self, client_id: str) -> bool:
        now = time.time()
        self._clean(client_id, now)
        if len(self._clients[client_id]) >= self.max_requests:
            return False
        self._clients[client_id].append(now)
        return True


_limiter = RateLimiter(max_requests=120, window_seconds=60)  # 120 req/min per client


async def rate_limit_middleware(request: Request, call_next):
    client_id = request.client.host if request.client else "unknown"
    if not _limiter.check(client_id):
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后重试")
    return await call_next(request)
