# ADR002 - Provide one integration per HTTP client

- Date: 2026-11-07
- Status: ACCEPTED
- Author: Moritz E. Beber

## Decision

HTTPX becomes an optional dependency. The HTTP-specific classes (`AsyncRateLimitedTransport`, `AsyncMultiRateLimitedTransport`, `AbstractRateLimiterRepository`, and `HTTPXAsyncHTTPTransportKeywordArguments`) live in one sub-package per HTTP client, `httpx_limiter.httpx` and `httpx_limiter.httpx2`, each installed with the extra of the same name. The package root keeps only the client-independent `Rate`, `Number`, and `AbstractAsyncLimiter`, and there is neither automatic client selection nor a compatibility alias for the old root imports.

## Context

HTTPX2 is a separate package that keeps the HTTPX API but defines its own classes. `Request`, `Response`, `Limits`, `Proxy`, and the transports of one client are distinct types from those of the other. The two clients do not interoperate: an `httpx.AsyncClient` with an HTTPX2 transport, and the reverse, fails with an `AssertionError`, and calling a transport's `handle_async_request` with the other client's request does not fail at all, so only static typing catches that mix-up. Users should be able to install the library with either client, or both, without pulling in the one they do not use. The rate limiters themselves do not depend on any HTTP client. The package is still in beta, so a breaking change to the import paths is acceptable.

## Options

1. (SELECTED) One sub-package per HTTP client
2. Keep HTTPX at the root and add an HTTPX2 sub-package
3. Select the HTTP client automatically
4. One sub-package per HTTP client with deprecated root aliases

### Option 1 (SELECTED): One sub-package per HTTP client

Move the HTTP-specific classes into `httpx_limiter.httpx` and `httpx_limiter.httpx2`. Each sub-package imports only its own client, annotates with that client's types, and raises a `ModuleNotFoundError` that names the extra to install when the client is missing. Code shared by both, such as the caching repository logic, lives in private, client-independent modules in the package root.

#### Consequences

- Adopted because: users install only the client they use, and the core imports no HTTP client at all.
- Adopted because: each integration is typed with its own client's classes, so type checkers reject mixing an HTTPX transport, request, or repository with HTTPX2 and vice versa.
- Adopted because: both integrations can be used in the same process, and limiters can be shared between them.
- Adopted because: both clients are treated symmetrically, so adding or dropping a client later does not move the other one.
- Adopted despite: it is a breaking change, and every user must change the imports of the HTTP-specific classes and select an extra.
- Adopted despite: the public classes exist twice under the same names, once per sub-package.

### Option 2: Keep HTTPX at the root and add an HTTPX2 sub-package

Keep `httpx` as a required dependency and the HTTPX classes in the package root, and add only `httpx_limiter.httpx2`.

#### Consequences

- Rejected because: HTTPX2 users would still have to install HTTPX.
- Rejected because: the two clients would be exposed asymmetrically, with one at the root and one in a sub-package.
- Rejected despite: existing imports would keep working without changes.

### Option 3: Select the HTTP client automatically

Expose one set of classes in the root that use whichever client is installed, falling back from one to the other.

#### Consequences

- Rejected because: the choice is ambiguous when both clients are installed, and the result depends on the environment instead of the code.
- Rejected because: the classes cannot be annotated with one client's types, so mix-ups would only fail at runtime, if at all.
- Rejected despite: users would not need to choose an import path.

### Option 4: One sub-package per HTTP client with deprecated root aliases

Use the sub-packages from option 1, but keep the old root imports as aliases that issue a deprecation warning.

#### Consequences

- Rejected because: the root aliases must import a specific client, so they fail with a `ModuleNotFoundError` when the HTTPX extra is not installed, or need a lazy module `__getattr__` that complicates the core.
- Rejected because: the package is in beta, and a clean break is simpler for users and maintainers than a deprecation period.
- Rejected despite: existing code would keep working for a transition period.

## Supporting Material

- Pull request introducing the integrations <https://github.com/Midnighter/httpx-limiter/pull/417>
- HTTPX2 on PyPI <https://pypi.org/project/httpx2/>
