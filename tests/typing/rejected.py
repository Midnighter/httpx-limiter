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


"""
Provide typing examples that the type checkers must reject.

Each HTTP integration only accepts the objects of its own HTTP client. Every line that
ends in an `# expect: <code>` comment is a mixed-backend combination, and the comment
names the mypy error code it must produce. `tests/unit/test_typing.py` fails if mypy
reports any other error or misses an expected one.

"""

import httpx
import httpx2

from httpx_limiter import AbstractAsyncLimiter, Rate
from httpx_limiter.aiolimiter import AiolimiterAsyncLimiter
from httpx_limiter.httpx import (
    AbstractRateLimiterRepository as HTTPXRepository,
)
from httpx_limiter.httpx import (
    AsyncMultiRateLimitedTransport as HTTPXMultiTransport,
)
from httpx_limiter.httpx import (
    AsyncRateLimitedTransport as HTTPXTransport,
)
from httpx_limiter.httpx import (
    HTTPXAsyncHTTPTransportKeywordArguments as HTTPXKeywordArguments,
)
from httpx_limiter.httpx2 import (
    AbstractRateLimiterRepository as HTTPX2Repository,
)
from httpx_limiter.httpx2 import (
    AsyncMultiRateLimitedTransport as HTTPX2MultiTransport,
)
from httpx_limiter.httpx2 import (
    AsyncRateLimitedTransport as HTTPX2Transport,
)
from httpx_limiter.httpx2 import (
    HTTPXAsyncHTTPTransportKeywordArguments as HTTPX2KeywordArguments,
)


LIMITER = AiolimiterAsyncLimiter.create(Rate.create())


class HTTPXRequestRepository(HTTPXRepository):
    """A valid HTTPX repository."""

    def get_identifier(self, request: httpx.Request) -> str:
        """Return the host of the request."""
        return request.url.host

    def create(self, request: httpx.Request) -> AbstractAsyncLimiter:  # noqa: ARG002
        """Return a limiter."""
        return LIMITER


class HTTPX2RequestRepository(HTTPX2Repository):
    """A valid HTTPX2 repository."""

    def get_identifier(self, request: httpx2.Request) -> str:
        """Return the host of the request."""
        return request.url.host

    def create(self, request: httpx2.Request) -> AbstractAsyncLimiter:  # noqa: ARG002
        """Return a limiter."""
        return LIMITER


class HTTPX2RepositoryWithHTTPXRequests(HTTPX2Repository):
    """An HTTPX2 repository whose methods wrongly take HTTPX requests."""

    def get_identifier(self, request: httpx.Request) -> str:  # expect: override
        """Return the host of the request."""
        return request.url.host

    def create(self, request: httpx2.Request) -> AbstractAsyncLimiter:  # noqa: ARG002
        """Return a limiter."""
        return LIMITER


# Transports wrap only transports of their own backend.
HTTPXTransport(
    limiter=LIMITER,
    transport=httpx2.AsyncHTTPTransport(),  # expect: arg-type
)
HTTPX2Transport(
    limiter=LIMITER,
    transport=httpx.AsyncHTTPTransport(),  # expect: arg-type
)

# Repositories are bound to the requests of their own backend.
HTTPXMultiTransport(
    repository=HTTPX2RequestRepository(),  # expect: arg-type
    transport=httpx.AsyncHTTPTransport(),
)
HTTPX2MultiTransport(
    repository=HTTPXRequestRepository(),  # expect: arg-type
    transport=httpx2.AsyncHTTPTransport(),
)

# Factories take the configuration objects of their own backend.
HTTPXTransport.create(LIMITER, limits=httpx2.Limits())  # expect: arg-type
HTTPX2Transport.create(LIMITER, limits=httpx.Limits())  # expect: arg-type
HTTPXTransport.create(
    LIMITER,
    proxy=httpx2.Proxy("http://localhost"),  # expect: arg-type
)
HTTPX2Transport.create(LIMITER, proxy=httpx.URL("http://localhost"))  # expect: arg-type
HTTPXMulti = HTTPXMultiTransport.create(
    repository=HTTPXRequestRepository(),
    limits=httpx2.Limits(),  # expect: arg-type
)

# Keyword argument dictionaries are specific to a backend, too.
HTTPX_ARGUMENTS: HTTPXKeywordArguments = {
    "limits": httpx2.Limits(),  # expect: typeddict-item
}
HTTPX2_ARGUMENTS: HTTPX2KeywordArguments = {
    "limits": httpx.Limits(),  # expect: typeddict-item
}

# Clients accept only transports of their own backend.
httpx.AsyncClient(transport=HTTPX2Transport.create(LIMITER))  # expect: arg-type
httpx2.AsyncClient(transport=HTTPXTransport.create(LIMITER))  # expect: arg-type
