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


@run_in_pyodide(packages=["httpx-limiter"])
def test_imports(selenium_standalone):
    from httpx_limiter.aiolimiter import AiolimiterAsyncLimiter
