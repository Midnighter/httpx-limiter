# ADR003 - Define the limiter and repository interfaces as abstract base classes

- Date: 2026-11-07
- Status: ACCEPTED
- Author: Moritz E. Beber

## Decision

The limiter interface `AbstractAsyncLimiter` and the rate limiter repository stay abstract base classes instead of becoming `typing.Protocol`s. Supported limiters are explicit: this package ships a subclass of `AbstractAsyncLimiter` for each limiter backend it supports. The internal, generic `RateLimiterRepository[RequestT]` implements the caching `get` method, and each HTTP integration exposes a subclass, `AbstractRateLimiterRepository`, that users subclass to implement `get_identifier` and `create` for their client's requests.

## Context

The transports enter a limiter as an asynchronous context manager around each request, and `AsyncMultiRateLimitedTransport` asks a repository for the limiter of each request. A repository decides how to identify a request and which limiter to create for it, and it must return the same limiter for the same identifier so that requests sharing a limit share its state. Limiter backends, such as aiolimiter and pyrate-limiter, are optional dependencies that this package wraps in `AiolimiterAsyncLimiter` and `PyrateAsyncLimiter`, which also translate a `Rate` into the backend's configuration. With the introduction of one integration per HTTP client (ADR002), the repository became generic over the request type, which prompted the question whether structural `Protocol`s, possibly `runtime_checkable`, would be better interfaces than nominal abstract base classes.

## Options

1. (SELECTED) Abstract base classes
2. Protocols with runtime checks

### Option 1 (SELECTED): Abstract base classes

Keep `AbstractAsyncLimiter` as an `ABC` with an abstract `__aenter__` and a default `__aexit__`. Keep `RateLimiterRepository` as a generic `ABC` with abstract `get_identifier` and `create` methods and a concrete, caching `get` method that subclasses inherit.

#### Consequences

- Adopted because: support for a limiter backend is explicit, since this package ships and wraps each supported limiter, and the wrapper translates a `Rate` into the backend's configuration.
- Adopted because: every repository inherits one correct caching implementation, so users only implement how to identify a request and which limiter to create.
- Adopted because: instantiating a subclass that misses an abstract method fails immediately with a `TypeError` that names the missing method.
- Adopted despite: a limiter or repository from elsewhere with matching methods, such as `aiolimiter.AsyncLimiter`, cannot be used without a subclass.

### Option 2: Protocols with runtime checks

Define both interfaces as `runtime_checkable` `Protocol`s, generic over the request type for the repository, and accept any object that matches them. A trial showed that the existing limiter subclasses keep working unchanged when they inherit from such a protocol explicitly, and that mypy, ty, and pyrefly accept `aiolimiter.AsyncLimiter` passed directly.

#### Consequences

- Rejected because: a limiter protocol matches any asynchronous context manager, such as `asyncio.Semaphore` or `asyncio.timeout()`, so whether an object is a rate limiter would only be a convention.
- Rejected because: a repository protocol does not share the caching `get` implementation with classes that only match it structurally, so every implementation would have to cache correctly itself, or the caching would have to move into the transport.
- Rejected because: `isinstance` checks against a `runtime_checkable` protocol only test that the methods exist, not their signatures or the request type, so the runtime check gives little safety beyond what static typing already provides.
- Rejected because: an incomplete implementation that does not inherit from the protocol is only detected by a type checker or when the missing method is called, not when the object is created.
- Rejected despite: any object with matching methods would work without inheriting from the library, which decouples user code and simplifies test doubles.

## Supporting Material

- `typing.Protocol` and `runtime_checkable` <https://docs.python.org/3/library/typing.html#typing.Protocol>
- `abc` module <https://docs.python.org/3/library/abc.html>
