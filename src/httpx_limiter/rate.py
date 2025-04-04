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


"""Provide a definition of a rate."""

from __future__ import annotations

from datetime import timedelta
from typing import NamedTuple


Number = float | int


class Rate(NamedTuple):
    """Define the rate."""

    magnitude: float
    duration: timedelta

    @classmethod
    def create(cls, magnitude: Number = 1, duration: timedelta | Number = 1) -> Rate:
        """Create a rate."""
        magnitude = float(magnitude)

        if not isinstance(duration, timedelta):
            duration = timedelta(seconds=float(duration))

        return cls(magnitude=magnitude, duration=duration)

    def in_seconds(self) -> float:
        """Return the duration in unit seconds."""
        return self.duration.total_seconds()
