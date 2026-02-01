# How-To Combine Rate Limiting with Automatic Retries?

Even with a rate limiter, you may occasionally receive [`429 Too Many
Requests`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/429)
HTTP errors if the server's capacity fluctuates or if you have multiple clients
running. A local rate limiter is your _first line of defense_, but it cannot
guarantee that you won't reach a server-side limit. The solution is to combine
rate limiting with automatic retries.

When you combine both techniques, it makes sense for the inner layer to be the
rate limiter, while the outer layer handles retries. This way, each retry
attempt is also subject to rate limiting.

## Using `httpx-tenacity`

For this example, we use the companion package
[httpx-tenacity](https://midnighter.github.io/httpx-tenacity/) which provides a
clean HTTPX transport-based approach to retrying. It also comes with sensible
defaults that retry on server-side errors.

```python
import httpx
from httpx_limiter import AsyncRateLimitedTransport, Rate
from httpx_limiter.aiolimiter import AiolimiterAsyncLimiter
from httpx_tenacity import AsyncTenaciousTransport


async def main() -> None:
    retry = AsyncTenaciousTransport.create(
        max_attempts=3,
        min_wait_seconds=0.1,
        max_wait_seconds=0.5,
    )
    retry.transport = AsyncRateLimitedTransport.create(
        limiter=AiolimiterAsyncLimiter.create(Rate.create(magnitude=10))
    )
    async with httpx.AsyncClient(transport=retry) as client:
        response = await client.get("https://api.example.com/data")
        print(response.json())
```
