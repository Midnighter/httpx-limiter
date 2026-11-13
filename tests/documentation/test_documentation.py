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
Test code examples in documentation.

We assume that examples in the documentation are at a similar level as acceptance tests.
Every Python code block runs on its own. Blocks that define an asynchronous `main`
function are awaited, with the `AsyncHTTPTransport` of both HTTP clients replaced by a
`MockTransport`, so that requests pass through the documented rate-limited transports
without touching the network. Which HTTP client an example uses is explicit in its
imports, and `test_examples_exist_for_both_backends` requires examples for both.

"""

from __future__ import annotations

import inspect
import re
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from mktestdocs import grab_code_blocks


if TYPE_CHECKING:  # pragma: no cover
    from types import ModuleType


ROOT_DIR = Path(__file__).parents[2]
DOCS = sorted([*(ROOT_DIR / "docs").glob("**/*.md"), ROOT_DIR / "README.md"])
EXAMPLES = [
    pytest.param(block, id=f"{document.relative_to(ROOT_DIR)}::{index}")
    for document in DOCS
    for index, block in enumerate(grab_code_blocks(document.read_text()))
]
# The documents that must show examples for each HTTP client.
BACKENDS_PER_DOCUMENT = {
    "README.md": {"httpx", "httpx2"},
    "docs/tutorial.md": {"httpx", "httpx2"},
    "docs/how-to/adapt-rate-limit.md": {"httpx", "httpx2"},
    "docs/how-to/per-domain-limit.md": {"httpx", "httpx2"},
    "docs/how-to/combine-retries.md": {"httpx", "httpx2"},
}


def _backends_used(block: str) -> set[str]:
    """Return the HTTP integrations that a code block imports."""
    return set(re.findall(r"httpx_limiter\.(httpx2?)\b", block))


def _mock_transport_factory(client: ModuleType, seen: list[str]) -> object:
    """Create a replacement for `AsyncHTTPTransport` that records requests."""
    signature = inspect.signature(client.AsyncHTTPTransport)

    def handler(request: object) -> object:
        seen.append(client.__name__)
        return client.Response(
            200,
            json={"remaining": 3},
            headers={"X-RateLimit-Remaining": "3"},
            request=request,
        )

    def factory(**kwargs: object) -> object:
        # Binding the arguments rejects keywords that the real transport does not take.
        signature.bind(**kwargs)
        return client.MockTransport(handler)

    return factory


@pytest.fixture
def requests_seen(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Replace the network transport of both HTTP clients and record requests."""
    seen: list[str] = []

    for name in ("httpx", "httpx2"):
        client = import_module(name)
        monkeypatch.setattr(
            client,
            "AsyncHTTPTransport",
            _mock_transport_factory(client, seen),
        )

    return seen


@pytest.mark.anyio
@pytest.mark.parametrize("block", EXAMPLES)
async def test_document_examples_independently(
    block: str,
    requests_seen: list[str],
):
    """
    Run an individual code example from a document.

    Each code block must be completely independent of each other, for example, imports
    must be restated within each block. An asynchronous `main` function is awaited, and
    when it makes requests, they must have passed through the mock transport of each
    HTTP client whose integration the block imports.

    """
    namespace: dict[str, object] = {"__name__": "__main__"}
    exec(block, namespace)  # noqa: S102

    main = namespace.get("main")
    if inspect.iscoroutinefunction(main):
        await main()

        if ".get(" in block:
            assert set(requests_seen) == _backends_used(block)


@pytest.mark.parametrize(("document", "expected"), BACKENDS_PER_DOCUMENT.items())
def test_examples_exist_for_both_backends(document: str, expected: set[str]):
    """Require awaited examples for each HTTP client in the listed documents."""
    awaited: set[str] = set()

    for block in grab_code_blocks((ROOT_DIR / document).read_text()):
        if "async def main" in block and ".get(" in block:
            awaited |= _backends_used(block)

    assert awaited == expected
