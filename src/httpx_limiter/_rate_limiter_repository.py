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


"""Provide a backend-neutral, generic repository for rate limiters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar


if TYPE_CHECKING:  # pragma: no cover
    from .abstract_async_limiter import AbstractAsyncLimiter


RequestT = TypeVar("RequestT")


class RateLimiterRepository(ABC, Generic[RequestT]):
    """
    Define the backend-neutral repository for rate limiters.

    This internal base class maintains a cache of rate limiters keyed by a
    request-specific identifier. It is generic over the request type so that each
    HTTP integration can expose a repository specialized for its own requests.

    Methods:
        get_identifier: Return a request-specific identifier.
        create: Return a request-specific rate limiter.
        get: Return a cached request-specific rate limiter.

    """

    def __init__(self, **kwargs: dict[str, object]) -> None:
        super().__init__(**kwargs)
        self._limiters: dict[str, AbstractAsyncLimiter] = {}

    @abstractmethod
    def get_identifier(self, request: RequestT) -> str:
        """Return a request-specific identifier."""

    @abstractmethod
    def create(self, request: RequestT) -> AbstractAsyncLimiter:
        """Return a request-specific rate limiter."""

    def get(self, request: RequestT) -> AbstractAsyncLimiter:
        """Return a request-specific rate limiter."""
        identifier = self.get_identifier(request)

        if identifier not in self._limiters:
            self._limiters[identifier] = self.create(request)

        return self._limiters[identifier]
