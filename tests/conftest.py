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


"""Define the fixtures shared by the unit and acceptance tests."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

import pytest

from httpx_limiter_test_types import HTTPBackend


if TYPE_CHECKING:  # pragma: no cover
    from httpx_limiter import AbstractAsyncLimiter


@pytest.fixture(
    scope="session",
    params=[
        pytest.param(("asyncio", {"use_uvloop": False}), id="asyncio"),
    ],
)
def anyio_backend(request: pytest.FixtureRequest) -> tuple[str, dict[str, bool]]:
    """Set the anyio event loop."""
    return request.param


@pytest.fixture(
    params=[
        pytest.param(("aiolimiter", "AiolimiterAsyncLimiter"), id="aiolimiter"),
        pytest.param(("pyrate", "PyrateAsyncLimiter"), id="pyrate"),
    ],
)
def limiter_class(request: pytest.FixtureRequest) -> type[AbstractAsyncLimiter]:
    """
    Provide each limiter implementation.

    The import happens here and not at collection time, because the Pyodide tests
    run in a host environment without `httpx_limiter` installed.

    """
    module, name = request.param
    return getattr(import_module(f"httpx_limiter.{module}"), name)


@pytest.fixture(
    params=[
        pytest.param("httpx", id="httpx"),
        pytest.param("httpx2", id="httpx2"),
    ],
)
def http(request: pytest.FixtureRequest) -> HTTPBackend:
    """
    Provide each HTTP backend together with its integration.

    The imports happen here and not at collection time, so that a missing backend
    fails every test that needs it instead of being skipped.

    """
    return HTTPBackend.create(request.param)
