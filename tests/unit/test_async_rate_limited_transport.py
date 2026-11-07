# Copyright (c) 2024 Moritz E. Beber
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


"""Test the expected functionality of the asynchronous rate-limited transport."""

from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING, Self

import anyio
import pytest

from httpx_limiter import AbstractAsyncLimiter, Rate
from httpx_limiter.aiolimiter import AiolimiterAsyncLimiter
from httpx_limiter.pyrate import PyrateAsyncLimiter


if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable
    from types import TracebackType

    from httpx_limiter_test_types import (
        AsyncBaseTransport,
        HTTPBackend,
        Request,
        Response,
    )


def make_mock_transport(http: HTTPBackend, status_code: int = 200, content: str = ""):
    """Return a mock transport of the selected backend that answers all requests."""
    return http.client.MockTransport(
        lambda _: http.client.Response(status_code=status_code, text=content),
    )


@pytest.mark.anyio
async def test_init(http: HTTPBackend, limiter_class: type[AbstractAsyncLimiter]):
    """Test that an asynchronous limited transport can be initialized."""
    transport = http.integration.AsyncRateLimitedTransport(
        limiter=limiter_class.create(Rate.create()),
        transport=make_mock_transport(http),
    )

    assert isinstance(transport, http.client.AsyncBaseTransport)


@pytest.mark.anyio
async def test_create(http: HTTPBackend, limiter_class: type[AbstractAsyncLimiter]):
    """Test that an asynchronous rate-limited transport can be created."""
    transport = http.integration.AsyncRateLimitedTransport.create(
        limiter=limiter_class.create(Rate.create()),
    )

    assert isinstance(transport, http.integration.AsyncRateLimitedTransport)
    assert isinstance(transport, http.client.AsyncBaseTransport)
    await transport.aclose()


@pytest.mark.anyio
async def test_single_response(
    http: HTTPBackend,
    limiter_class: type[AbstractAsyncLimiter],
):
    """Test that the single-rate transport returns the wrapped response."""
    transport = http.integration.AsyncRateLimitedTransport(
        limiter=limiter_class.create(Rate.create()),
        transport=make_mock_transport(http, status_code=201, content="created"),
    )

    async with http.client.AsyncClient(transport=transport) as client:
        response = await client.get("http://example.com")

    assert isinstance(response, http.client.Response)
    assert response.status_code == 201
    assert response.text == "created"


@pytest.mark.parametrize(
    ("limiter_class", "rate", "request_count", "min_elapsed", "max_elapsed"),
    [
        # Burst only: all requests fit in initial capacity → completes quickly.
        (AiolimiterAsyncLimiter, Rate.create(magnitude=2, duration=0.2), 2, 0.0, 0.15),
        (PyrateAsyncLimiter, Rate.create(magnitude=2, duration=0.2), 2, 0.0, 0.2),
        # Beyond burst: must wait for at least one refill cycle.
        (AiolimiterAsyncLimiter, Rate.create(magnitude=2, duration=0.2), 4, 0.15, 0.6),
        (PyrateAsyncLimiter, Rate.create(magnitude=2, duration=0.2), 4, 0.15, 0.8),
        # Well beyond burst: must wait for multiple refill cycles.
        (AiolimiterAsyncLimiter, Rate.create(magnitude=2, duration=0.2), 6, 0.3, 1.0),
        (PyrateAsyncLimiter, Rate.create(magnitude=2, duration=0.2), 6, 0.3, 1.2),
    ],
    ids=[
        "aiolimiter-burst",
        "pyrate-burst",
        "aiolimiter-beyond-burst",
        "pyrate-beyond-burst",
        "aiolimiter-well-beyond-burst",
        "pyrate-well-beyond-burst",
    ],
)
@pytest.mark.anyio
async def test_handle_async_request(  # noqa: PLR0913, PLR0917
    http: HTTPBackend,
    limiter_class: type[AbstractAsyncLimiter],
    rate: Rate,
    request_count: int,
    min_elapsed: float,
    max_elapsed: float,
):
    """Test that handled requests are rate-limited."""
    # We submit a fixed number of requests and measure how long they take to complete.
    # If rate limiting is working, requests beyond the burst capacity must wait for
    # tokens to replenish. We assert elapsed time falls within a generous range:
    # the lower bound proves rate limiting is active, and the upper bound guards
    # against unexpected hangs.
    transport = http.integration.AsyncRateLimitedTransport(
        limiter=limiter_class.create(rate),
        transport=make_mock_transport(http),
    )
    async with http.client.AsyncClient(transport=transport) as client:
        start = anyio.current_time()
        async with anyio.create_task_group() as tg:
            with anyio.fail_after(max_elapsed) as _scope:
                for _ in range(request_count):
                    tg.start_soon(client.get, "http://example.com")
                # For `fail_after` to work as expected, there needs to be at least one
                # async checkpoint to trigger a timeout.
                await anyio.lowlevel.checkpoint()
        elapsed = anyio.current_time() - start

    assert elapsed >= min_elapsed, (
        f"Expected at least {min_elapsed} s, got {elapsed:.3f} s"
    )
    assert elapsed < max_elapsed, (
        f"Expected less than {max_elapsed} s, got {elapsed:.3f} s"
    )


