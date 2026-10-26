"""Small per-process request limits for sensitive endpoints."""

from collections import OrderedDict, deque
from math import ceil
from threading import Lock
from time import monotonic

from fastapi import Depends, HTTPException, Request, status

from app.core.deps import get_current_user
from app.models.user import User


class InMemoryRateLimiter:
    """Sliding-window limiter for the single-instance deployment profile."""

    def __init__(self, max_entries: int = 4096) -> None:
        self._requests: OrderedDict[str, deque[float]] = OrderedDict()
        self._lock = Lock()
        self._max_entries = max_entries

    def check(self, key: str, limit: int, window_seconds: int, *, now: float | None = None) -> None:
        current = monotonic() if now is None else now
        cutoff = current - window_seconds
        with self._lock:
            requests = self._requests.get(key)
            if requests is None:
                requests = deque()
                self._requests[key] = requests
            else:
                self._requests.move_to_end(key)
            while requests and requests[0] <= cutoff:
                requests.popleft()
            if len(requests) >= limit:
                retry_after = max(1, ceil(window_seconds - (current - requests[0])))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many attempts. Please wait before trying again.",
                    headers={"Retry-After": str(retry_after)},
                )
            requests.append(current)

            # Bound the process-local map and discard expired windows from other keys.
            if len(self._requests) > self._max_entries:
                for stale_key, stale_requests in tuple(self._requests.items()):
                    while stale_requests and stale_requests[0] <= cutoff:
                        stale_requests.popleft()
                    if not stale_requests:
                        self._requests.pop(stale_key, None)
                while len(self._requests) > self._max_entries:
                    self._requests.popitem(last=False)

    def clear(self) -> None:
        """Reset counters, primarily for isolated tests."""
        with self._lock:
            self._requests.clear()


auth_rate_limiter = InMemoryRateLimiter()


def limit_auth_requests(request: Request) -> None:
    action = request.url.path.rsplit("/", 1)[-1]
    if action == "register":
        limit, window = 8, 60
    else:
        limit, window = 10, 60
    client_host = request.client.host if request.client else "unknown"
    auth_rate_limiter.check(f"{action}:{client_host}", limit, window)


def limit_scan_requests(request: Request, current: User = Depends(get_current_user)) -> None:
    client_host = request.client.host if request.client else "unknown"
    auth_rate_limiter.check(f"scan:{client_host}:{current.id}", 15, 60)
