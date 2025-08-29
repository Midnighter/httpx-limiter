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


"""Test the AsyncLimiter class."""

from datetime import timedelta

import pytest

from httpx_limiter import AbstractAsyncLimiter, Rate
from httpx_limiter.aiolimiter import AiolimiterAsyncLimiter
from httpx_limiter.pyrate import PyrateAsyncLimiter


@pytest.mark.parametrize(
    "rates",
    [
        pytest.param(
            [],
            marks=pytest.mark.raises(exception=ValueError, message="At least one rate"),
        ),
        [Rate.create(1)],
        [
            Rate.create(1, 0.01),
            Rate.create(2),
            Rate.create(10, timedelta(hours=1)),
            Rate.create(100, timedelta(days=1)),
        ],
        pytest.param(
            [Rate.create(1, timedelta(hours=1)), Rate.create(2)],
            marks=pytest.mark.raises(
                exception=ValueError,
                message="Invalid ordering of rates provided",
            ),
        ),
    ],
)
@pytest.mark.anyio
async def test_async_limiter_init(rates: list[Rate]):
    """Test the pyrate-based AsyncLimiter factory class method."""
    PyrateAsyncLimiter.create(*rates)


@pytest.mark.parametrize(
    "rate",
    [
        Rate.create(1),
        Rate.create(1, 0.01),
        Rate.create(1, 20),
    ],
)
@pytest.mark.anyio
async def test_aiolimiter_async_limiter_init(rate: Rate):
    """Test the aiolimiter-based AsyncLimiter factory class method."""
    AiolimiterAsyncLimiter.create(rate)


@pytest.fixture(scope="module", params=[PyrateAsyncLimiter, AiolimiterAsyncLimiter])
async def limiter(
    anyio_backend: tuple[str, dict[str, bool]],  # noqa: ARG001
    request: pytest.FixtureRequest,
) -> AbstractAsyncLimiter:
    """Fixture for creating concrete asynchronous limiter instances."""
    return request.param.create(Rate.create(1, duration=0.01))


@pytest.mark.anyio
async def test_async_limiter_context(limiter: AbstractAsyncLimiter):
    """Test that we can use the limiter to manage a context."""
    count = 0

    async with limiter:
        count += 1

    assert count == 1
