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
Provide types shared by the test suites.

Pytest puts the `test-helpers` directory on `sys.path` (see `pythonpath` in
`pyproject.toml`), so tests import this module by name instead of from a
`conftest.py`.

"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, NamedTuple


if TYPE_CHECKING:  # pragma: no cover
    from types import ModuleType
    from typing import TypeAlias

    import httpx
    import httpx2

    import httpx_limiter.httpx
    import httpx_limiter.httpx2

    # The fixture selects the backend at run time, so tests annotate the objects that
    # they receive from it with the union of both backends' types.
    Request: TypeAlias = httpx.Request | httpx2.Request
    Response: TypeAlias = httpx.Response | httpx2.Response
    AsyncClient: TypeAlias = httpx.AsyncClient | httpx2.AsyncClient
    AsyncBaseTransport: TypeAlias = httpx.AsyncBaseTransport | httpx2.AsyncBaseTransport
    RateLimiterRepository: TypeAlias = (
        httpx_limiter.httpx.AbstractRateLimiterRepository
        | httpx_limiter.httpx2.AbstractRateLimiterRepository
    )


class HTTPBackend(NamedTuple):
    """
    Describe one HTTP backend and its integration.

    Attributes:
        name: The name of the HTTP client package, for example `httpx2`.
        client: The HTTP client package itself.
        integration: The matching `httpx_limiter` integration sub-package.

    """

    name: str
    client: ModuleType
    integration: ModuleType

    @classmethod
    def create(cls, name: str) -> HTTPBackend:
        """
        Import an HTTP client package and its integration.

        Args:
            name: The name of the HTTP client package, for example `httpx2`.

        Returns:
            The HTTP backend with both packages imported.

        """
        return cls(
            name=name,
            client=import_module(name),
            integration=import_module(f"httpx_limiter.{name}"),
        )
