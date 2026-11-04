# Copyright (c) 2026 Moritz E. Beber
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


"""Provide an abstract repository for rate limiters of HTTPX requests."""

import httpx

from httpx_limiter._rate_limiter_repository import RateLimiterRepository


class AbstractRateLimiterRepository(RateLimiterRepository[httpx.Request]):
    """
    Define the abstract repository for rate limiters of HTTPX requests.

    This abstract base class provides a framework for managing rate limiters
    based on HTTPX requests. It maintains a cache of rate limiters and provides
    methods to retrieve request-specific identifiers and limiters.

    Subclasses must implement methods to determine how requests are identified
    and what rate limits should be applied to them.

    Methods:
        get_identifier: Return a request-specific identifier.
        create: Return a request-specific rate limiter.
        get: Return a request-specific rate limiter.

    """
