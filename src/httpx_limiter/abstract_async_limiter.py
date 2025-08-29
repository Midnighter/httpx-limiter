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


"""Provide an abstract base class for asynchronous rate limiters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING


if TYPE_CHECKING:  # pragma: no cover
    from types import TracebackType


class AbstractAsyncLimiter(ABC):
    """
    Define an abstract base class for asynchronous rate limiters.

    This interface dictates that all asynchronous rate limiters shall implement the
    context manager protocol.

    """

    @abstractmethod
    async def __aenter__(self) -> AbstractAsyncLimiter:
        """Acquire a rate limit token upon entering the asynchronous context."""

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit the asynchronous context."""
