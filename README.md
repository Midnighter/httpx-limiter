# HTTPX Limiter

| |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
|---|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Package | [![Latest PyPI Version](https://img.shields.io/pypi/v/httpx-limiter.svg)](https://pypi.org/project/httpx-limiter/) [![Supported Python Versions](https://img.shields.io/pypi/pyversions/httpx-limiter.svg)](https://pypi.org/project/httpx-limiter/) [![Documentation](https://readthedocs.org/projects/httpx-limiter/badge/?version=latest)](https://httpx-limiter.readthedocs.io/en/latest/?badge=latest)                                                                                                                                                                              |
| Meta | [![Apache-2.0](https://img.shields.io/pypi/l/httpx-limiter.svg)](LICENSE) [![Code of Conduct](https://img.shields.io/badge/Contributor%20Covenant-v2.0%20adopted-ff69b4.svg)](.github/CODE_OF_CONDUCT.md) [![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/) [![Code Style Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black) [![Linting: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) |
| Automation |                                                                                                                                                                                                                                                                                                                                                                                                                                       |

_A lightweight package that provides rate-limited httpx transports._

## Installation

The package is published on [PyPI](https://pypi.org/project/httpx-limiter/).
Install it, for example, with

```sh
pip install httpx-limiter
```

## Tutorial

You can limit the number of requests made by an HTTPX client using the transports
provided in this package. That is useful in situations when you need to make a large
number of asynchronous requests against endpoints that implement a rate limit,

### Single Rate Limit

The simplest use case is to apply a single rate limit to all requests. If you want to be
able to make twenty requests per second, for example, use the following code:

```python
import httpx
from httpx_limiter import AsyncRateLimitedTransport, Rate

async def main():
    async with httpx.AsyncClient(
        transport=AsyncRateLimitedTransport.create(rate=Rate.create(magnitude=20)),
    ) as client:
        response = await client.get("https://httpbin.org")
```

> [!IMPORTANT]
> Due to limitations in the design of the underlying leaky bucket implementation,
> which is used to implement the rate limiting, the magnitude of the rate is also the
> maximum capacity of the bucket. That means, if you set a rate that is larger than one,
> a burst of requests equal to that capacity will be allowed. If you do not want to
> allow any bursts, set the magnitude to one, but the duration to the inverse of your
> desired rate. If you want to allow twenty requests per second, for example, set the
> magnitude to 1 and the duration to 0.05 seconds.

### Multiple Rate Limits

For more advanced use cases, you can apply different rate limits based on a concrete
implementation of the `AbstractRateLimiterRepository`. There are two relevant methods
that both get passed the current request. One method needs to identify which rate limit
to apply, and the other method sets the rate limit itself. See the following example:

```python
import httpx
from httpx_limiter import AbstractRateLimiterRepository, AsyncMultiRateLimitedTransport, Rate

class DomainBasedRateLimiterRepository(AbstractRateLimiterRepository):
    """Apply different rate limits based on the domain being requested."""
    
    def get_identifier(self, request: httpx.Request) -> str:
        """Return the domain as the identifier for rate limiting."""
        return request.url.host
    
    def get_rate(self, request: httpx.Request) -> Rate:
        """Apply the same, but independent rate limit to each domain."""
        return Rate.create(magnitude=25)

client = httpx.AsyncClient(
    transport=AsyncMultiRateLimitedTransport.create(
        repository=DomainBasedRateLimiterRepository(),
    ),
)
```

> [!NOTE]
> You are free to ignore the request argument and use global information like the time
> of day to determine the rate limit.

```python
from datetime import datetime, timezone

import httpx
from httpx_limiter import AbstractRateLimiterRepository, AsyncMultiRateLimitedTransport, Rate

class DayNightRateLimiterRepository(AbstractRateLimiterRepository):
    """Apply different rate limits based on the time of day."""

    def get_identifier(self, _: httpx.Request) -> str:
        """Identify whether it is currently day or night."""
        if 6 <= datetime.now(tz=timezone.utc).hour < 18:
            return "day"
        
        return "night"

    def get_rate(self, _: httpx.Request) -> Rate:
        """Apply different rate limits during the day or night."""
        if self.get_identifier(_) == "day":
            return Rate.create(magnitude=10)
        
        return Rate.create(magnitude=100)
```

## Copyright

- Copyright © 2024,2025 Moritz E. Beber.
- Free software distributed under the [Apache Software License 2.0](./LICENSE).
