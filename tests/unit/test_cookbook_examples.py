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


"""
Test cookbook examples.

These tests verify that the code patterns documented in docs/cookbook.md
work correctly. They use mocked HTTP responses to avoid network dependencies.
"""

import httpx
import pytest
from httpx_tenacity import AsyncTenaciousTransport
from pytest_httpx import HTTPXMock
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from httpx_limiter import (
    AbstractRateLimiterRepository,
    AsyncMultiRateLimitedTransport,
    AsyncRateLimitedTransport,
    Rate,
)
from httpx_limiter.aiolimiter import AiolimiterAsyncLimiter
from httpx_limiter.pyrate import PyrateAsyncLimiter


class TestHttpxTenacityStandalone:
    """Test httpx-tenacity for standalone retry needs."""

    @pytest.mark.anyio
    async def test_successful_request(self, httpx_mock: HTTPXMock):
        """Test that a successful request returns normally."""
        httpx_mock.add_response(json={"status": "ok"})

        transport = AsyncTenaciousTransport.create()

        async with httpx.AsyncClient(transport=transport) as client:
            response = await client.get("https://api.example.com/data")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    @pytest.mark.anyio
    async def test_retries_on_transient_error(self, httpx_mock: HTTPXMock):
        """Test that transient errors trigger retries."""
        httpx_mock.add_response(status_code=503)
        httpx_mock.add_response(status_code=503)
        httpx_mock.add_response(json={"status": "ok"})

        transport = AsyncTenaciousTransport.create(
            min_wait_seconds=0.01,
            max_wait_seconds=0.1,
        )

        async with httpx.AsyncClient(transport=transport) as client:
            response = await client.get("https://api.example.com/data")

        assert response.status_code == 200


class TestCombinedRateLimitingWithRetries:
    """Test combining httpx-limiter with tenacity decorators."""

    @pytest.mark.anyio
    async def test_successful_request(self, httpx_mock: HTTPXMock):
        """Test that a successful request returns normally."""
        httpx_mock.add_response(json={"status": "ok"})

        limiter = AiolimiterAsyncLimiter.create(Rate.create(magnitude=10))
        transport = AsyncRateLimitedTransport.create(limiter=limiter)

        @retry(
            stop=stop_after_attempt(5),
            wait=wait_exponential(multiplier=1, min=0.1, max=1),
            retry=retry_if_exception_type(httpx.HTTPStatusError),
        )
        async def fetch_url(client: httpx.AsyncClient, url: str) -> httpx.Response:
            response = await client.get(url)
            response.raise_for_status()
            return response

        async with httpx.AsyncClient(transport=transport) as client:
            response = await fetch_url(client, "https://api.example.com/data")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    @pytest.mark.anyio
    async def test_retries_on_error(self, httpx_mock: HTTPXMock):
        """Test that errors trigger retries."""
        httpx_mock.add_response(status_code=500)
        httpx_mock.add_response(status_code=500)
        httpx_mock.add_response(json={"status": "ok"})

        limiter = AiolimiterAsyncLimiter.create(Rate.create(magnitude=10))
        transport = AsyncRateLimitedTransport.create(limiter=limiter)

        @retry(
            stop=stop_after_attempt(5),
            wait=wait_exponential(multiplier=0.01, min=0.01, max=0.1),
            retry=retry_if_exception_type(httpx.HTTPStatusError),
        )
        async def fetch_url(client: httpx.AsyncClient, url: str) -> httpx.Response:
            response = await client.get(url)
            response.raise_for_status()
            return response

        async with httpx.AsyncClient(transport=transport) as client:
            response = await fetch_url(client, "https://api.example.com/data")

        assert response.status_code == 200


