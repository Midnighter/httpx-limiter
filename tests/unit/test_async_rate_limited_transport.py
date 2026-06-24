# Copyright (c) 2024 Moritz E. Beber
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.


"""Test the expected functionality of the asynchronous rate-limited transport."""

import anyio
import httpx
import pytest
from pytest_httpx import HTTPXMock

from httpx_limiter import AbstractAsyncLimiter, AsyncRateLimitedTransport, Rate
from httpx_limiter.aiolimiter import AiolimiterAsyncLimiter
from httpx_limiter.pyrate import PyrateAsyncLimiter


@pytest.mark.anyio
async def test_aiolimiter_init():
    """Test that an asynchronous limited transport can be initialized."""
    AsyncRateLimitedTransport(
        limiter=AiolimiterAsyncLimiter.create(Rate.create()),
        transport=httpx.AsyncHTTPTransport(),
    )


@pytest.mark.anyio
async def test_pyrate_init():
    """Test that an asynchronous limited transport can be initialized."""
    AsyncRateLimitedTransport(
        limiter=PyrateAsyncLimiter.create(Rate.create()),
        transport=httpx.AsyncHTTPTransport(),
    )


@pytest.mark.anyio
async def test_aiolimiter_create():
    """Test that an asynchronous rate-limited transport can be created."""
    transport = AsyncRateLimitedTransport.create(
        limiter=AiolimiterAsyncLimiter.create(Rate.create()),
    )

    assert isinstance(transport, AsyncRateLimitedTransport)


@pytest.mark.anyio
async def test_pyrate_create():
    """Test that an asynchronous rate-limited transport can be created."""
    transport = AsyncRateLimitedTransport.create(
        limiter=PyrateAsyncLimiter.create(Rate.create()),
    )

    assert isinstance(transport, AsyncRateLimitedTransport)


@pytest.mark.parametrize(
    ("limiter", "rate", "request_count", "min_elapsed", "max_elapsed"),
    [
        # Burst only: all requests fit in initial capacity → completes quickly.
        (AiolimiterAsyncLimiter, Rate.create(magnitude=2, duration=0.2), 2, 0.0, 0.15),
        (PyrateAsyncLimiter, Rate.create(magnitude=2, duration=0.2), 2, 0.0, 0.2),
        # Beyond burst: must wait for at least one refill cycle.
        (AiolimiterAsyncLimiter, Rate.create(magnitude=2, duration=0.2), 4, 0.15, 0.6),
        (PyrateAsyncLimiter, Rate.create(magnitude=2, duration=0.2), 4, 0.15, 0.8),
        # Well beyond burst: must wait for multiple refill cycles.
        (AiolimiterAsyncLimiter, Rate.create(magnitude=2, duration=0.2), 6, 0.3, 1.0),
        (PyrateAsyncLimiter, Rate.create(magnitude=2, duration=0.2), 6, 0.3, 1.2),
    ],
)
@pytest.mark.anyio
async def test_handle_async_request(  # noqa: PLR0913
    limiter: type[AbstractAsyncLimiter],
    rate: Rate,
    request_count: int,
    min_elapsed: float,
    max_elapsed: float,
    httpx_mock: HTTPXMock,
):
    """Test that handled requests are rate-limited."""
    httpx_mock.add_callback(
        lambda _: httpx.Response(status_code=200), is_reusable=True,
    )

    # We submit a fixed number of requests and measure how long they take to complete.
    # If rate limiting is working, requests beyond the burst capacity must wait for
    # tokens to replenish. We assert elapsed time falls within a generous range:
    # the lower bound proves rate limiting is active, and the upper bound guards
    # against unexpected hangs.
    async with httpx.AsyncClient(
        transport=AsyncRateLimitedTransport.create(limiter=limiter.create(rate)),
    ) as client:
        start = anyio.current_time()
        async with anyio.create_task_group() as tg:
            for _ in range(request_count):
                tg.start_soon(client.get, "http://example.com")
        elapsed = anyio.current_time() - start

    assert elapsed >= min_elapsed, (
        f"Expected at least {min_elapsed}s, got {elapsed:.3f}s"
    )
    assert elapsed <= max_elapsed, (
        f"Expected at most {max_elapsed}s, got {elapsed:.3f}s"
    )
