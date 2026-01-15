# Cookbook

This cookbook provides advanced patterns and real-world recipes for building robust
production scrapers and clients with `httpx-limiter`.

## Combining Rate Limiting with Automatic Retries

Even with a rate limiter, you may occasionally receive `429 Too Many Requests` errors if
the server's capacity fluctuates or if you have multiple clients running.

A local rate limiter is your "first line of defense," but it cannot guarantee you won't
hit a server-side limit. The solution is to combine rate limiting with automatic retries.

### Using httpx-tenacity (Recommended for Simple Cases)

For simple retry needs without rate limiting, use
[httpx-tenacity](https://midnighter.github.io/httpx-tenacity/) which provides a clean
transport-based approach:

```python
import httpx
from httpx_tenacity import AsyncTenaciousTransport


async def main() -> None:
    transport = AsyncTenaciousTransport.create(
        max_attempts=5,
        min_wait_seconds=0.1,
        max_wait_seconds=60,
    )
    async with httpx.AsyncClient(transport=transport) as client:
        response = await client.get("https://api.example.com/data")
        print(response.json())
```

### Combining Rate Limiting with Retries

When you need both rate limiting and retries, use `httpx-limiter` for the transport
and wrap your request logic with retry decorators using
[tenacity](https://pypi.org/project/tenacity/):

```python
import httpx
from httpx_limiter import AsyncRateLimitedTransport, Rate
from httpx_limiter.aiolimiter import AiolimiterAsyncLimiter
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


limiter = AiolimiterAsyncLimiter.create(Rate.create(magnitude=10))
transport = AsyncRateLimitedTransport.create(limiter=limiter)


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(httpx.HTTPStatusError),
)
async def fetch_url(client: httpx.AsyncClient, url: str) -> httpx.Response:
    response = await client.get(url)
    response.raise_for_status()
    return response


async def main() -> None:
    async with httpx.AsyncClient(transport=transport) as client:
        try:
            response = await fetch_url(client, "https://api.example.com/data")
            print(response.json())
        except httpx.HTTPStatusError as exc:
            print(f"Failed after retries: {exc}")
```

---

## Adaptive Rate Limiting (Header Feedback)

If an API provides rate limit headers like `X-RateLimit-Remaining`, you can use a custom
repository to dynamically adjust your client's behavior.

This demonstrates the flexibility of the project's repository pattern by creating a
repository that can be updated based on server feedback.

!!! warning

    This pattern maintains a single "global" rate limiter that gets replaced when the
    rate needs to change. This works well for single-endpoint scenarios. For multiple
    endpoints with different limits, consider storing rates per-identifier.

```python
import httpx
from httpx_limiter import (
    AbstractRateLimiterRepository,
    AsyncMultiRateLimitedTransport,
    Rate,
)
from httpx_limiter.aiolimiter import AiolimiterAsyncLimiter


class AdaptiveRepository(AbstractRateLimiterRepository):
    """Adjust rate limiting based on server feedback headers."""

    def __init__(self) -> None:
        super().__init__()
        self._current_magnitude = 5

    def get_identifier(self, request: httpx.Request) -> str:
        return "global"

    def create(self, request: httpx.Request) -> AiolimiterAsyncLimiter:
        return AiolimiterAsyncLimiter.create(
            Rate.create(magnitude=self._current_magnitude)
        )

    def update_from_header(self, remaining: int) -> None:
        """Adjust rate based on server feedback."""
        new_magnitude = 1 if remaining < 10 else 5

        if new_magnitude != self._current_magnitude:
            self._current_magnitude = new_magnitude
            self._limiters.clear()


repo = AdaptiveRepository()


async def rate_limit_hook(response: httpx.Response) -> None:
    """Inspect headers and update the limiter."""
    remaining = response.headers.get("X-RateLimit-Remaining")
    if remaining:
        repo.update_from_header(int(remaining))


transport = AsyncMultiRateLimitedTransport.create(repository=repo)


async def main() -> None:
    event_hooks = {"response": [rate_limit_hook]}
    async with httpx.AsyncClient(
        transport=transport,
        event_hooks=event_hooks,
    ) as client:
        response = await client.get("https://api.github.com/users/octocat")
        print(response.json())
```

---

## Per-Domain Rate Limiting with Sensible Defaults

When scraping multiple domains, you often need different rate limits for each. This
recipe shows how to configure domain-specific limits with a fallback default.

```python
import httpx
from httpx_limiter import (
    AbstractRateLimiterRepository,
    AsyncMultiRateLimitedTransport,
    Rate,
)
from httpx_limiter.pyrate import PyrateAsyncLimiter


DOMAIN_RATES: dict[str, Rate] = {
    "api.github.com": Rate.create(magnitude=30),
    "api.twitter.com": Rate.create(magnitude=15),
}
DEFAULT_RATE = Rate.create(magnitude=5)


class PerDomainRepository(AbstractRateLimiterRepository):
    """Apply preconfigured rate limits per domain."""

    def get_identifier(self, request: httpx.Request) -> str:
        return str(request.url.host)

    def create(self, request: httpx.Request) -> PyrateAsyncLimiter:
        host = str(request.url.host)
        rate = DOMAIN_RATES.get(host, DEFAULT_RATE)
        return PyrateAsyncLimiter.create(rate)


async def main() -> None:
    transport = AsyncMultiRateLimitedTransport.create(
        repository=PerDomainRepository(),
    )
    async with httpx.AsyncClient(transport=transport) as client:
        await client.get("https://api.github.com/users/octocat")
        await client.get("https://api.twitter.com/2/users/me")
        await client.get("https://other-api.example.com/data")
```
