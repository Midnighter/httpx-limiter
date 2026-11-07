# HTTPX Limiter

A lightweight package that provides rate-limited httpx and httpx2 transports.

## Installation

The package is published on [PyPI](https://pypi.org/project/httpx-limiter/). Plain
`pip install httpx-limiter` installs only the shared core, which contains no HTTP
client. Select the HTTP client you use with an extra, `httpx` or `httpx2`, and normally
also a rate limiter backend, `aiolimiter` or `pyrate`.

```sh
pip install 'httpx-limiter[httpx,aiolimiter]'
pip install 'httpx-limiter[httpx2,pyrate]'
```

To use both HTTP clients in the same process, install both extras.

```sh
pip install 'httpx-limiter[httpx,httpx2,aiolimiter]'
```

There is no automatic fallback: you choose the integration explicitly by importing from
`httpx_limiter.httpx` or from `httpx_limiter.httpx2`.

### Migrating from <0.7

The HTTP-specific classes moved out of the package root and `httpx` is no longer a
required dependency. Install `httpx-limiter[httpx]` instead of `httpx-limiter` and
change your imports. `Rate`, `AbstractAsyncLimiter`, and the limiter implementations
keep their import paths.

```diff
-from httpx_limiter import AsyncRateLimitedTransport, Rate
+from httpx_limiter import Rate
+from httpx_limiter.httpx import AsyncRateLimitedTransport
```

The same applies to `AsyncMultiRateLimitedTransport`, `AbstractRateLimiterRepository`,
and `HTTPXAsyncHTTPTransportKeywordArguments`. For HTTPX2, import them from
`httpx_limiter.httpx2` instead.

## Rate Limiter Backends

This package provides two different asynchronous rate limiter implementations to choose
from:

1. [aiolimiter](https://aiolimiter.readthedocs.io)
2. [pyrate-limiter](https://pyratelimiter.readthedocs.io)

!!! warning

    While both implementations fulfill similar purposes, there are significant
    differences between them. Please read the descriptions below to make an informed
    decision about which one best suits your needs.

### 1. aiolimiter

-   **Single rate limit only**: Supports only one rate limit at a time
-   **Lightweight**: Minimal dependencies and simpler configuration
-   **Linear token refresh rate**: As an example, if you set a rate of 2 per second,
    roughly one token will be added every 500 milliseconds

```python
from httpx_limiter import Rate
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
from httpx_limiter import Rate
from httpx_limiter.pyrate import PyrateAsyncLimiter

async def main():
    # Single rate limit
    limiter = PyrateAsyncLimiter.create(Rate.create(magnitude=20))

    # Multiple rate limits
    limiter = PyrateAsyncLimiter.create(
        Rate.create(magnitude=10),  # 10 per second
        Rate.create(magnitude=100, duration=60),  # 100 per minute
    )
```

## Copyright

-   Copyright © 2024, 2025 Moritz E. Beber.
-   Free software distributed under the [Apache Software License
    2.0](https://www.apache.org/licenses/LICENSE-2.0.html).
