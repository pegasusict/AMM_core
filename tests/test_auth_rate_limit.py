from __future__ import annotations

import asyncio

import pytest

from auth.rate_limit import SlidingWindowRateLimiter


def test_sliding_window_blocks_then_recovers() -> None:
    now = 1000.0

    def clock() -> float:
        return now

    limiter = SlidingWindowRateLimiter(clock=clock)

    ok1, retry1 = asyncio.run(
        limiter.allow("login:ip", max_attempts=2, window_seconds=60)
    )
    ok2, retry2 = asyncio.run(
        limiter.allow("login:ip", max_attempts=2, window_seconds=60)
    )
    blocked, retry3 = asyncio.run(
        limiter.allow("login:ip", max_attempts=2, window_seconds=60)
    )

    assert ok1 is True and retry1 == 0
    assert ok2 is True and retry2 == 0
    assert blocked is False and retry3 > 0

    now += 61.0
    ok3, retry4 = asyncio.run(
        limiter.allow("login:ip", max_attempts=2, window_seconds=60)
    )
    assert ok3 is True and retry4 == 0


def test_sliding_window_isolated_per_key() -> None:
    limiter = SlidingWindowRateLimiter(clock=lambda: 42.0)

    ok1, _ = asyncio.run(limiter.allow("key-a", max_attempts=1, window_seconds=60))
    blocked_a, _ = asyncio.run(
        limiter.allow("key-a", max_attempts=1, window_seconds=60)
    )
    ok_b, _ = asyncio.run(limiter.allow("key-b", max_attempts=1, window_seconds=60))

    assert ok1 is True
    assert blocked_a is False
    assert ok_b is True
