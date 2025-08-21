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

import pytest

from httpx_limiter import AsyncLimiter, Rate


@pytest.mark.parametrize(
    "rates",
    [
        pytest.param(
            [],
            marks=pytest.mark.raises(exception=ValueError, message="At least one rate"),
        ),
        [Rate.create(1)],
        [Rate.create(1), Rate.create(2)],
    ],
)
@pytest.mark.anyio
async def test_async_limiter_init(rates: list[Rate]):
    """Test the AsyncLimiter factory class method."""
    AsyncLimiter.create(*rates)


@pytest.mark.anyio
async def test_async_limiter_context():
    """Test that we can use the limiter to manage a context."""
    count = 0

    async with AsyncLimiter.create(Rate.create(1, duration=0.01)):
        count += 1

    assert count == 1
