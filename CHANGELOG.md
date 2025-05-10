# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - (2025-05-10)

### Added

- Added an `AbstractRateLimiterRepository` and `AsyncMultiRateLimitedTransport` allowing
  for multiple rate limits based on the request.

## [0.2.0] - (2025-04-04)

### Added

- Added a `Rate` value object to the public interface.

### Changed

- Replaced the `limiter` dependency with `aiolimiter`.

## [0.1.0] - (2024-11-22)

- First release
