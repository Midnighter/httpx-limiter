# HTTPX Limiter

|            |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Package    | [![Latest PyPI Version](https://img.shields.io/pypi/v/httpx-limiter.svg)](https://pypi.org/project/httpx-limiter/) [![Supported Python Versions](https://img.shields.io/pypi/pyversions/httpx-limiter.svg)](https://pypi.org/project/httpx-limiter/)                                                                                                                                                                                                                                                                                                                                                 |
| Meta       | [![Apache-2.0](https://img.shields.io/pypi/l/httpx-limiter.svg)](LICENSE) [![Code of Conduct](https://img.shields.io/badge/Contributor%20Covenant-v2.0%20adopted-ff69b4.svg)](.github/CODE_OF_CONDUCT.md) [![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/) [![Code Style Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black) [![Linting: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) |
| Automation | [![CI](https://github.com/Midnighter/httpx-limiter/actions/workflows/main.yml/badge.svg)](https://github.com/Midnighter/httpx-limiter/actions/workflows/main.yml)                                                                                                                                                                                                                                                                                                                                                                                                                                    |

_A lightweight package that provides rate-limited httpx transports._

## Installation

The package is published on [PyPI](https://pypi.org/project/httpx-limiter/). Install it,
for example, with the aiolimiter backend.

```sh
pip install 'httpx-limiter[aiolimiter]'
```

There is also a pyrate-limiter backend available.

```sh
pip install 'httpx-limiter[pyrate]'
```

## Rate Limiter Backends

This package provides two different asynchronous rate limiter implementations to choose
from:

1. [aiolimiter](https://aiolimiter.readthedocs.io)
2. [pyrate-limiter](https://pyratelimiter.readthedocs.io)

> [!IMPORTANT]
> While both implementations fulfill similar purposes, there are significant differences
> between them. Please read the descriptions below to make an informed decision about
> which one best suits your needs.

### 1. aiolimiter

-   **Single rate limit only**: Supports only one rate limit at a time
-   **Lightweight**: Minimal dependencies and simpler configuration
-   **Linear token refresh rate**: As an example, if you set a rate of 2 per second,
    roughly one token will be added every 500 milliseconds

```python
from httpx_limiter.aiolimiter import AiolimiterAsyncLimiter

limiter = AiolimiterAsyncLimiter.create(Rate.create(magnitude=20))
```

### 2. pyrate-limiter

-   **Multiple rate limits**: Support for multiple concurrent rate limits, for example,
    10 requests per second _and_ 100 requests per minute
-   **Flexible configuration**: Comprehensive configuration options
-   **Multiprocessing dependency**: Current implementation depends on `multiprocessing`
    which may not be available in all environments, such as pyodide
-   **Stepwise token refresh rate**: As an example, if you set a rate of 2 per second,
    two token will be added every second

```python
from httpx_limiter.pyrate import PyrateAsyncLimiter

# Single rate limit
limiter = PyrateAsyncLimiter.create(Rate.create(magnitude=20))

# Multiple rate limits
limiter = PyrateAsyncLimiter.create(
    Rate.create(magnitude=10),  # 10 per second
    Rate.create(magnitude=100, duration=60),  # 100 per minute
)
```

## Tutorial

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

> [!IMPORTANT]
> Due to limitations in the design of the underlying [leaky
> bucket](https://en.wikipedia.org/wiki/Leaky_bucket) implementation, which is
> used to implement the rate limiting, the magnitude of the rate is also the
> maximum capacity of the bucket. That means, if you set a rate that is larger
> than one, a burst of requests equal to that capacity will be allowed. If you
> do not want to allow any bursts, set the magnitude to one, but the duration to
> the inverse of your desired rate. If you want to allow twenty requests per
> second, for example, set the magnitude to 1 and the duration to 0.05 seconds.
>
> ```python
> Rate.create(magnitude=1, duration=1/20)
> ```

### Multiple Rate Limits

For more advanced use cases, you can apply different rate limits based on a concrete
implementation of the `AbstractRateLimiterRepository`. There are two relevant methods
that both get passed the current request. One method needs to return an identifier for
which rate limiter to choose, and the other method creates a rate limiter. See the
following example:

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

> [!TIP]
> You are free to ignore the request parameter and use global information like
> the time of day to determine the rate limit.

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

## Copyright

-   Copyright © 2024, 2025 Moritz E. Beber.
-   Free software distributed under the [Apache Software License 2.0](./LICENSE).
