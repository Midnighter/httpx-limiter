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


"""Provide an asynchronous multiple rate-limited transport."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx


if TYPE_CHECKING:  # pragma: no cover
    from .abstract_rate_limiter_repository import AbstractRateLimiterRepository


class AsyncMultiRateLimitedTransport(httpx.AsyncBaseTransport):
    """
    Define the asynchronous multiple rate-limited transport.

    This transport consists of a composed transport for handling requests and a
    repository for rate limiters that are selected based on the request.

    """

    def __init__(
        self,
        *,
        repository: AbstractRateLimiterRepository,
        transport: httpx.AsyncBaseTransport,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._repo = repository
        self._transport = transport

    @classmethod
    def create(
        cls,
        *,
        repository: AbstractRateLimiterRepository,
        **kwargs: dict,
    ) -> AsyncMultiRateLimitedTransport:
        """
        Create an instance of an asynchronous multiple rate-limited transport.

        This factory method constructs the instance with an underlying
        `httpx.AsyncHTTPTransport`.
        That transport is passed any additional keyword arguments.

        Args:
            repository: The repository to use for rate limiters.
            **kwargs: Additional keyword arguments are used in the construction of an
                `httpx.AsyncHTTPTransport`.

        Returns:
            A default instance of the class created from the given arguments.

        """
        return cls(
            repository=repository,
            transport=httpx.AsyncHTTPTransport(**kwargs),  # type: ignore[arg-type]
        )

    async def handle_async_request(
        self,
        request: httpx.Request,
    ) -> httpx.Response:
        """Handle an asynchronous request with rate limiting."""
        limiter = self._repo.get(request)
        async with limiter:
            return await self._transport.handle_async_request(request)
