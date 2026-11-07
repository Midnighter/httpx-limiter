You can limit the number of requests made by an HTTPX or HTTPX2 client using the
transports provided in this package. That is useful in situations when you need to make
a large number of asynchronous requests against endpoints that implement a rate limit.

Every example below is shown for both HTTP clients. Pick the tab that matches the client you
installed. Transports, repositories, requests, and responses must all come from the
same client: `httpx_limiter.httpx` works with `httpx` and `httpx_limiter.httpx2` works
with `httpx2`.

### Single Rate Limit

The simplest use case is to apply a single rate limit to all requests. If you want to be
able to make twenty requests per second, for example, use the following code:

=== "HTTPX"

    ```python
    import httpx
    from httpx_limiter import Rate
    from httpx_limiter.httpx import AsyncRateLimitedTransport
    from httpx_limiter.pyrate import PyrateAsyncLimiter

    async def main():
        limiter = PyrateAsyncLimiter.create(Rate.create(magnitude=20))

        async with httpx.AsyncClient(
            transport=AsyncRateLimitedTransport.create(limiter=limiter),
        ) as client:
            response = await client.get("https://httpbin.org")
    ```

=== "HTTPX2"

    ```python
    import httpx2
    from httpx_limiter import Rate
    from httpx_limiter.httpx2 import AsyncRateLimitedTransport
    from httpx_limiter.pyrate import PyrateAsyncLimiter

    async def main():
        limiter = PyrateAsyncLimiter.create(Rate.create(magnitude=20))

        async with httpx2.AsyncClient(
            transport=AsyncRateLimitedTransport.create(limiter=limiter),
        ) as client:
            response = await client.get("https://httpbin.org")
    ```

