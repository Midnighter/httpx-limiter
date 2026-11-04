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


"""Provide an abstract repository for rate limiters."""

from abc import ABC, abstractmethod

import httpx

from .abstract_async_limiter import AbstractAsyncLimiter


class AbstractRateLimiterRepository(ABC):
    """
    Define the abstract repository for rate limiters.

    This abstract base class provides a framework for managing rate limiters
    based on HTTP requests. It maintains a cache of rate limiters and provides
    methods to retrieve request-specific identifiers, rates, and limiters.

    Subclasses must implement methods to determine how requests are identified
    and what rate limits should be applied to them.

    Methods:
        get_identifier: Return a request-specific identifier.
        get_rates: Return one or more request-specific rates.
        get: Return a request-specific rate limiter.

    """

    def __init__(self, **kwargs: dict[str, object]) -> None:
        super().__init__(**kwargs)
        self._limiters: dict[str, AbstractAsyncLimiter] = {}

    @abstractmethod
    def get_identifier(self, request: httpx.Request) -> str:
        """Return a request-specific identifier."""

    @abstractmethod
    def create(self, request: httpx.Request) -> AbstractAsyncLimiter:
        """Return a request-specific rate limiter."""

    def get(self, request: httpx.Request) -> AbstractAsyncLimiter:
        """Return a request-specific rate limiter."""
        identifier = self.get_identifier(request)

        if identifier not in self._limiters:
            self._limiters[identifier] = self.create(request)

        return self._limiters[identifier]
