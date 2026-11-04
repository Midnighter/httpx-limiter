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

from collections.abc import Callable
from io import BytesIO

import anyio
import httpx
import pytest
from pytest_httpx import HTTPXMock

from httpx_limiter import AbstractAsyncLimiter, Rate
from httpx_limiter.aiolimiter import AiolimiterAsyncLimiter
from httpx_limiter.httpx import (
    AbstractRateLimiterRepository,
    AsyncMultiRateLimitedTransport,
    AsyncRateLimitedTransport,
)
from httpx_limiter.pyrate import PyrateAsyncLimiter


@pytest.mark.anyio
async def test_aiolimiter_init():
    """Test that an asynchronous limited transport can be initialized."""
    AsyncRateLimitedTransport(
        limiter=AiolimiterAsyncLimiter.create(Rate.create()),
        transport=httpx.AsyncHTTPTransport(),
    )


@pytest.mark.anyio
async def test_pyrate_init():
    """Test that an asynchronous limited transport can be initialized."""
    AsyncRateLimitedTransport(
        limiter=PyrateAsyncLimiter.create(Rate.create()),
        transport=httpx.AsyncHTTPTransport(),
    )


@pytest.mark.anyio
async def test_aiolimiter_create():
    """Test that an asynchronous rate-limited transport can be created."""
    transport = AsyncRateLimitedTransport.create(
        limiter=AiolimiterAsyncLimiter.create(Rate.create()),
    )

    assert isinstance(transport, AsyncRateLimitedTransport)


@pytest.mark.anyio
async def test_pyrate_create():
    """Test that an asynchronous rate-limited transport can be created."""
    transport = AsyncRateLimitedTransport.create(
        limiter=PyrateAsyncLimiter.create(Rate.create()),
    )

    assert isinstance(transport, AsyncRateLimitedTransport)


@pytest.mark.parametrize(
    ("limiter", "rate", "request_count", "min_elapsed", "max_elapsed"),
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
)
@pytest.mark.anyio
async def test_handle_async_request(  # noqa: PLR0913, PLR0917
    limiter: type[AbstractAsyncLimiter],
    rate: Rate,
    request_count: int,
    min_elapsed: float,
    max_elapsed: float,
    httpx_mock: HTTPXMock,
):
    """Test that handled requests are rate-limited."""
    httpx_mock.add_callback(
        lambda _: httpx.Response(status_code=200), is_reusable=True,
    )

    # We submit a fixed number of requests and measure how long they take to complete.
    # If rate limiting is working, requests beyond the burst capacity must wait for
    # tokens to replenish. We assert elapsed time falls within a generous range:
    # the lower bound proves rate limiting is active, and the upper bound guards
    # against unexpected hangs.
    async with httpx.AsyncClient(
        transport=AsyncRateLimitedTransport.create(limiter=limiter.create(rate)),
    ) as client:
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


class DisposableTransport(httpx.AsyncBaseTransport):
    """A test transport that owns a disposable resource."""

    def __init__(self) -> None:
        super().__init__()
        self.resource = BytesIO()

    async def handle_async_request(
        self,
        request: httpx.Request,  # noqa: ARG002
    ) -> httpx.Response:
        """Return a successful response without touching the network."""
        return httpx.Response(status_code=200)

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


class DefaultRepository(AbstractRateLimiterRepository):
    """A concrete repository that returns a single limiter for all requests."""

    def get_identifier(self, request: httpx.Request) -> str:  # noqa: ARG002
        """Return a fixed identifier for testing."""
        return "default"

    def create(self, request: httpx.Request) -> AbstractAsyncLimiter:  # noqa: ARG002
        """Return a rate limiter for testing."""
        return AiolimiterAsyncLimiter.create(Rate.create())


def make_single(
    inner: httpx.AsyncBaseTransport,
) -> httpx.AsyncBaseTransport:
    """Wrap the transport in a single rate-limited transport."""
    return AsyncRateLimitedTransport(
        limiter=AiolimiterAsyncLimiter.create(Rate.create()),
        transport=inner,
    )


def make_multi(
    inner: httpx.AsyncBaseTransport,
) -> httpx.AsyncBaseTransport:
    """Wrap the transport in a multiple rate-limited transport."""
    return AsyncMultiRateLimitedTransport(
        repository=DefaultRepository(),
        transport=inner,
    )


@pytest.mark.parametrize(
    "make_wrapper", [make_single, make_multi], ids=["single", "multi"],
)
@pytest.mark.anyio
async def test_explicit_aclose(
    make_wrapper: Callable[[httpx.AsyncBaseTransport], httpx.AsyncBaseTransport],
):
    """Test that explicitly closing the wrapper closes the underlying transport."""
    inner = DisposableTransport()
    wrapper = make_wrapper(inner)

    await wrapper.aclose()

    assert inner.resource.closed


@pytest.mark.parametrize(
    "make_wrapper", [make_single, make_multi], ids=["single", "multi"],
)
@pytest.mark.anyio
async def test_client_aclose(
    make_wrapper: Callable[[httpx.AsyncBaseTransport], httpx.AsyncBaseTransport],
):
    """Test that explicitly closing the client closes the underlying transport."""
    inner = DisposableTransport()
    client = httpx.AsyncClient(transport=make_wrapper(inner))

    await client.aclose()

    assert inner.resource.closed


@pytest.mark.parametrize(
    "make_wrapper", [make_single, make_multi], ids=["single", "multi"],
)
@pytest.mark.anyio
async def test_client_context_exit(
    make_wrapper: Callable[[httpx.AsyncBaseTransport], httpx.AsyncBaseTransport],
):
    """Test that leaving the client context closes the underlying transport."""
    inner = DisposableTransport()

    async with httpx.AsyncClient(transport=make_wrapper(inner)):
        assert not inner.resource.closed

    assert inner.resource.closed


@pytest.mark.parametrize(
    "make_wrapper", [make_single, make_multi], ids=["single", "multi"],
)
@pytest.mark.anyio
async def test_client_context_exit_on_exception(
    make_wrapper: Callable[[httpx.AsyncBaseTransport], httpx.AsyncBaseTransport],
):
    """Test that an exceptional client exit closes the transport and propagates."""
    inner = DisposableTransport()

    async def raise_inside_client() -> None:
        async with httpx.AsyncClient(transport=make_wrapper(inner)):
            msg = "boom"
            raise RuntimeError(msg)

    with pytest.raises(RuntimeError, match="boom"):
        await raise_inside_client()

    assert inner.resource.closed


@pytest.mark.parametrize(
    ("make_outer", "make_inner"),
    [(make_single, make_multi), (make_multi, make_single)],
    ids=["single-multi", "multi-single"],
)
@pytest.mark.anyio
async def test_nested_aclose(
    make_outer: Callable[[httpx.AsyncBaseTransport], httpx.AsyncBaseTransport],
    make_inner: Callable[[httpx.AsyncBaseTransport], httpx.AsyncBaseTransport],
):
    """Test that closing an outer wrapper reaches the innermost transport."""
    inner = DisposableTransport()
    outer = make_outer(make_inner(inner))

    await outer.aclose()

    assert inner.resource.closed


@pytest.mark.parametrize(
    "make_wrapper", [make_single, make_multi], ids=["single", "multi"],
)
@pytest.mark.anyio
async def test_aclose_error_propagation(
    make_wrapper: Callable[[httpx.AsyncBaseTransport], httpx.AsyncBaseTransport],
):
    """Test that an error in the underlying cleanup is propagated."""
    wrapper = make_wrapper(FailingTransport())

    with pytest.raises(RuntimeError, match="cleanup failed"):
        await wrapper.aclose()
