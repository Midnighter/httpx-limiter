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


"""Provide an asynchronous rate-limited transport."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, TypedDict


if sys.version_info < (3, 11):
    from typing_extensions import Unpack
else:
    from typing import Unpack

from pyrate_limiter import (
    AbstractClock,
    BucketAsyncWrapper,
    Duration,
    InMemoryBucket,
    Limiter,
    TimeAsyncClock,
    validate_rate_list,
)
from pyrate_limiter import Rate as PyRate

from httpx_limiter import AbstractAsyncLimiter


if TYPE_CHECKING:  # pragma: no cover
    from types import TracebackType

    from httpx_limiter.rate import Rate


class PyRateLimiterKeywordArguments(TypedDict, total=False):
    """Keyword arguments for the pyrate limiter."""

    clock: AbstractClock
    raise_when_fail: bool
    max_delay: int | Duration | None
    retry_until_max_delay: bool
    buffer_ms: int


class PyrateAsyncLimiter(AbstractAsyncLimiter):
    """
    Define an asynchronous limiter that composes the pyrate limiter.

    This class encapsulates the creation and configuration of a pyrate-limiter
    Limiter with appropriate async bucket wrapper and settings.

    Args:
        limiter: An instance of an asynchronous pyrate limiter.
        **kwargs: Additional keyword arguments for the parent classes.

    """

    def __init__(self, *, limiter: Limiter, **kwargs: dict[str, object]) -> None:
        super().__init__(**kwargs)
        self._limiter = limiter

    @classmethod
    def create(
        cls,
        *rates: Rate,
        **kwargs: Unpack[PyRateLimiterKeywordArguments],
    ) -> PyrateAsyncLimiter:
        """Create an instance of PyrateAsyncLimiter."""
        if not rates:
            msg = "At least one rate must be provided."
            raise ValueError(msg)

        rate_limits = [
            PyRate(limit=rate.magnitude, interval=rate.in_milliseconds())
            for rate in rates
        ]
        if not validate_rate_list(rates=rate_limits):
            url = "https://pyratelimiter.readthedocs.io/en/latest/#defining-rate-limits-and-buckets"
            msg = (
                f"Invalid ordering of rates provided {rate_limits}. Please read "
                f"{url} for more information."
            )
            raise ValueError(msg)

        # Cast kwargs to proper types for internal use
        limiter = Limiter(
            argument=BucketAsyncWrapper(InMemoryBucket(rate_limits)),
            clock=kwargs.get("clock", TimeAsyncClock()),
            raise_when_fail=kwargs.get("raise_when_fail", False),
            max_delay=kwargs.get("max_delay", Duration.HOUR),
            retry_until_max_delay=kwargs.get("retry_until_max_delay", True),
            buffer_ms=kwargs.get("buffer_ms", 50),
        )
        return cls(limiter=limiter)

    async def __aenter__(self) -> PyrateAsyncLimiter:  # noqa: PYI034
        """Acquire a token upon entering the asynchronous context."""
        # Keep trying to acquire, let timeouts be handled externally.
        while not (await self._limiter.try_acquire_async("httpx-limiter")):
            pass  # pragma: no cover

        return self

    async def __aexit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: TracebackType | None,
    ) -> None:
        """Exit the asynchronous context."""
