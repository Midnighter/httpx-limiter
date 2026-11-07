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

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from httpx_limiter import AbstractAsyncLimiter, Rate
from httpx_limiter.aiolimiter import AiolimiterAsyncLimiter
from httpx_limiter.pyrate import PyrateAsyncLimiter


if TYPE_CHECKING:  # pragma: no cover
    from httpx_limiter_test_types import HTTPBackend, RateLimiterRepository, Request


def make_repository(
    http: HTTPBackend,
    limiter_class: type[AbstractAsyncLimiter],
    identifier: str,
    rate: Rate,
) -> RateLimiterRepository:
    """Return a new repository of the selected backend that returns fixed values."""

    class Repository(http.integration.AbstractRateLimiterRepository):
        """A concrete repository implementation for the selected backend."""

        def get_identifier(self, request: Request) -> str:  # noqa: ARG002
            """Return a predefined identifier for testing."""
            return identifier

        def create(self, request: Request) -> AbstractAsyncLimiter:  # noqa: ARG002
            """Return a rate limiter based on the rate."""
            return limiter_class.create(rate)

    return Repository()


def make_method_repository(http: HTTPBackend) -> RateLimiterRepository:
    """Return a new repository of the selected backend that separates by method."""

    class MethodRateLimiterRepository(http.integration.AbstractRateLimiterRepository):
        """A concrete implementation of the abstract repository for testing."""

        def get_identifier(self, request: Request) -> str:
            """Return a method-based identifier for testing."""
            return request.method

        def create(self, request: Request) -> AbstractAsyncLimiter:
            """Return a rate limiter based on the request method."""
            if request.method == "GET":
                return AiolimiterAsyncLimiter.create(Rate.create())

            return PyrateAsyncLimiter.create(Rate.create())

    return MethodRateLimiterRepository()


@pytest.mark.anyio
async def test_get_identifier(
    http: HTTPBackend,
    limiter_class: type[AbstractAsyncLimiter],
):
    """Test that get_identifier is called and returns the expected value."""
    repo = make_repository(http, limiter_class, "test_id", Rate.create(1))

    result = repo.get_identifier(
        http.client.Request(method="GET", url="http://test.com"),
    )

    assert result == "test_id"


@pytest.mark.anyio
async def test_create(http: HTTPBackend, limiter_class: type[AbstractAsyncLimiter]):
    """Test that create is called and returns the expected value."""
    repo = make_repository(http, limiter_class, "test_id", Rate.create(9))

    result = repo.create(http.client.Request(method="GET", url="http://test.com"))

    assert isinstance(result, limiter_class)


@pytest.mark.anyio
async def test_get_existing_limiter(
    http: HTTPBackend,
    limiter_class: type[AbstractAsyncLimiter],
):
    """Test that get returns an existing limiter if available."""
    repo = make_repository(http, limiter_class, "test_id", Rate.create(1))

    first_limiter = repo.get(http.client.Request(method="GET", url="http://test.com"))
    second_limiter = repo.get(http.client.Request(method="GET", url="http://test.com"))

    assert second_limiter is first_limiter


@pytest.mark.anyio
async def test_multiple_identifiers(http: HTTPBackend):
    """Test that different identifiers create different limiters."""
    repo = make_method_repository(http)

    first_limiter = repo.get(http.client.Request(method="GET", url="http://test.com"))
    second_limiter = repo.get(
        http.client.Request(method="POST", url="http://test.com"),
    )

    assert second_limiter is not first_limiter
    assert isinstance(first_limiter, AiolimiterAsyncLimiter)
    assert isinstance(second_limiter, PyrateAsyncLimiter)
