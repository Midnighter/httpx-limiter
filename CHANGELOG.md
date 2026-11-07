# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Breaking Changes

- `httpx` is no longer a required dependency. Plain `pip install httpx-limiter`
  installs only the shared core, which imports no HTTP client. Select the HTTP client
  with an extra, `httpx` or `httpx2`, and normally also a rate limiter extra, for
  example `pip install 'httpx-limiter[httpx,aiolimiter]'`,
  `'httpx-limiter[httpx2,pyrate]'`, or `'httpx-limiter[httpx,httpx2,aiolimiter]'`.
- The HTTP-specific classes moved out of the package root into one sub-package per HTTP
  client. Migrate by changing the imports of `AsyncRateLimitedTransport`,
  `AsyncMultiRateLimitedTransport`, `AbstractRateLimiterRepository`, and
  `HTTPXAsyncHTTPTransportKeywordArguments`:

  ```diff
  -from httpx_limiter import AsyncRateLimitedTransport, Rate
  +from httpx_limiter import Rate
  +from httpx_limiter.httpx import AsyncRateLimitedTransport
  ```

  For HTTPX2, import from `httpx_limiter.httpx2` instead. `Rate`,
  `AbstractAsyncLimiter`, `AiolimiterAsyncLimiter`, and `PyrateAsyncLimiter` keep their
  import paths. The old root-level and module-level HTTP imports are removed without
  compatibility aliases.
- There is no automatic fallback or backend selection. Clients, transports, requests,
  and responses must all come from the same HTTP client: an `httpx_limiter.httpx`
  transport does not work with `httpx2` and vice versa.

### Added

- Added the HTTPX2 integration `httpx_limiter.httpx2` with its own
  `AsyncRateLimitedTransport`, `AsyncMultiRateLimitedTransport`,
  `AbstractRateLimiterRepository`, and `HTTPXAsyncHTTPTransportKeywordArguments`,
  installable with the new `httpx2` extra. Both integrations can be used in the same
  process.
- Added the `httpx` extra for the HTTPX integration `httpx_limiter.httpx`.
- Documented both integrations with side-by-side examples, and run the documentation
  examples for both HTTP clients in the documentation tests. The retry recipe stays
  HTTPX-only until `httpx-tenacity` supports HTTPX2.
- Added support for Python 3.15.

### Changed

- Updated the package description to mention both HTTPX and HTTPX2.
- Pyodide compatibility tests now run against Pyodide 314.0.7 (Python 3.14) and cover
  both the `httpx` and `httpx2` integrations. `aiolimiter` works in Pyodide with either
  client; `pyrate-limiter` is still not Pyodide-compatible.
- Updated `CONTRIBUTING.md` to use `fix/...` and `feat/...` branch names and the
  current hatch commands for style, type, test, and documentation checks.

### Removed

- Dropped support for Python 3.10.

### Fixed

- Fixed `AsyncRateLimitedTransport` and `AsyncMultiRateLimitedTransport` not closing
  their underlying transport. Both now implement `aclose` that awaits the composed
  transport's `aclose`, so closing a client or transport wrapper also closes the
  underlying transport. Sharing an inner transport between wrappers therefore shares
  its lifetime.
- Fixed `AsyncRateLimitedTransport` and `AsyncMultiRateLimitedTransport` not entering
  their underlying transport. Entering a wrapper, for example through
  `async with AsyncClient(transport=...)`, now also enters the composed transport, so
  custom transports that set up resources in `__aenter__` are ready before the first
  request.
- Fixed a flaky acceptance test by raising the burst of the Traefik rate limit in
  `compose.yaml` from 1 to 5, so that small timing jitter no longer causes spurious
  429 responses.

## [0.6.1] - (2026-05-01)

### Changed

- Converted package-level imports (in `__init__.py` modules) to use redundant symbol
  aliases. This change supports type checkers to recognize exported symbols that are
  intended to be part of the public package API.
  See <https://typing.python.org/en/latest/spec/distributing.html#import-conventions>
  for more information. This change has no functional impact.

## [0.6.0] - (2026-03-22)

### Added

-   Introduced [PEP-735](https://peps.python.org/pep-0735/) dependency groups.
    No impact on package functionality.
-   Started supporting Python 3.14.
-   Added `ty` alongside `mypy` for static type checking. No impact on package
    functionality.
-   Added a `style:fix` script to automatically fix style issues identified by
    `ruff check`. No impact on package functionality.

### Changed

-   Pinned all GitHub Actions to specific commit SHAs to ensure stability and
    security. No impact on package functionality.
-   Introduced `ubuntu-slim` image where possible. No impact on package
    functionality.
-   Made the `__aexit__` method of `AbstractAsyncLimiter` non-abstract and thus
    optional to implement by subclasses. No impact on package functionality.
-   Upgraded to pyrate-limiter v4 and adjusted to the new API.

## [0.5.0] - (2026-01-08)

### Changed

-   Introduced facilities to allow for multiple rate-limiter backends. That
    included an abstract base class for the limiter and two implementations based on
    aiolimiter and pyrate-limiter that have different capabilities. The changes
    broke the previous interface of the package.

## [0.4.0] - (2025-08-22)

### Added

-   Added the possibility to enforce multiple rate limits, for example, 10 per
    second, 1000 per minute, and so on.

### Changed

-   Replaced the `aiolimiter` dependency with `pyrate-limiter`.
-   Modified some types and method signatures to be compatible with the new
    `pyrate-limiter` dependency.

### Fixed

-   Provided type annotations for keyword arguments in the transports.

## [0.3.0] - (2025-05-10)

### Added

-   Added an `AbstractRateLimiterRepository` and `AsyncMultiRateLimitedTransport` allowing
    for multiple rate limits based on the request.

## [0.2.0] - (2025-04-04)

### Added

-   Added a `Rate` value object to the public interface.

### Changed

-   Replaced the `limiter` dependency with `aiolimiter`.

## [0.1.0] - (2024-11-22)

-   First release
