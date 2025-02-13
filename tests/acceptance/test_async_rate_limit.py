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

from collections import Counter

import anyio
import httpx
import pytest

from httpx_limiter import AsyncRateLimitedTransport


async def _record_response(client: httpx.AsyncClient, result: list[int]) -> None:
    response = await client.get("http://httpbin.localhost/status/200")
    result.append(response.status_code)


@pytest.mark.anyio
async def test_limits():
    """Test that an API's rate limit is maintained."""
    httpx_client = httpx.AsyncClient(
        transport=AsyncRateLimitedTransport.create(
            rate=29,
            capacity=30,
        ),
    )

    response_codes: list[int] = []

    async with anyio.create_task_group() as group:
        for _ in range(210):
            group.start_soon(_record_response, httpx_client, response_codes)

    assert len(response_codes) == 210
    assert all(code == 200 for code in response_codes)


@pytest.mark.anyio
async def test_exceed_limits():
    """Test that an API's rate limit are exceeded."""
    httpx_client = httpx.AsyncClient(
        transport=AsyncRateLimitedTransport.create(
            rate=40,
            capacity=40,
        ),
    )

    response_codes: list[int] = []

    async with anyio.create_task_group() as group:
        for _ in range(280):
            group.start_soon(_record_response, httpx_client, response_codes)

    assert len(response_codes) == 280

    codes_counter = Counter(response_codes)
    assert tuple(code for code, _ in codes_counter.most_common()) == (200, 429)
    assert codes_counter[200] == 210
    assert codes_counter[429] == 70
