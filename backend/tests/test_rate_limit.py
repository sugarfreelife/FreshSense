import pytest
from fastapi import HTTPException

from app.core.rate_limit import InMemoryRateLimiter


def test_sliding_window_blocks_then_allows_after_expiry():
    limiter = InMemoryRateLimiter()
    limiter.check("login:test-client", 2, 60, now=100)
    limiter.check("login:test-client", 2, 60, now=120)

    with pytest.raises(HTTPException) as blocked:
        limiter.check("login:test-client", 2, 60, now=130)
    assert blocked.value.status_code == 429
    assert blocked.value.headers["Retry-After"] == "30"

    limiter.check("login:test-client", 2, 60, now=161)


def test_rate_limit_isolated_by_action_and_client():
    limiter = InMemoryRateLimiter()
    limiter.check("login:client-a", 1, 60, now=100)
    limiter.check("register:client-a", 1, 60, now=100)
    limiter.check("login:client-b", 1, 60, now=100)


def test_rate_limit_storage_stays_bounded_for_many_client_keys():
    limiter = InMemoryRateLimiter(max_entries=2)
    limiter.check("login:client-a", 10, 60, now=100)
    limiter.check("login:client-b", 10, 60, now=101)
    limiter.check("login:client-c", 10, 60, now=102)
    assert len(limiter._requests) == 2
