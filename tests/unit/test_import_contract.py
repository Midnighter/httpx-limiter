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


"""Test which HTTP clients the package and its integrations import."""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap

import pytest


HTTP_CLIENTS = ("httpx", "httpx2")

# Each run starts a fresh interpreter in which the blocked HTTP clients cannot be
# imported, as if they were not installed, and reports what each import loaded.
SCRIPT = textwrap.dedent(
    """
    import importlib
    import json
    import sys

    for name in {blocked!r}:
        sys.modules[name] = None

    def loaded():
        return sorted(m for m in ("httpx", "httpx2") if sys.modules.get(m))

    import httpx_limiter
    import httpx_limiter.aiolimiter
    import httpx_limiter.pyrate

    result = {{"core": loaded(), "integrations": {{}}}}
    for name in ("httpx", "httpx2"):
        try:
            importlib.import_module(f"httpx_limiter.{{name}}")
        except ModuleNotFoundError as error:
            outcome = {{"error": str(error), "name": error.name}}
        else:
            outcome = {{"loaded": loaded()}}
        result["integrations"][name] = outcome
    print(json.dumps(result))
    """,
)


@pytest.mark.parametrize(
    "blocked",
    [(), ("httpx",), ("httpx2",), ("httpx", "httpx2")],
    ids=["none-blocked", "httpx-blocked", "httpx2-blocked", "both-blocked"],
)
def test_import_contract(blocked: tuple[str, ...]):
    """Test that each import pulls in exactly the HTTP clients that it needs."""
    result = json.loads(
        subprocess.run(  # noqa: S603
            [sys.executable, "-c", SCRIPT.format(blocked=blocked)],
            capture_output=True,
            text=True,
            check=True,
        ).stdout,
    )

    # The root package and the limiter integrations import no HTTP client.
    assert result["core"] == []
    # Integrations are imported in order, so the httpx2 integration may find httpx
    # already loaded by the httpx integration, but never the other way around.
    expected_loaded = {
        "httpx": ["httpx"],
        "httpx2": [c for c in HTTP_CLIENTS if c not in blocked],
    }
    for name, outcome in result["integrations"].items():
        if name in blocked:
            assert outcome["name"] == name
            assert f"httpx-limiter[{name}]" in outcome["error"]
        else:
            assert outcome == {"loaded": expected_loaded[name]}
