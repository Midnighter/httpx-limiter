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
from httpx_limiter.pyrate import PyrateAsyncLimiter


if TYPE_CHECKING:  # pragma: no cover
    from httpx_limiter_test_types import AsyncClient, HTTPBackend


async def _record_response(client: AsyncClient, counter: Counter[int]) -> None:
    response = await client.get("http://httpbin.localhost/status/200")
    counter[response.status_code] += 1


@pytest.fixture
async def slower(limiter_class: type[AbstractAsyncLimiter]) -> AbstractAsyncLimiter:
    """Fixture for a slower rate limiter."""
    rate = Rate.create(duration=1 / 20)
    if limiter_class is PyrateAsyncLimiter:
        return PyrateAsyncLimiter.create(rate, buffer_ms=1)

    return limiter_class.create(rate)


@pytest.mark.anyio
async def test_limits(http: HTTPBackend, slower: AbstractAsyncLimiter):
    """Test that an API's rate limit is maintained."""
    response_codes: Counter[int] = Counter()

    start = perf_counter()

    async with (
        http.client.AsyncClient(
            transport=http.integration.AsyncRateLimitedTransport.create(
                limiter=slower,
            ),
        ) as client,
        anyio.create_task_group() as group,
    ):
        for _ in range(100):
            group.start_soon(_record_response, client, response_codes)

    duration = perf_counter() - start
    # Making 100 requests at a rate of 20 requests per second should take around
    # five seconds.
    assert 5 <= duration < 6, f"Requests took {duration=} seconds."

    assert response_codes.total() == 100
    assert response_codes[http.client.codes.OK] in range(95, 101)


@pytest.fixture
async def faster(limiter_class: type[AbstractAsyncLimiter]) -> AbstractAsyncLimiter:
    """Fixture for a faster rate limiter."""
    rate = Rate.create(duration=1 / 40)
    if limiter_class is PyrateAsyncLimiter:
        return PyrateAsyncLimiter.create(rate, buffer_ms=1)

    return limiter_class.create(rate)


@pytest.mark.anyio
async def test_exceed_limits(http: HTTPBackend, faster: AbstractAsyncLimiter):
    """
    Test that an API's rate limit is exceeded.

    We cannot predict exactly the alignment of the rate at which we make requests and
    the rate at which requests are accepted. Hence, we make requests at twice the
    server's rate and assert properties of the responses rather than exact counts.

    """
    server_rate = 20
    server_burst = 5
    request_count = 100
    response_codes: Counter[int] = Counter()

    start = perf_counter()

    async with (
        http.client.AsyncClient(
            transport=http.integration.AsyncRateLimitedTransport.create(
                limiter=faster,
            ),
        ) as client,
        anyio.create_task_group() as group,
    ):
        for _ in range(request_count):
            group.start_soon(_record_response, client, response_codes)

    duration = perf_counter() - start
    # Making 100 requests at a rate of 40 requests per second should take around
    # 2.5 seconds, so we only check that the limiter did not let them all through
    # at once.
    assert duration >= 2, f"Requests took {duration=} seconds."

    assert response_codes.total() == request_count
    assert set(response_codes) == {
        http.client.codes.OK,
        http.client.codes.TOO_MANY_REQUESTS,
    }
    assert response_codes[http.client.codes.OK] > 0
    assert response_codes[http.client.codes.TOO_MANY_REQUESTS] > 0
    # The server cannot accept much more than its rate times the elapsed time, plus
    # its burst. A 20% tolerance covers timing jitter.
    max_accepted = server_rate * duration * 1.2 + server_burst
    assert response_codes[http.client.codes.OK] <= max_accepted, f"{response_codes=}"
