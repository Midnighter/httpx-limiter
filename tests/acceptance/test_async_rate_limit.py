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

from collections import Counter
from time import perf_counter

import anyio
import httpx
import pytest

from httpx_limiter import AsyncLimiter, AsyncRateLimitedTransport, Rate


async def _record_response(client: httpx.AsyncClient, counter: Counter) -> None:
    response = await client.get("http://httpbin.localhost/status/200")
    counter[response.status_code] += 1


@pytest.mark.anyio
async def test_limits():
    """Test that an API's rate limit is maintained."""
    response_codes = Counter()

    async with (
        httpx.AsyncClient(
            transport=AsyncRateLimitedTransport(
                limiter=AsyncLimiter.create(
                    Rate.create(duration=1 / 20),
                    max_delay=6_000,
                    buffer_ms=1,
                ),
                transport=httpx.AsyncHTTPTransport(),
            ),
        ) as client,
        anyio.create_task_group() as group,
    ):
        start = perf_counter()

        for _ in range(100):
            group.start_soon(_record_response, client, response_codes)

    duration = perf_counter() - start
    # Making 100 requests at a rate of 20 requests per second should take around
    # five seconds.
    assert 5 < duration < 6, f"Requests took {duration=} seconds."

    assert response_codes.total() == 100
    assert response_codes[httpx.codes.OK] in range(95, 101)


@pytest.mark.anyio
async def test_exceed_limits():
    """
    Test that an API's rate limit is exceeded.

    We cannot predict exactly the alignment of the rate at which we make requests and
    the rate at which requests are accepted. Hence, we allow the response codes to be
    within a range of expected values.

    """
    response_codes = Counter()

    async with (
        httpx.AsyncClient(
            transport=AsyncRateLimitedTransport(
                limiter=AsyncLimiter.create(
                    Rate.create(duration=1 / 25),
                    max_delay=6_000,
                    buffer_ms=1,
                ),
                transport=httpx.AsyncHTTPTransport(),
            ),
        ) as client,
        anyio.create_task_group() as group,
    ):
        start = perf_counter()

        for _ in range(125):
            group.start_soon(_record_response, client, response_codes)

    duration = perf_counter() - start
    # Making 125 requests at a rate of 25 requests per second should take around
    # five seconds.
    assert 5 < duration < 6, f"Requests took {duration=} seconds."

    assert response_codes.total() == 125
    assert response_codes[httpx.codes.OK] in range(90, 101)
    assert response_codes[httpx.codes.TOO_MANY_REQUESTS] == (
        125 - response_codes[httpx.codes.OK]
    )
