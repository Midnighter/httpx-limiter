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

from pytest_pyodide import run_in_pyodide
from pytest_pyodide.decorator import copy_files_to_pyodide


DISTRIBUTION_PATHS = [
    ("dist/", "dist/"),
    ("pyodide-dist/", "pyodide-dist/"),
]


@copy_files_to_pyodide(
    file_list=DISTRIBUTION_PATHS,
    install_wheels=True,
    recurse_directories=False,
)
@run_in_pyodide(packages=["ssl", "micropip", "httpx"])
async def test_aiolimiter_backend(selenium_standalone):
    import httpx
    from httpx_limiter import AsyncRateLimitedTransport, Rate

    # We need to replicate optional dependency installation in Pyodide,
    # unfortunately, since we cannot specify extras during the wheel installation.
    import micropip

    await micropip.install("aiolimiter ~=1.2")

    from httpx_limiter.aiolimiter import AiolimiterAsyncLimiter

    limiter = AiolimiterAsyncLimiter.create(Rate.create(magnitude=10, duration=1))
    async with httpx.AsyncClient(
        transport=AsyncRateLimitedTransport.create(limiter=limiter)
    ) as client:
        response = await client.get("https://httpbin.org/status/200")
        assert response.status_code == 200


@copy_files_to_pyodide(
    file_list=DISTRIBUTION_PATHS,
    install_wheels=True,
    recurse_directories=False,
)
@run_in_pyodide(packages=["ssl", "micropip", "httpx"])
async def test_pyrate_backend(selenium_standalone):
    import httpx
    from httpx_limiter import AsyncRateLimitedTransport, Rate

    # We need to replicate optional dependency installation in Pyodide,
    # unfortunately, since we cannot specify extras during the wheel installation.
    import micropip

    await micropip.install("pyrate-limiter ~=3.9")

    from httpx_limiter.pyrate import PyrateAsyncLimiter

    limiter = PyrateAsyncLimiter.create(Rate.create(magnitude=10, duration=1))
    async with httpx.AsyncClient(
        transport=AsyncRateLimitedTransport.create(limiter=limiter)
    ) as client:
        response = await client.get("https://httpbin.org/status/200")
        assert response.status_code == 200