!!! warning

    Due to limitations in the design of the underlying [leaky
    bucket](https://en.wikipedia.org/wiki/Leaky_bucket) implementation, which is used to
    implement the rate limiting, the magnitude of **the rate is also the maximum
    capacity of the bucket**. That means, if you **set a rate that is larger than one, a
    burst of requests equal to that capacity will be allowed**. If you do not want to
    allow any bursts, set the magnitude to one, but the duration to the inverse of your
    desired rate. If you want to allow twenty requests per second, for example, set the
    magnitude to 1 and the duration to 0.05 seconds.


    ```python
    from httpx_limiter import Rate

    Rate.create(magnitude=1, duration=1/20)
    ```

### Multiple Rate Limits

For more advanced use cases, you can apply different rate limits based on a concrete
implementation of the abstract `AbstractRateLimiterRepository` of your HTTP client,
[for HTTPX][httpx_limiter.httpx.AbstractRateLimiterRepository] or [for
HTTPX2][httpx_limiter.httpx2.AbstractRateLimiterRepository].
There are two relevant methods that both get passed the current request. One method
needs to identify which rate limit to apply, and the other method sets the rate limit
itself. See the following example:

=== "HTTPX"

    ```python
    import httpx
    from httpx_limiter import Rate
    from httpx_limiter.httpx import (
        AbstractRateLimiterRepository,
        AsyncMultiRateLimitedTransport,
    )
    from httpx_limiter.aiolimiter import AiolimiterAsyncLimiter


    class DomainBasedRateLimiterRepository(AbstractRateLimiterRepository):
        """Apply different rate limits based on the domain being requested."""

        def get_identifier(self, request: httpx.Request) -> str:
            """Return the domain as the identifier for rate limiting."""
            return request.url.host

        def create(self, request: httpx.Request) -> AiolimiterAsyncLimiter:
            """Create a rate limiter for the domain."""
            return AiolimiterAsyncLimiter.create(Rate.create(magnitude=25))


    async def main():
        async with httpx.AsyncClient(
            transport=AsyncMultiRateLimitedTransport.create(
                repository=DomainBasedRateLimiterRepository(),
            ),
        ) as client:
            response = await client.get("https://httpbin.org")
    ```

=== "HTTPX2"

    ```python
    import httpx2
    from httpx_limiter import Rate
    from httpx_limiter.httpx2 import (
        AbstractRateLimiterRepository,
        AsyncMultiRateLimitedTransport,
    )
    from httpx_limiter.aiolimiter import AiolimiterAsyncLimiter


    class DomainBasedRateLimiterRepository(AbstractRateLimiterRepository):
        """Apply different rate limits based on the domain being requested."""

        def get_identifier(self, request: httpx2.Request) -> str:
            """Return the domain as the identifier for rate limiting."""
            return request.url.host

        def create(self, request: httpx2.Request) -> AiolimiterAsyncLimiter:
            """Create a rate limiter for the domain."""
            return AiolimiterAsyncLimiter.create(Rate.create(magnitude=25))


    async def main():
        async with httpx2.AsyncClient(
            transport=AsyncMultiRateLimitedTransport.create(
                repository=DomainBasedRateLimiterRepository(),
            ),
        ) as client:
            response = await client.get("https://httpbin.org")
    ```

!!! tip

    You are free to ignore the request parameter and use global information like the
    time of day to determine the rate limit.

=== "HTTPX"

    ```python
    from datetime import datetime, timezone

    import httpx
    from httpx_limiter import Rate
    from httpx_limiter.httpx import (
        AbstractRateLimiterRepository,
        AsyncMultiRateLimitedTransport,
    )
    from httpx_limiter.pyrate import PyrateAsyncLimiter


    class DayNightRateLimiterRepository(AbstractRateLimiterRepository):
        """Apply different rate limits based on the time of day."""

        def get_identifier(self, request: httpx.Request) -> str:
            """Identify whether it is currently day or night."""
            if 6 <= datetime.now(tz=timezone.utc).hour < 18:
                return "day"

            return "night"

        def create(self, request: httpx.Request) -> PyrateAsyncLimiter:
            """Create a rate limiter based on the time of day."""
            if self.get_identifier(request) == "day":
                return PyrateAsyncLimiter.create(Rate.create(magnitude=10))

            return PyrateAsyncLimiter.create(Rate.create(magnitude=100))


    async def main():
        async with httpx.AsyncClient(
            transport=AsyncMultiRateLimitedTransport.create(
                repository=DayNightRateLimiterRepository(),
            ),
        ) as client:
            response = await client.get("https://httpbin.org")
    ```

=== "HTTPX2"

    ```python
    from datetime import datetime, timezone

    import httpx2
    from httpx_limiter import Rate
    from httpx_limiter.httpx2 import (
        AbstractRateLimiterRepository,
        AsyncMultiRateLimitedTransport,
    )
    from httpx_limiter.pyrate import PyrateAsyncLimiter


    class DayNightRateLimiterRepository(AbstractRateLimiterRepository):
        """Apply different rate limits based on the time of day."""

        def get_identifier(self, request: httpx2.Request) -> str:
            """Identify whether it is currently day or night."""
            if 6 <= datetime.now(tz=timezone.utc).hour < 18:
                return "day"

            return "night"

        def create(self, request: httpx2.Request) -> PyrateAsyncLimiter:
            """Create a rate limiter based on the time of day."""
            if self.get_identifier(request) == "day":
                return PyrateAsyncLimiter.create(Rate.create(magnitude=10))

            return PyrateAsyncLimiter.create(Rate.create(magnitude=100))


    async def main():
        async with httpx2.AsyncClient(
            transport=AsyncMultiRateLimitedTransport.create(
                repository=DayNightRateLimiterRepository(),
            ),
        ) as client:
            response = await client.get("https://httpbin.org")
    ```

### Transport Options

Both `AsyncRateLimitedTransport.create` and `AsyncMultiRateLimitedTransport.create`
forward additional keyword arguments to the `AsyncHTTPTransport` of the selected client.
The accepted keywords are described by the
[`HTTPXAsyncHTTPTransportKeywordArguments`][httpx_limiter.httpx.HTTPXAsyncHTTPTransportKeywordArguments]
type of `httpx_limiter.httpx` and the
[matching type][httpx_limiter.httpx2.HTTPXAsyncHTTPTransportKeywordArguments] of
`httpx_limiter.httpx2`. Types such as `Limits` and `Proxy` must come from the selected
client.

=== "HTTPX"

    ```python
    import httpx
    from httpx_limiter import Rate
    from httpx_limiter.aiolimiter import AiolimiterAsyncLimiter
    from httpx_limiter.httpx import AsyncRateLimitedTransport

    async def main():
        limiter = AiolimiterAsyncLimiter.create(Rate.create(magnitude=20))
        transport = AsyncRateLimitedTransport.create(
            limiter=limiter,
            limits=httpx.Limits(max_connections=10),
            retries=2,
        )
        async with httpx.AsyncClient(transport=transport) as client:
            response = await client.get("https://httpbin.org")
    ```

=== "HTTPX2"

    ```python
    import httpx2
    from httpx_limiter import Rate
    from httpx_limiter.aiolimiter import AiolimiterAsyncLimiter
    from httpx_limiter.httpx2 import AsyncRateLimitedTransport

    async def main():
        limiter = AiolimiterAsyncLimiter.create(Rate.create(magnitude=20))
        transport = AsyncRateLimitedTransport.create(
            limiter=limiter,
            limits=httpx2.Limits(max_connections=10),
            retries=2,
        )
        async with httpx2.AsyncClient(transport=transport) as client:
            response = await client.get("https://httpbin.org")
    ```

### Using Both Clients Together

You can install both extras, `httpx-limiter[httpx,httpx2]`, and use both integrations in
the same process. The limiters are independent of the HTTP client, so you may even share
one limiter between them. The HTTP objects, however, are **not interchangeable**: an
`httpx_limiter.httpx` transport cannot be used with an `httpx2.AsyncClient`, and a
repository for `httpx.Request` cannot serve `httpx2.Request` objects.

```python
import httpx
import httpx2
from httpx_limiter import Rate
from httpx_limiter.aiolimiter import AiolimiterAsyncLimiter
from httpx_limiter.httpx import AsyncRateLimitedTransport as HTTPXTransport
from httpx_limiter.httpx2 import AsyncRateLimitedTransport as HTTPX2Transport

async def main():
    limiter = AiolimiterAsyncLimiter.create(Rate.create(magnitude=20))

    async with (
        httpx.AsyncClient(transport=HTTPXTransport.create(limiter=limiter)) as old,
        httpx2.AsyncClient(transport=HTTPX2Transport.create(limiter=limiter)) as new,
    ):
        first = await old.get("https://httpbin.org")  # an httpx.Response
        second = await new.get("https://httpbin.org")  # an httpx2.Response
```
