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

import httpx
from aiolimiter import AsyncLimiter

from httpx_limiter import AbstractRateLimiterRepository, Rate


class ConcreteRateLimiterRepository(AbstractRateLimiterRepository):
    """A concrete implementation of the abstract repository for testing."""

    def __init__(self, identifier: str, rate: Rate) -> None:
        super().__init__()
        self._rate = rate
        self._identifier = identifier

    def get_identifier(self, _: httpx.Request) -> str:
        """Return a predefined identifier for testing."""
        return self._identifier

    def get_rate(self, _: httpx.Request) -> Rate:
        """Return a predefined rate for testing."""
        return self._rate


class MethodRateLimiterRepository(AbstractRateLimiterRepository):
    """A concrete implementation of the abstract repository for testing."""

    def get_identifier(self, request: httpx.Request) -> str:
        """Return a method-based identifier for testing."""
        return request.method

    def get_rate(self, _: httpx.Request) -> Rate:
        """Return a constant rate."""
        return Rate.create(1)


def test_get_identifier():
    """Test that get_identifier is called and returns the expected value."""
    repo = ConcreteRateLimiterRepository(identifier="test_id", rate=Rate.create(1))

    result = repo.get_identifier(httpx.Request(method="GET", url="http://test.com"))

    assert result == "test_id"


def test_get_rate():
    """Test that get_rate is called and returns the expected value."""
    repo = ConcreteRateLimiterRepository(identifier="test_id", rate=Rate.create(9))

    result = repo.get_rate(httpx.Request(method="GET", url="http://test.com"))

    assert result.magnitude == 9

def test_get_new_limiter():
    """Test that get creates and returns a new limiter when needed."""
    repo = ConcreteRateLimiterRepository(identifier="test_id", rate=Rate.create(1))

    result = repo.get(httpx.Request(method="GET", url="http://test.com"))

    assert isinstance(result, AsyncLimiter)

def test_get_existing_limiter():
    """Test that get returns an existing limiter if available."""
    repo = ConcreteRateLimiterRepository(identifier="test_id", rate=Rate.create(1))

    first_limiter = repo.get(httpx.Request(method="GET", url="http://test.com"))
    second_limiter = repo.get(httpx.Request(method="GET", url="http://test.com"))

    assert second_limiter is first_limiter

def test_multiple_identifiers():
    """Test that different identifiers create different limiters."""
    repo = MethodRateLimiterRepository()

    first_limiter = repo.get(httpx.Request(method="GET", url="http://test.com"))
    second_limiter = repo.get(httpx.Request(method="POST", url="http://test.com"))

    assert second_limiter is not first_limiter
