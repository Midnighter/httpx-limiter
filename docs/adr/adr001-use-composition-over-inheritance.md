# ADR001 - Use composition over inheritance

- Date: 2024-11-22
- Status: ACCEPTED
- Author: Moritz E. Beber

## Decision

The rate-limited transports subclass only the abstract `httpx.AsyncBaseTransport` and wrap an injected transport and an injected rate limiter, instead of subclassing `httpx.AsyncHTTPTransport`. Each request is delegated to the wrapped transport inside the limiter's context manager.

## Context

httpx separates clients from transports, and any object implementing `httpx.AsyncBaseTransport` can be plugged into an async client. Rate limiting is cross-cutting behaviour that should apply regardless of which transport sends the request: the default `AsyncHTTPTransport`, a `MockTransport` in tests, or third-party transports such as caching layers. It should also be possible to layer rate limiting with other wrapping transports in whatever order an application needs. Separately, the limiter itself is abstracted behind `AbstractAsyncLimiter`, so the transport cannot assume a concrete limiter implementation and is composed of two injected parts.

## Options

1. (SELECTED) Composition
2. Subclass the HTTP transport

### Option 1 (SELECTED): Composition

Subclass only the abstract base transport and wrap an injected transport, delegating each request to it inside the limiter's context manager.

#### Consequences

- Adopted because: it works with any transport implementing the base interface.
- Adopted because: it can be stacked with other wrapping transports in any order.
- Adopted because: the wrapper stays small and easy to test by injecting a `MockTransport` and a limiter.
- Adopted because: it composes naturally with the `AbstractAsyncLimiter` abstraction, letting the same transport work with any limiter backend.
- Adopted despite: `AsyncHTTPTransport`'s constructor options are not inherited, so `create(**kwargs)` has to forward them and type them separately (`HTTPXAsyncHTTPTransportKeywordArguments`).
- Adopted despite: the wrapper must forward lifecycle methods such as `aclose()` to the wrapped transport, which also shares the inner transport's lifetime.

### Option 2: Subclass the HTTP transport

Subclass `httpx.AsyncHTTPTransport` and override `handle_async_request` to rate-limit around the parent implementation.

#### Consequences

- Rejected because: rate limiting would be tied to the HTTP transport and unavailable for other transport types, such as `MockTransport` or third-party transports.
- Rejected because: it cannot be layered with other wrapping transports through composition.
- Rejected despite: it inherits the constructor options and the `aclose()` lifecycle for free, leaving one object to configure.

## Supporting Material

- httpx transports documentation <https://www.python-httpx.org/advanced/transports/>
