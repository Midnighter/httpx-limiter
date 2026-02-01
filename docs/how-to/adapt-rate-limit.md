# How-To Dynamically Adjust The Rate Limit?

If a server responds with rate limit headers, like `X-RateLimit-Remaining`, you
can use a custom repository to dynamically adjust your client's behavior. This
demonstrates the flexibility of the project's repository pattern by creating a
repository that can be updated based on server feedback.

!!! warning

    This pattern maintains a single _global_ rate limiter that gets replaced
    when the rate needs to change. This works well for single domain or endpoint
    scenarios. For multiple endpoints with different limits, consider storing
    rates per identifier.

```python
import httpx
from httpx_limiter import (
    AbstractRateLimiterRepository,
    AsyncMultiRateLimitedTransport,
    Rate,
)
from httpx_limiter.aiolimiter import AiolimiterAsyncLimiter


class AdaptiveRepository(AbstractRateLimiterRepository):
    """Adjust rate limiting based on server response headers."""

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




async def rate_limit_hook(response: httpx.Response) -> None:
    """Inspect headers and update the limiter."""
    remaining = response.headers.get("X-RateLimit-Remaining")
    if remaining:
        repo.update_from_header(int(remaining))




async def main() -> None:
    repo = AdaptiveRepository()
    event_hooks = {"response": [rate_limit_hook]}

    async with httpx.AsyncClient(
        transport=AsyncMultiRateLimitedTransport.create(repository=repo),
        event_hooks=event_hooks,
    ) as client:
        response = await client.get("https://api.github.com/users/octocat")
        print(response.json())
```

This is a fairly basic example. For real scenarios, you likely want to implement
a global lock in the `update_from_header` method to avoid race conditions when
updating the rate from multiple concurrent requests.
