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


"""Provide an asynchronous rate-limited transport using aiolimiter."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aiolimiter import AsyncLimiter

from httpx_limiter import AbstractAsyncLimiter


if TYPE_CHECKING:  # pragma: no cover
    from types import TracebackType

    from httpx_limiter.rate import Rate


class AiolimiterAsyncLimiter(AbstractAsyncLimiter):
    """
    Define an asynchronous limiter that composes the aiolimiter AsyncLimiter.

    This class encapsulates the creation and configuration of an aiolimiter
    AsyncLimiter with appropriate settings.

    Args:
        limiter: An instance of an aiolimiter AsyncLimiter.
        **kwargs: Additional keyword arguments for the parent classes.

    """

    def __init__(self, *, limiter: AsyncLimiter, **kwargs: dict[str, object]) -> None:
        super().__init__(**kwargs)
        self._limiter = limiter

    @classmethod
    def create(cls, rate: Rate) -> AiolimiterAsyncLimiter:
        """
        Create an instance of AiolimiterAsyncLimiter.

        Note: aiolimiter only supports a single rate limit, unlike pyrate-limiter
        which supports multiple rates.
        """
        limiter = AsyncLimiter(
            max_rate=rate.magnitude,
            time_period=rate.in_seconds(),
        )
        return cls(limiter=limiter)

    async def __aenter__(self) -> AiolimiterAsyncLimiter:  # noqa: PYI034
        """Acquire a token upon entering the asynchronous context."""
        await self._limiter.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit the asynchronous context."""
        await self._limiter.__aexit__(exc_type=exc_type, exc=exc_val, tb=exc_tb)
