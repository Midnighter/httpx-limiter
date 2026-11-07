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


"""Test httpx-limiter's compatibility with Pyodide."""

import pytest
from pytest_pyodide import run_in_pyodide
from pytest_pyodide.decorator import copy_files_to_pyodide


DISTRIBUTION_PATHS = [
    ("dist/", "dist/"),
]


@pytest.mark.parametrize("backend", ["httpx", "httpx2"])
@copy_files_to_pyodide(
    file_list=DISTRIBUTION_PATHS,
    install_wheels=True,
    recurse_directories=False,
)
@run_in_pyodide(packages=["micropip"])
async def test_aiolimiter_backend(selenium_standalone, backend):  # noqa: ARG001, ANN001
    """Test that we can import and use the aiolimiter backend in Pyodide."""
    from importlib import import_module

    # We need to replicate optional dependency installation in Pyodide,
    # unfortunately, since we cannot specify extras during the wheel installation.
    import micropip

    await micropip.install(
        [
            {"httpx": "httpx ~=0.25", "httpx2": "httpx2 ~=2.10"}[backend],
            "aiolimiter ~=1.2",
        ],
    )

    from httpx_limiter import Rate
    from httpx_limiter.aiolimiter import AiolimiterAsyncLimiter

    http = import_module(backend)
    integration = import_module(f"httpx_limiter.{backend}")

    def handler(request):  # noqa: ARG001, ANN001, ANN202
        return http.Response(200, text="OK")

    limiter = AiolimiterAsyncLimiter.create(Rate.create(magnitude=10, duration=1))
    async with http.AsyncClient(
        transport=integration.AsyncRateLimitedTransport(
            limiter=limiter,
            transport=http.MockTransport(handler=handler),
        ),
    ) as client:
        response = await client.get("http://example.com")
        assert response.status_code == 200
        assert response.text == "OK"
        assert type(response).__module__.split(".")[0] == backend


@pytest.mark.xfail(
    reason="The pyrate-limiter package includes multiprocessing and is thus not "
    "pyodide compatible.",
    strict=True,
)
@pytest.mark.parametrize("backend", ["httpx", "httpx2"])
@copy_files_to_pyodide(
    file_list=DISTRIBUTION_PATHS,
    install_wheels=True,
    recurse_directories=False,
)
@run_in_pyodide(packages=["micropip"])
async def test_pyrate_backend(selenium_standalone, backend):  # noqa: ARG001, ANN001
    """Test that we can import and use the pyrate backend in Pyodide."""
    from importlib import import_module

    # We need to replicate optional dependency installation in Pyodide,
    # unfortunately, since we cannot specify extras during the wheel installation.
    import micropip

    await micropip.install(
        [
            {"httpx": "httpx ~=0.25", "httpx2": "httpx2 ~=2.10"}[backend],
            "pyrate-limiter ~=4.0",
        ],
    )

    from httpx_limiter import Rate
    from httpx_limiter.pyrate import PyrateAsyncLimiter

    http = import_module(backend)
    integration = import_module(f"httpx_limiter.{backend}")

    def handler(request):  # noqa: ARG001, ANN001, ANN202
        return http.Response(200, text="OK")

    limiter = PyrateAsyncLimiter.create(Rate.create(magnitude=10, duration=1))
    async with http.AsyncClient(
        transport=integration.AsyncRateLimitedTransport(
            limiter=limiter,
            transport=http.MockTransport(handler=handler),
        ),
    ) as client:
        response = await client.get("http://example.com")
        assert response.status_code == 200
