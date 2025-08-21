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
from collections.abc import Sequence

import httpx

from .async_limiter import AsyncLimiter
from .rate import Rate


class AbstractRateLimiterRepository(ABC):
    """Define the abstract repository for rate limiters."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._limiters: dict[str, AsyncLimiter] = {}

    @abstractmethod
    def get_identifier(self, request: httpx.Request) -> str:
        """Return a request-specific identifier."""

    @abstractmethod
    def get_rates(self, request: httpx.Request) -> Sequence[Rate]:
        """Return one or more request-specific rates."""

    def get(self, request: httpx.Request) -> AsyncLimiter:
        """Return a request-specific rate limiter."""
        identifier = self.get_identifier(request)

        if identifier not in self._limiters:
            self._limiters[identifier] = AsyncLimiter.create(*self.get_rates(request))

        return self._limiters[identifier]
