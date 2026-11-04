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


"""Provide additional type definitions."""

import ssl
from collections.abc import Iterable
from typing import TypeAlias, TypedDict

import httpx


# Fallback for Pyodide HTTPX. See: https://github.com/Midnighter/httpx-limiter/pull/10#issuecomment-3241566927
SocketOption: TypeAlias = (
    tuple[int, int, int]
    | tuple[int, int, bytes | bytearray]
    | tuple[int, int, None, int]
)

# We redefine the following types from httpx._types to avoid a dependency on the
# private module. It would be better if HTTPX exposed these types publicly, but
# they are unlikely to change often. Thus we consider it acceptable to redefine
# them here for type hinting purposes.
CertTypes: TypeAlias = str | tuple[str, str] | tuple[str, str, str]
ProxyTypes: TypeAlias = httpx.URL | str | httpx.Proxy


class HTTPXAsyncHTTPTransportKeywordArguments(TypedDict, total=False):
    """Keyword arguments for the httpx.AsyncHTTPTransport constructor."""

    verify: ssl.SSLContext | str | bool
    cert: CertTypes | None
    trust_env: bool
    http1: bool
    http2: bool
    limits: httpx.Limits
    proxy: ProxyTypes | None
    uds: str | None
    local_address: str | None
    retries: int
    socket_options: Iterable[SocketOption] | None