@pytest.mark.anyio
async def test_multi_selects_limiter_and_returns_response(
    http: HTTPBackend,
    limiter_class: type[AbstractAsyncLimiter],
):
    """Test that the multi-rate transport picks limiters per request."""
    created: list[str] = []

    class HostRepository(http.integration.AbstractRateLimiterRepository):
        """A repository with one limiter per host."""

        def get_identifier(self, request: Request) -> str:
            """Return the host."""
            return request.url.host

        def create(self, request: Request) -> AbstractAsyncLimiter:
            """Return a limiter that is slow only for the slow host."""
            created.append(request.url.host)
            if request.url.host == "slow.example.com":
                return limiter_class.create(Rate.create(magnitude=1, duration=0.3))

            return limiter_class.create(Rate.create(magnitude=100, duration=0.3))

    def handler(request: Request) -> Response:
        return http.client.Response(
            status_code=202 if request.url.host == "slow.example.com" else 200,
            text=request.url.host,
        )

    transport = http.integration.AsyncMultiRateLimitedTransport(
        repository=HostRepository(),
        transport=http.client.MockTransport(handler),
    )
    async with http.client.AsyncClient(transport=transport) as client:
        start = anyio.current_time()
        fast = [await client.get("http://fast.example.com") for _ in range(3)]
        fast_elapsed = anyio.current_time() - start
        slow = [await client.get("http://slow.example.com") for _ in range(2)]
        slow_elapsed = anyio.current_time() - start

    assert [r.status_code for r in fast] == [200] * 3
    assert {r.text for r in fast} == {"fast.example.com"}
    assert [r.status_code for r in slow] == [202] * 2
    assert {r.text for r in slow} == {"slow.example.com"}
    assert created == ["fast.example.com", "slow.example.com"]
    assert fast_elapsed < 0.2
    assert slow_elapsed - fast_elapsed >= 0.2


@pytest.mark.anyio
async def test_backends_coexist():
    """Test that both integrations work side by side with their own types."""
    import httpx  # noqa: PLC0415
    import httpx2  # noqa: PLC0415

    from httpx_limiter import httpx as httpx_integration  # noqa: PLC0415
    from httpx_limiter import httpx2 as httpx2_integration  # noqa: PLC0415

    httpx_transport = httpx_integration.AsyncRateLimitedTransport(
        limiter=AiolimiterAsyncLimiter.create(Rate.create()),
        transport=httpx.MockTransport(lambda _: httpx.Response(200, text="from httpx")),
    )
    httpx2_transport = httpx2_integration.AsyncRateLimitedTransport(
        limiter=PyrateAsyncLimiter.create(Rate.create()),
        transport=httpx2.MockTransport(
            lambda _: httpx2.Response(202, text="from httpx2"),
        ),
    )

    async with (
        httpx.AsyncClient(transport=httpx_transport) as first,
        httpx2.AsyncClient(transport=httpx2_transport) as second,
    ):
        first_response = await first.get("http://example.com")
        second_response = await second.get("http://example.com")

    assert type(first_response) is httpx.Response
    assert (first_response.status_code, first_response.text) == (200, "from httpx")
    assert type(second_response) is httpx2.Response
    assert (second_response.status_code, second_response.text) == (202, "from httpx2")
    assert not isinstance(httpx_transport, httpx2.AsyncBaseTransport)
    assert not isinstance(httpx2_transport, httpx.AsyncBaseTransport)


def make_transports(http: HTTPBackend) -> tuple[type, type]:
    """Return disposable and failing transport classes of the selected backend."""

    class DisposableTransport(http.client.AsyncBaseTransport):
        """A test transport that owns a disposable resource."""

        def __init__(self) -> None:
            super().__init__()
            self.resource = BytesIO()
            self.entered = False
            self.exited = False
            self.exc_type: type[BaseException] | None = None

        async def __aenter__(self) -> Self:
            """Record that the transport was entered."""
            self.entered = True
            return self

        async def __aexit__(
            self,
            exc_type: type[BaseException] | None = None,
            exc_value: BaseException | None = None,
            traceback: TracebackType | None = None,
        ) -> None:
            """Record that the transport was exited and with which exception."""
            self.exited = True
            self.exc_type = exc_type
            await super().__aexit__(exc_type, exc_value, traceback)

        async def handle_async_request(
            self,
            request: Request,  # noqa: ARG002
        ) -> Response:
            """Return a successful response without touching the network."""
            return http.client.Response(status_code=200)

        async def aclose(self) -> None:
            """Dispose of the owned resource."""
            await anyio.lowlevel.checkpoint()
            self.resource.close()

    class FailingTransport(DisposableTransport):
        """A test transport whose cleanup fails."""

        async def aclose(self) -> None:
            """Dispose of the owned resource, but fail in the process."""
            await super().aclose()
            msg = "cleanup failed"
            raise RuntimeError(msg)

    return DisposableTransport, FailingTransport


