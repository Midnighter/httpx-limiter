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

from collections import Counter

import anyio
import httpx
import pytest

from httpx_limiter import (
    AbstractRateLimiterRepository,
    AsyncMultiRateLimitedTransport,
    Rate,
)


class HostRateLimiterRepository(AbstractRateLimiterRepository):
    """A concrete implementation of the abstract repository for testing."""

    def get_identifier(self, request: httpx.Request) -> str:
        """Return a host-based identifier for testing."""
        return request.url.host

    def get_rate(self, request: httpx.Request) -> Rate:
        """Return a host-dependent rate."""
        match self.get_identifier(request):
            case "httpbin.localhost":
                return Rate.create(duration=1 / 20)
            case "fast.localhost":
                return Rate.create(duration=1 / 40)
            case _:
                return Rate.create(1)


async def _record_response(
    client: httpx.AsyncClient,
    url: str,
    counter: Counter,
) -> None:
    response = await client.get(url)
    counter[response.status_code] += 1


@pytest.mark.anyio
async def test_limits():
    """Test that an API's rate limit is maintained."""
    httpx_client = httpx.AsyncClient(
        transport=AsyncMultiRateLimitedTransport.create(
            repository=HostRateLimiterRepository(),
        ),
    )

    slow_rate_codes = Counter()
    fast_rate_codes = Counter()

    async with anyio.create_task_group() as group:
        for _ in range(100):
            group.start_soon(
                _record_response,
                httpx_client,
                "http://httpbin.localhost/status/200",
                slow_rate_codes,
            )
            group.start_soon(
                _record_response,
                httpx_client,
                "http://fast.localhost/status/200",
                fast_rate_codes,
            )

    assert slow_rate_codes.total() == 100
    assert slow_rate_codes[httpx.codes.OK] == 100

    assert fast_rate_codes.total() == 100
    assert fast_rate_codes[httpx.codes.OK] == 100
