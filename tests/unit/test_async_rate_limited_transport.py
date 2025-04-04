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
from aiolimiter import AsyncLimiter
from pytest_httpx import HTTPXMock

from httpx_limiter import AsyncRateLimitedTransport, Rate


def test_init():
    """Test that an asynchronous rate-limited transport can be initialized."""
    AsyncRateLimitedTransport(
        limiter=AsyncLimiter(10),
        transport=httpx.AsyncHTTPTransport(),
    )


def test_create():
    """Test that an asynchronous rate-limited transport can be created."""
    transport = AsyncRateLimitedTransport.create(rate=Rate.create())
    assert isinstance(transport, AsyncRateLimitedTransport)


@pytest.mark.anyio
async def test_handle_async_request(httpx_mock: HTTPXMock):
    """Test that handled requests are rate-limited."""
    counter = 0

    async def count_responses(request: httpx.Request) -> httpx.Response:  # noqa: ARG001
        nonlocal counter

        counter += 1

        return httpx.Response(status_code=200)

    httpx_mock.add_callback(count_responses, is_reusable=True)

    # We configure the bucket with a rate of two to allow a burst of requests and a
    # refresh interval of 0.1 seconds. That means, when we create ten requests but then
    # cancel all outstanding requests after 0.06 seconds, a bit more than half the time
    # of the interval will have passed, and we expect a capacity of one to be returned.
    # Consequently, we expect three requests to succeed in total.
    async with (
        httpx.AsyncClient(
            transport=AsyncRateLimitedTransport.create(
                rate=Rate.create(magnitude=2, duration=0.1),
            ),
        ) as client,
        anyio.create_task_group() as tg,
    ):
        with anyio.move_on_after(0.07) as scope:
            for _ in range(10):
                tg.start_soon(client.get, "http://example.com")
            await anyio.sleep(2)

        tg.cancel_scope.cancel()

    assert scope.cancelled_caught
    assert counter == 3
