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
Check that the wheel does not require an HTTP client unconditionally.

Usage: `python check_wheel_metadata.py dist`. The script checks every wheel in the
given directories, so it does not rely on the shell to expand a glob, which Windows
does not do. Every `Requires-Dist` entry for `httpx` or `httpx2` must be guarded by
the extra of the same name.

"""

from __future__ import annotations

import logging
import re
import sys
import zipfile
from importlib.metadata import PathDistribution
from pathlib import Path


logger = logging.getLogger(__name__)

HTTP_CLIENTS = ("httpx", "httpx2")
# Hatchling writes requirements as `<name><specifier>; extra == '<extra>'`.
REQUIREMENT = re.compile(
    r"^(?P<name>[A-Za-z0-9._-]+)[^;]*(?:;\s*(?P<marker>.+))?$",
)


def check(wheel: Path) -> list[str]:
    """Return the problems with the HTTP client requirements of a wheel."""
    with zipfile.ZipFile(wheel) as archive:
        metadata = next(
            (
                name
                for name in archive.namelist()
                if name.endswith(".dist-info/METADATA")
            ),
            None,
        )
        if metadata is None:
            return [f"{wheel.name}: the wheel contains no METADATA file."]

        dist_info = zipfile.Path(archive, metadata).parent
        requirements = PathDistribution(dist_info).requires or []

    problems = []
    found = set()
    for line in requirements:
        match = REQUIREMENT.match(line)
        name = match["name"].lower() if match else line
        if name not in HTTP_CLIENTS:
            continue
        found.add(name)
        marker = match["marker"] if match else None
        if marker is None:
            problems.append(f"{wheel.name}: {line!r} is not optional.")
        elif not re.fullmatch(rf"extra\s*==\s*['\"]{name}['\"]", marker.strip()):
            problems.append(f"{wheel.name}: {line!r} is not in the matching extra.")
    problems.extend(
        f"{wheel.name}: no '{client}' extra requires {client}."
        for client in HTTP_CLIENTS
        if client not in found
    )
    return problems


def main(directories: list[str]) -> int:
    """Check every wheel in the given directories and report the problems."""
    if not directories:
        logger.error("Usage: python check_wheel_metadata.py DIRECTORY [DIRECTORY ...]")
        return 2

    wheels = sorted(
        wheel for directory in directories for wheel in Path(directory).glob("*.whl")
    )
    if not wheels:
        logger.error("No wheel found in %s.", ", ".join(directories))
        return 1

    problems = [problem for wheel in wheels for problem in check(wheel)]
    for problem in problems:
        logger.error("%s", problem)
    if problems:
        return 1

    logger.info("The HTTP clients are optional extras in every wheel.")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    sys.exit(main(sys.argv[1:]))
