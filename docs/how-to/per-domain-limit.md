# How-To Apply Per-Domain Rate Limits

When scraping multiple domains, you often need to apply different rate limits
for each. This recipe shows how to configure domain-specific limits with a
fallback default.

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

Of course, you may even combine this with the [adaptive rate limiting
technique](./adapt-rate-limit.md).