def make_wrappers(
    http: HTTPBackend,
) -> dict[str, Callable[[AsyncBaseTransport], AsyncBaseTransport]]:
    """Return functions that wrap a transport in each kind of rate-limited transport."""

    class DefaultRepository(http.integration.AbstractRateLimiterRepository):
        """A concrete repository that returns a single limiter for all requests."""

        def get_identifier(self, request: Request) -> str:  # noqa: ARG002
            """Return a fixed identifier for testing."""
            return "default"

        def create(self, request: Request) -> AbstractAsyncLimiter:  # noqa: ARG002
            """Return a rate limiter for testing."""
            return AiolimiterAsyncLimiter.create(Rate.create())

    def make_single(inner: AsyncBaseTransport) -> AsyncBaseTransport:
        """Wrap the transport in a single rate-limited transport."""
        return http.integration.AsyncRateLimitedTransport(
            limiter=AiolimiterAsyncLimiter.create(Rate.create()),
            transport=inner,
        )

    def make_multi(inner: AsyncBaseTransport) -> AsyncBaseTransport:
        """Wrap the transport in a multiple rate-limited transport."""
        return http.integration.AsyncMultiRateLimitedTransport(
            repository=DefaultRepository(),
            transport=inner,
        )

    return {"single": make_single, "multi": make_multi}


wrappers = pytest.mark.parametrize("kind", ["single", "multi"])


@wrappers
@pytest.mark.anyio
async def test_explicit_aclose(http: HTTPBackend, kind: str):
    """Test that explicitly closing the wrapper closes the underlying transport."""
    inner = make_transports(http)[0]()
    wrapper = make_wrappers(http)[kind](inner)

    await wrapper.aclose()

    assert inner.resource.closed


@wrappers
@pytest.mark.anyio
async def test_client_aclose(http: HTTPBackend, kind: str):
    """Test that explicitly closing the client closes the underlying transport."""
    inner = make_transports(http)[0]()
    client = http.client.AsyncClient(transport=make_wrappers(http)[kind](inner))

    await client.aclose()

    assert inner.resource.closed


@wrappers
@pytest.mark.anyio
async def test_client_context_exit(http: HTTPBackend, kind: str):
    """Test that the client context enters and exits the underlying transport."""
    inner = make_transports(http)[0]()

    async with http.client.AsyncClient(transport=make_wrappers(http)[kind](inner)):
        assert inner.entered
        assert not inner.resource.closed

    assert inner.exited
    assert inner.exc_type is None
    assert inner.resource.closed


@wrappers
@pytest.mark.anyio
async def test_client_context_exit_on_exception(http: HTTPBackend, kind: str):
    """Test that an exceptional client exit reaches the transport and propagates."""
    inner = make_transports(http)[0]()

    async def raise_inside_client() -> None:
        async with http.client.AsyncClient(
            transport=make_wrappers(http)[kind](inner),
        ):
            msg = "boom"
            raise RuntimeError(msg)

    with pytest.raises(RuntimeError, match="boom"):
        await raise_inside_client()

    assert inner.exited
    assert inner.exc_type is RuntimeError
    assert inner.resource.closed


@pytest.mark.parametrize(
    ("outer_kind", "inner_kind"),
    [("single", "multi"), ("multi", "single")],
    ids=["single-multi", "multi-single"],
)
@pytest.mark.anyio
async def test_nested_aclose(http: HTTPBackend, outer_kind: str, inner_kind: str):
    """Test that entering and exiting an outer wrapper reach the innermost one."""
    make = make_wrappers(http)
    inner = make_transports(http)[0]()
    outer = make[outer_kind](make[inner_kind](inner))

    async with outer:
        assert inner.entered

    assert inner.exited
    assert inner.exc_type is None
    assert inner.resource.closed


@wrappers
@pytest.mark.anyio
async def test_aclose_error_propagation(http: HTTPBackend, kind: str):
    """Test that an error in the underlying cleanup is propagated."""
    wrapper = make_wrappers(http)[kind](make_transports(http)[1]())

    with pytest.raises(RuntimeError, match="cleanup failed"):
        await wrapper.aclose()
