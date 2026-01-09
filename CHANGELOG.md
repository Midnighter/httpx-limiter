# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

-   Pinned all GitHub Actions to specific commit SHAs to ensure stability and
    security. No impact on package functionality.

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
