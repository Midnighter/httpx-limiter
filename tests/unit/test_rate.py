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


"""Test the expected functionality of the rate value object."""

from datetime import timedelta

import pytest

from httpx_limiter import Number, Rate


def test_init():
    """Test that the rate is properly initialized."""
    rate = Rate(magnitude=2, duration=timedelta(seconds=1))

    assert isinstance(rate.magnitude, int)
    assert rate.magnitude == 2

    assert isinstance(rate.duration, timedelta)
    assert rate.duration == timedelta(seconds=1)


@pytest.mark.parametrize(
    ("magnitude", "duration", "expected"),
    [
        (2, 3, Rate(magnitude=2, duration=timedelta(seconds=3))),
        (4, 5.2, Rate(magnitude=4, duration=timedelta(seconds=5.2))),
        (
            6,
            timedelta(microseconds=230),
            Rate(magnitude=6, duration=timedelta(microseconds=230)),
        ),
    ],
)
def test_create(magnitude: int, duration: timedelta | Number, expected: Rate):
    """Test that rates are properly created."""
    assert Rate.create(magnitude, duration) == expected


@pytest.mark.parametrize(
    ("duration", "expected"),
    [
        (timedelta(milliseconds=500), 500_000),
        (0.5, 500_000),
        (0.02, 20_000),
        (2, 2_000_000),
    ],
)
def test_in_microseconds(duration: timedelta | Number, expected: int):
    """Test that the duration is correctly converted to microseconds."""
    assert Rate.create(duration=duration).in_microseconds() == expected
