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


"""Provide additional type definitions for the HTTPX2 integration."""

import ssl
from collections.abc import Iterable
from typing import TypeAlias, TypedDict

import httpx2

from httpx_limiter._types import CertTypes, SocketOption


ProxyTypes: TypeAlias = httpx2.URL | str | httpx2.Proxy


class HTTPXAsyncHTTPTransportKeywordArguments(TypedDict, total=False):
    """Keyword arguments for the httpx2.AsyncHTTPTransport constructor."""

    verify: ssl.SSLContext | str | bool
    cert: CertTypes | None
    trust_env: bool
    http1: bool
    http2: bool
    limits: httpx2.Limits
    proxy: ProxyTypes | None
    uds: str | None
    local_address: str | None
    retries: int
    socket_options: Iterable[SocketOption] | None
