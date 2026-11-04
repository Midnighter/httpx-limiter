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


"""Provide an asynchronous multiple rate-limited transport."""

from __future__ import annotations

from typing import TYPE_CHECKING, Unpack

import httpx2


if TYPE_CHECKING:  # pragma: no cover
    from .abstract_rate_limiter_repository import AbstractRateLimiterRepository
    from .types import HTTPXAsyncHTTPTransportKeywordArguments


class AsyncMultiRateLimitedTransport(httpx2.AsyncBaseTransport):
    """
    Define the asynchronous multiple rate-limited transport.

    This transport consists of a composed transport for handling requests and a
    repository for rate limiters that are selected based on the request.

    """

    def __init__(
        self,
        *,
        repository: AbstractRateLimiterRepository,
        transport: httpx2.AsyncBaseTransport,
        **kwargs: dict[str, object],
    ) -> None:
        super().__init__(**kwargs)
        self._repo = repository
        self._transport = transport

    @classmethod
    def create(
        cls,
        *,
        repository: AbstractRateLimiterRepository,
        **kwargs: Unpack[HTTPXAsyncHTTPTransportKeywordArguments],
    ) -> AsyncMultiRateLimitedTransport:
        """
        Create an instance of an asynchronous multiple rate-limited transport.

        This factory method constructs the instance with an underlying
        `httpx2.AsyncHTTPTransport`.
        That transport is passed any additional keyword arguments.

        Args:
            repository: The repository to use for rate limiters.
            **kwargs: Additional keyword arguments are used in the construction of an
                `httpx2.AsyncHTTPTransport`.

        Returns:
            A default instance of the class created from the given arguments.

        """
        return cls(
            repository=repository,
            transport=httpx2.AsyncHTTPTransport(**kwargs),
        )

    async def handle_async_request(
        self,
        request: httpx2.Request,
    ) -> httpx2.Response:
        """Handle an asynchronous request with rate limiting."""
        limiter = self._repo.get(request)
        async with limiter:
            return await self._transport.handle_async_request(request)

    async def aclose(self) -> None:
        """
        Close the transport and its underlying transport.

        Closing this wrapper also closes the composed transport, which is why
        sharing an inner transport between wrappers shares its lifetime.

        """
        await self._transport.aclose()
