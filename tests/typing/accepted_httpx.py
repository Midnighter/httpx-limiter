# Copyright (c) 2026 Moritz E. Beber
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
Provide typing examples for the HTTPX integration.

These examples are never run. `tests/unit/test_typing.py` checks them with mypy and
fails if mypy reports any error, so a regression in the public typing is caught.

"""

import ssl

import httpx

from httpx_limiter import AbstractAsyncLimiter, Rate
from httpx_limiter.aiolimiter import AiolimiterAsyncLimiter
from httpx_limiter.httpx import (
    AbstractRateLimiterRepository,
    AsyncMultiRateLimitedTransport,
    AsyncRateLimitedTransport,
    HTTPXAsyncHTTPTransportKeywordArguments,
)
from httpx_limiter.pyrate import PyrateAsyncLimiter


class CustomTransport(httpx.AsyncBaseTransport):
    """A custom transport that can be wrapped."""

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        """Return an empty response."""
        return httpx.Response(200, request=request)


class HostRepository(AbstractRateLimiterRepository):
    """A repository that overrides both abstract methods for HTTPX requests."""

    def get_identifier(self, request: httpx.Request) -> str:
        """Return the host of the request."""
        return request.url.host

    def create(self, request: httpx.Request) -> AbstractAsyncLimiter:  # noqa: ARG002
        """Return a limiter."""
        return PyrateAsyncLimiter.create(Rate.create())


def wrap_custom_transport() -> httpx.AsyncClient:
    """Wrap custom transports and use the result in a client."""
    limiter = AiolimiterAsyncLimiter.create(Rate.create())
    single = AsyncRateLimitedTransport(limiter=limiter, transport=CustomTransport())
    multi = AsyncMultiRateLimitedTransport(
        repository=HostRepository(),
        transport=single,
    )
    return httpx.AsyncClient(transport=multi)


def create_with_configuration() -> httpx.AsyncClient:
    """Create transports through the factories with HTTPX configuration objects."""
    limiter = AiolimiterAsyncLimiter.create(Rate.create())
    configuration: HTTPXAsyncHTTPTransportKeywordArguments = {
        "verify": ssl.create_default_context(),
        "limits": httpx.Limits(max_connections=10),
        "proxy": httpx.Proxy("http://localhost:8080"),
        "retries": 2,
    }
    single = AsyncRateLimitedTransport.create(limiter=limiter, **configuration)
    AsyncRateLimitedTransport.create(limiter, proxy=httpx.URL("http://localhost"))
    multi = AsyncMultiRateLimitedTransport.create(
        repository=HostRepository(),
        proxy="http://localhost:8080",
    )
    return httpx.AsyncClient(transport=multi if single else single)


def use_repository(request: httpx.Request) -> AbstractAsyncLimiter:
    """Use the repository with the matching request type."""
    return HostRepository().get(request)
