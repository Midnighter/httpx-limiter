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


@copy_files_to_pyodide(
    file_list=[("dist/", "pyodide-dist/")],
    install_wheels=True,
    recurse_directories=False,
)
@run_in_pyodide(packages=["ssl", "micropip", "httpx"])
def test_aiolimiter_backend(selenium):
    selenium.run(
        """
        from httpx_limiter import AsyncRateLimitedTransport, Rate
        """
    )
