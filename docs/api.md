The following classes are exposed to the user. The HTTP-specific classes live in the
sub-package of the HTTP client that you use, `httpx_limiter.httpx` or
`httpx_limiter.httpx2`, and each requires the matching extra.

* [`Rate`][httpx_limiter.Rate]
* [`AbstractAsyncLimiter`][httpx_limiter.AbstractAsyncLimiter]
* [`AsyncRateLimitedTransport`][httpx_limiter.httpx.AsyncRateLimitedTransport]
* [`AbstractRateLimiterRepository`][httpx_limiter.httpx.AbstractRateLimiterRepository]
* [`AsyncMultiRateLimitedTransport`][httpx_limiter.httpx.AsyncMultiRateLimitedTransport]
* [`HTTPXAsyncHTTPTransportKeywordArguments`][httpx_limiter.httpx.HTTPXAsyncHTTPTransportKeywordArguments]
* [`AsyncRateLimitedTransport`][httpx_limiter.httpx2.AsyncRateLimitedTransport] (HTTPX2)
* [`AbstractRateLimiterRepository`][httpx_limiter.httpx2.AbstractRateLimiterRepository] (HTTPX2)
* [`AsyncMultiRateLimitedTransport`][httpx_limiter.httpx2.AsyncMultiRateLimitedTransport] (HTTPX2)
* [`HTTPXAsyncHTTPTransportKeywordArguments`][httpx_limiter.httpx2.HTTPXAsyncHTTPTransportKeywordArguments] (HTTPX2)
* [`AiolimiterAsyncLimiter`][httpx_limiter.aiolimiter.AiolimiterAsyncLimiter]
* [`PyrateAsyncLimiter`][httpx_limiter.pyrate.PyrateAsyncLimiter]

## Core

::: httpx_limiter
    options:
        members:
            - Rate
            - AbstractAsyncLimiter

## HTTPX

::: httpx_limiter.httpx
    options:
        members:
            - AsyncRateLimitedTransport
            - AbstractRateLimiterRepository
            - AsyncMultiRateLimitedTransport
            - HTTPXAsyncHTTPTransportKeywordArguments

## HTTPX2

::: httpx_limiter.httpx2
    options:
        members:
            - AsyncRateLimitedTransport
            - AbstractRateLimiterRepository
            - AsyncMultiRateLimitedTransport
            - HTTPXAsyncHTTPTransportKeywordArguments

## Rate limiters

::: httpx_limiter.aiolimiter
    options:
        members:
            - AiolimiterAsyncLimiter

::: httpx_limiter.pyrate
    options:
        members:
            - PyrateAsyncLimiter
