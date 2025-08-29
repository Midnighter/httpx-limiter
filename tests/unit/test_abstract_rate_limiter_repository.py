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


"""Test the expected functionality of the rate limiter repository."""

from abc import abstractmethod
from collections.abc import Sequence

import httpx
import pytest

from httpx_limiter import AbstractAsyncLimiter, AbstractRateLimiterRepository, Rate
from httpx_limiter.aiolimiter import AiolimiterAsyncLimiter
from httpx_limiter.pyrate import PyrateAsyncLimiter


class ConcreteRepository(AbstractRateLimiterRepository):
    """A concrete aiolimiter-based repository implementation."""

    def __init__(self, identifier: str, rate: Rate) -> None:
        super().__init__()
        self._rate = rate
        self._identifier = identifier

    def get_identifier(self, request: httpx.Request) -> str:  # noqa: ARG002
        """Return a predefined identifier for testing."""
        return self._identifier

    @abstractmethod
    def create(self, request: httpx.Request) -> AbstractAsyncLimiter:
        """Return a rate-limited transport based on the rate."""


class AiolimiterRepository(ConcreteRepository):
    """A concrete aiolimiter-based repository implementation."""

    def create(self, request: httpx.Request) -> AbstractAsyncLimiter:  # noqa: ARG002
        """Return a rate-limited transport based on the rate."""
        return AiolimiterAsyncLimiter.create(self._rate)


class PyrateRepository(ConcreteRepository):
    """A concrete pyrate-based repository implementation."""

    def create(self, request: httpx.Request) -> AbstractAsyncLimiter:  # noqa: ARG002
        """Return a rate-limited transport based on the rate."""
        return PyrateAsyncLimiter.create(self._rate)


class MethodRateLimiterRepository(AbstractRateLimiterRepository):
    """A concrete implementation of the abstract repository for testing."""

    def get_identifier(self, request: httpx.Request) -> str:
        """Return a method-based identifier for testing."""
        return request.method

    def create(self, request: httpx.Request) -> AbstractAsyncLimiter:
        """Return a rate-limited transport based on the request method."""
        if request.method == "GET":
            return AiolimiterAsyncLimiter.create(Rate.create())

        return PyrateAsyncLimiter.create(Rate.create())


@pytest.mark.anyio
@pytest.mark.parametrize("repository", [AiolimiterRepository, PyrateRepository])
async def test_get_identifier(repository: type[ConcreteRepository]):
    """Test that get_identifier is called and returns the expected value."""
    repo = repository(identifier="test_id", rate=Rate.create(1))

    result = repo.get_identifier(httpx.Request(method="GET", url="http://test.com"))

    assert result == "test_id"


@pytest.mark.anyio
@pytest.mark.parametrize("repository", [AiolimiterRepository, PyrateRepository])
async def test_create(repository: type[ConcreteRepository]):
    """Test that create is called and returns the expected value."""
    repo = repository(identifier="test_id", rate=Rate.create(9))

    result = repo.create(httpx.Request(method="GET", url="http://test.com"))

    assert isinstance(result, AbstractAsyncLimiter)


@pytest.mark.anyio
@pytest.mark.parametrize("repository", [AiolimiterRepository, PyrateRepository])
async def test_get_existing_limiter(repository: type[ConcreteRepository]):
    """Test that get returns an existing limiter if available."""
    repo = repository(identifier="test_id", rate=Rate.create(1))

    first_limiter = repo.get(httpx.Request(method="GET", url="http://test.com"))
    second_limiter = repo.get(httpx.Request(method="GET", url="http://test.com"))

    assert second_limiter is first_limiter


@pytest.mark.anyio
async def test_multiple_identifiers():
    """Test that different identifiers create different limiters."""
    repo = MethodRateLimiterRepository()

    first_limiter = repo.get(httpx.Request(method="GET", url="http://test.com"))
    second_limiter = repo.get(httpx.Request(method="POST", url="http://test.com"))

    assert second_limiter is not first_limiter
