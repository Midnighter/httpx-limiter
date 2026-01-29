You can limit the number of requests made by an HTTPX client using the transports
provided in this package. That is useful in situations when you need to make a large
number of asynchronous requests against endpoints that implement a rate limit.

### Single Rate Limit

The simplest use case is to apply a single rate limit to all requests. If you want to be
able to make twenty requests per second, for example, use the following code:

```python
import httpx
from httpx_limiter import AsyncRateLimitedTransport, Rate
from httpx_limiter.pyrate import PyrateAsyncLimiter

async def main():
    limiter = PyrateAsyncLimiter.create(Rate.create(magnitude=20))
    async with httpx.AsyncClient(
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
implementation of the
[`AbstractRateLimiterRepository`][httpx_limiter.AbstractRateLimiterRepository]. There
are two relevant methods that both get passed the current request. One method needs to
identify which rate limit to apply, and the other method sets the rate limit itself. See
the following example:

```python
import httpx
from httpx_limiter import (
    AbstractRateLimiterRepository,
    AsyncMultiRateLimitedTransport,
    Rate
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


client = httpx.AsyncClient(
    transport=AsyncMultiRateLimitedTransport.create(
        repository=DomainBasedRateLimiterRepository(),
    ),
)
```

!!! tip

    You are free to ignore the request parameter and use global information like the
    time of day to determine the rate limit.

```python
from datetime import datetime, timezone

import httpx
from httpx_limiter import AbstractRateLimiterRepository, Rate
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
```
