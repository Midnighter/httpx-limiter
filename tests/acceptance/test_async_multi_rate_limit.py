# Copyright (c) 2025 Moritz E. Beber
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


"""
Test the expected behavior of the asynchronous rate-limited transport.

These tests expect the local service stack defined in the `compose.yaml` file to be
started. The service that we query lies behind a traefik proxy which implements a
rate limiting middleware (see https://doc.traefik.io/traefik/middlewares/http/ratelimit/)
that allows an average of twenty requests per second.

"""

from __future__ import annotations

from collections import Counter
from time import perf_counter
from typing import TYPE_CHECKING

import anyio
import pytest

from httpx_limiter import AbstractAsyncLimiter, Rate
from httpx_limiter.aiolimiter import AiolimiterAsyncLimiter
from httpx_limiter.pyrate import PyrateAsyncLimiter


if TYPE_CHECKING:  # pragma: no cover
    from httpx_limiter_test_types import (
        AsyncClient,
        HTTPBackend,
        RateLimiterRepository,
        Request,
    )


def make_repository(
    http: HTTPBackend,
    limiter_class: type[AbstractAsyncLimiter],
) -> RateLimiterRepository:
    """Return a host-based repository of the selected backend and limiter."""

    class HostBasedRepository(http.integration.AbstractRateLimiterRepository):
        """A concrete implementation of the abstract repository for testing."""

        def get_identifier(self, request: Request) -> str:
            """Return a host-based identifier for testing."""
            return request.url.host

        def create(self, request: Request) -> AbstractAsyncLimiter:
            """Return a rate limiter based on the request."""
            match self.get_identifier(request):
                case "httpbin.localhost":
                    rate = Rate.create(duration=1 / 20)
                case "fast.localhost":
                    rate = Rate.create(duration=1 / 40)
                case _:
                    rate = Rate.create()

            if limiter_class is PyrateAsyncLimiter:
                return PyrateAsyncLimiter.create(rate, buffer_ms=1)

            return AiolimiterAsyncLimiter.create(rate)

    return HostBasedRepository()


async def _record_response(
    client: AsyncClient,
    url: str,
    counter: Counter[int],
) -> None:
    response = await client.get(url)
    counter[response.status_code] += 1


@pytest.mark.anyio
async def test_limits(http: HTTPBackend, limiter_class: type[AbstractAsyncLimiter]):
    """Test that an API's rate limit is maintained."""
    slow_rate_codes: Counter[int] = Counter()
    fast_rate_codes: Counter[int] = Counter()

    start = perf_counter()

    async with (
        http.client.AsyncClient(
            transport=http.integration.AsyncMultiRateLimitedTransport.create(
                repository=make_repository(http, limiter_class),
            ),
        ) as client,
        anyio.create_task_group() as group,
    ):
        for _ in range(100):
            group.start_soon(
                _record_response,
                client,
                "http://httpbin.localhost/status/200",
                slow_rate_codes,
            )
            group.start_soon(
                _record_response,
                client,
                "http://fast.localhost/status/200",
                fast_rate_codes,
            )

    duration = perf_counter() - start
    # Making 100 requests at a rate of 20 requests per second should take around
    # five seconds; at 40 per second it should take around 2.5 seconds.
    assert 2.5 <= duration < 6, f"Requests took {duration=} seconds."

    assert slow_rate_codes.total() == 100
    assert slow_rate_codes[http.client.codes.OK] in range(95, 101)

    assert fast_rate_codes.total() == 100
    # Surprisingly, aiolimiter is less predictable.
    assert fast_rate_codes[http.client.codes.OK] in range(90, 101)
