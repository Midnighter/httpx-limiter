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

"""

from pathlib import Path

import pytest
from mktestdocs import check_md_file


ROOT_DIR = Path(__file__).parents[2]
DOCS = [*(ROOT_DIR / "docs").glob("**/*.md"), ROOT_DIR / "README.md"]


@pytest.mark.parametrize("document", DOCS, ids=str)
def test_document_examples_independently(document: Path):
    """
    Test the code examples in an individual document.

    Each code block must be completely independent of each other, for example, imports
    must be restated within each block.

    """
    check_md_file(fpath=document)
