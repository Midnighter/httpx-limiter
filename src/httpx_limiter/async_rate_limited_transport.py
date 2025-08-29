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


"""Provide an asynchronous rate-limited transport."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING


if sys.version_info < (3, 11):
    from typing_extensions import Unpack
else:
    from typing import Unpack

import httpx


if TYPE_CHECKING:  # pragma: no cover
    from .abstract_async_limiter import AbstractAsyncLimiter
    from .types import HTTPXAsyncHTTPTransportKeywordArguments


class AsyncRateLimitedTransport(httpx.AsyncBaseTransport):
    """
    Define the asynchronous rate-limited transport.

    This transport consists of a composed transport for handling requests and an
    implementation of a leaky bucket algorithm in order to rate-limit the number of
    requests.

    """

    def __init__(
        self,
        *,
        limiter: AbstractAsyncLimiter,
        transport: httpx.AsyncBaseTransport,
        **kwargs: dict[str, object],
    ) -> None:
        super().__init__(**kwargs)
        self._limiter = limiter
        self._transport = transport

    @classmethod
    def create(
        cls,
        limiter: AbstractAsyncLimiter,
        **kwargs: Unpack[HTTPXAsyncHTTPTransportKeywordArguments],
    ) -> AsyncRateLimitedTransport:
        """
        Create an instance of asynchronous rate-limited transport.

        This factory method constructs the instance with an underlying
        `httpx.AsyncHTTPTransport`.
        That transport is passed any additional keyword arguments.

        Args:
            limiter: A concrete instance of an asynchronous limiter.
            **kwargs: Additional keyword arguments are used in the construction of an
                `httpx.AsyncHTTPTransport`.

        Returns:
            A default instance of the class created from the given arguments.

        """
        return cls(
            limiter=limiter,
            transport=httpx.AsyncHTTPTransport(**kwargs),
        )

    async def handle_async_request(
        self,
        request: httpx.Request,
    ) -> httpx.Response:
        """Handle an asynchronous request with rate limiting."""
        async with self._limiter:
            return await self._transport.handle_async_request(request)
