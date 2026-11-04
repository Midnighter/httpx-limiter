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


"""Provide backend-neutral type definitions shared by the HTTP integrations."""

from typing import TypeAlias


# Fallback for Pyodide HTTPX. See: https://github.com/Midnighter/httpx-limiter/pull/10#issuecomment-3241566927
SocketOption: TypeAlias = (
    tuple[int, int, int]
    | tuple[int, int, bytes | bytearray]
    | tuple[int, int, None, int]
)

# We redefine the following type from the private types module of the HTTP clients to
# avoid a dependency on it. It is identical for HTTPX and HTTPX2.
CertTypes: TypeAlias = str | tuple[str, str] | tuple[str, str, str]
