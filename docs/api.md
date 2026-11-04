The following classes are exposed to the user:

* [`Rate`][httpx_limiter.Rate]
* [`AbstractAsyncLimiter`][httpx_limiter.AbstractAsyncLimiter]
* [`AsyncRateLimitedTransport`][httpx_limiter.httpx.AsyncRateLimitedTransport]
* [`AbstractRateLimiterRepository`][httpx_limiter.httpx.AbstractRateLimiterRepository]
* [`AsyncMultiRateLimitedTransport`][httpx_limiter.httpx.AsyncMultiRateLimitedTransport]
* [`AsyncRateLimitedTransport`][httpx_limiter.httpx2.AsyncRateLimitedTransport] (HTTPX2)
* [`AbstractRateLimiterRepository`][httpx_limiter.httpx2.AbstractRateLimiterRepository] (HTTPX2)
* [`AsyncMultiRateLimitedTransport`][httpx_limiter.httpx2.AsyncMultiRateLimitedTransport] (HTTPX2)
* [`AiolimiterAsyncLimiter`][httpx_limiter.aiolimiter.AiolimiterAsyncLimiter]
* [`PyrateAsyncLimiter`][httpx_limiter.pyrate.PyrateAsyncLimiter]

::: httpx_limiter
    options:
        members:
            - Rate
            - AbstractAsyncLimiter

::: httpx_limiter.httpx
    options:
        members:
            - AsyncRateLimitedTransport
            - AbstractRateLimiterRepository
            - AsyncMultiRateLimitedTransport

::: httpx_limiter.httpx2
    options:
        members:
            - AsyncRateLimitedTransport
            - AbstractRateLimiterRepository
            - AsyncMultiRateLimitedTransport

::: httpx_limiter.aiolimiter
    options:
        members:
            - AiolimiterAsyncLimiter

::: httpx_limiter.pyrate
    options:
        members:
            - PyrateAsyncLimiter