class TestAdaptiveRateLimiting:
    """Test the adaptive rate limiting pattern from the cookbook."""

    @pytest.mark.anyio
    async def test_adaptive_repository_updates_rate(self, httpx_mock: HTTPXMock):
        """Test that the adaptive repository can update its rate."""
        httpx_mock.add_response(
            headers={"X-RateLimit-Remaining": "5"},
            json={"status": "ok"},
        )

        class AdaptiveRepository(AbstractRateLimiterRepository):
            """Adjust rate limiting based on server feedback headers."""

            def __init__(self) -> None:
                super().__init__()
                self._current_magnitude = 5

            def get_identifier(self, request: httpx.Request) -> str:  # noqa: ARG002
                return "global"

            def create(self, request: httpx.Request) -> AiolimiterAsyncLimiter:  # noqa: ARG002
                return AiolimiterAsyncLimiter.create(
                    Rate.create(magnitude=self._current_magnitude),
                )

            def update_from_header(self, remaining: int) -> None:
                new_magnitude = 1 if remaining < 10 else 5
                if new_magnitude != self._current_magnitude:
                    self._current_magnitude = new_magnitude
                    self._limiters.clear()

        repo = AdaptiveRepository()

        async def rate_limit_hook(response: httpx.Response) -> None:
            remaining = response.headers.get("X-RateLimit-Remaining")
            if remaining:
                repo.update_from_header(int(remaining))

        transport = AsyncMultiRateLimitedTransport.create(repository=repo)

        event_hooks: dict[str, list] = {"response": [rate_limit_hook]}
        async with httpx.AsyncClient(
            transport=transport,
            event_hooks=event_hooks,
        ) as client:
            await client.get("https://api.github.com/users/octocat")

        assert repo._current_magnitude == 1  # noqa: SLF001

    @pytest.mark.anyio
    async def test_adaptive_repository_maintains_rate(self, httpx_mock: HTTPXMock):
        """Test that the rate is maintained when remaining is high."""
        httpx_mock.add_response(
            headers={"X-RateLimit-Remaining": "50"},
            json={"status": "ok"},
        )

        class AdaptiveRepository(AbstractRateLimiterRepository):
            """Adjust rate limiting based on server feedback headers."""

            def __init__(self) -> None:
                super().__init__()
                self._current_magnitude = 5

            def get_identifier(self, request: httpx.Request) -> str:  # noqa: ARG002
                return "global"

            def create(self, request: httpx.Request) -> AiolimiterAsyncLimiter:  # noqa: ARG002
                return AiolimiterAsyncLimiter.create(
                    Rate.create(magnitude=self._current_magnitude),
                )

            def update_from_header(self, remaining: int) -> None:
                new_magnitude = 1 if remaining < 10 else 5
                if new_magnitude != self._current_magnitude:
                    self._current_magnitude = new_magnitude
                    self._limiters.clear()

        repo = AdaptiveRepository()

        async def rate_limit_hook(response: httpx.Response) -> None:
            remaining = response.headers.get("X-RateLimit-Remaining")
            if remaining:
                repo.update_from_header(int(remaining))

        transport = AsyncMultiRateLimitedTransport.create(repository=repo)

        event_hooks: dict[str, list] = {"response": [rate_limit_hook]}
        async with httpx.AsyncClient(
            transport=transport,
            event_hooks=event_hooks,
        ) as client:
            await client.get("https://api.github.com/users/octocat")

        assert repo._current_magnitude == 5  # noqa: SLF001


class TestPerDomainRateLimiting:
    """Test the per-domain rate limiting pattern from the cookbook."""

    @pytest.mark.anyio
    async def test_per_domain_repository_uses_correct_rates(
        self,
        httpx_mock: HTTPXMock,
    ):
        """Test that different domains get different rate limiters."""
        httpx_mock.add_response(url="https://api.github.com/users/octocat")
        httpx_mock.add_response(url="https://api.twitter.com/2/users/me")
        httpx_mock.add_response(url="https://other-api.example.com/data")

        domain_rates: dict[str, Rate] = {
            "api.github.com": Rate.create(magnitude=30),
            "api.twitter.com": Rate.create(magnitude=15),
        }
        default_rate = Rate.create(magnitude=5)

        class PerDomainRepository(AbstractRateLimiterRepository):
            """Apply preconfigured rate limits per domain."""

            def get_identifier(self, request: httpx.Request) -> str:
                return str(request.url.host)

            def create(self, request: httpx.Request) -> PyrateAsyncLimiter:
                host = str(request.url.host)
                rate = domain_rates.get(host, default_rate)
                return PyrateAsyncLimiter.create(rate)

        repo = PerDomainRepository()
        transport = AsyncMultiRateLimitedTransport.create(repository=repo)

        async with httpx.AsyncClient(transport=transport) as client:
            await client.get("https://api.github.com/users/octocat")
            await client.get("https://api.twitter.com/2/users/me")
            await client.get("https://other-api.example.com/data")

        assert "api.github.com" in repo._limiters  # noqa: SLF001
        assert "api.twitter.com" in repo._limiters  # noqa: SLF001
        assert "other-api.example.com" in repo._limiters  # noqa: SLF001
        assert len(repo._limiters) == 3  # noqa: SLF001
