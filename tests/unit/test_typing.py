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


"""Test the public typing of the HTTP integrations with mypy."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from mypy import api


TYPING_DIR = Path(__file__).parents[1] / "typing"
ERROR = re.compile(r"^(?P<path>.+?):(?P<line>\d+): error: .* \[(?P<code>[a-z-]+)\]$")
EXPECT = re.compile(r"# expect: (?P<code>[a-z-]+)$")


@pytest.fixture(scope="session")
def mypy_cache(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Provide a cache directory that the mypy runs of this session share."""
    return tmp_path_factory.mktemp("mypy-cache")


@pytest.mark.parametrize(
    "name",
    [
        pytest.param("accepted_httpx.py", id="accepted-httpx"),
        pytest.param("accepted_httpx2.py", id="accepted-httpx2"),
        pytest.param("rejected.py", id="rejected"),
    ],
)
def test_typing_examples(name: str, mypy_cache: Path):
    """Test that mypy reports exactly the errors that the examples expect."""
    module = TYPING_DIR / name
    expected = {
        (line_number, match["code"])
        for line_number, line in enumerate(module.read_text().splitlines(), start=1)
        if (match := EXPECT.search(line))
    }

    stdout, stderr, status = api.run(
        ["--cache-dir", str(mypy_cache), "--no-error-summary", str(module)],
    )

    assert status == (1 if expected else 0), f"{stdout}\n{stderr}"
    errors = [line for line in stdout.splitlines() if ": error: " in line]
    matches = [ERROR.match(line) for line in errors]
    assert all(matches), stdout
    reported = {
        (int(match["line"]), match["code"])
        for match in matches
        if match and Path(match["path"]).resolve() == module.resolve()
    }
    assert len(reported) == len(errors), stdout
    assert reported == expected, stdout
