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
from limiter import Limiter
from pytest_httpx import HTTPXMock

from httpx_limiter import AsyncRateLimitedTransport


def test_init():
    """Test that an asynchronous limited transport can be initialized."""
    AsyncRateLimitedTransport(limiter=Limiter(), transport=httpx.AsyncHTTPTransport())


def test_create():
    """Test that an asynchronous limited transport can be created."""
    transport = AsyncRateLimitedTransport.create(rate=10, capacity=10)
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

    # We configure the bucket to allow a burst of three requests and a refresh rate of
    # one. We then cancel all outstanding requests after 1.5 seconds, which
    # means that we only expect four requests to succeed.
    async with (
        httpx.AsyncClient(
            transport=AsyncRateLimitedTransport.create(rate=1, capacity=3),
        ) as client,
        anyio.create_task_group() as tg,
    ):
        with anyio.move_on_after(1.5) as scope:
            for _ in range(10):
                tg.start_soon(client.get, "http://example.com")
            await anyio.sleep(2)

        tg.cancel_scope.cancel()

    assert scope.cancelled_caught
    assert counter == 4
