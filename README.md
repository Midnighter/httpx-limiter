# HTTPX Limiter

| |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
|---|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Package | [![Latest PyPI Version](https://img.shields.io/pypi/v/httpx-limiter.svg)](https://pypi.org/project/httpx-limiter/) [![Supported Python Versions](https://img.shields.io/pypi/pyversions/httpx-limiter.svg)](https://pypi.org/project/httpx-limiter/) [![Documentation](https://readthedocs.org/projects/httpx-limiter/badge/?version=latest)](https://httpx-limiter.readthedocs.io/en/latest/?badge=latest)                                                                                                                                                                              |
| Meta | [![Apache-2.0](https://img.shields.io/pypi/l/httpx-limiter.svg)](LICENSE) [![Code of Conduct](https://img.shields.io/badge/Contributor%20Covenant-v2.0%20adopted-ff69b4.svg)](.github/CODE_OF_CONDUCT.md) [![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/) [![Code Style Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black) [![Linting: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) |
| Automation |                                                                                                                                                                                                                                                                                                                                                                                                                                       |

_A lightweight package that provides rate-limited httpx transports._

## Installation

The package is published on [PyPI](https://pypi.org/project/httpx-limiter/).
Install it, for example, with

```sh
pip install httpx-limiter
```

## Usage

For situations when you need to make a large number of asynchronous request with
a controlled number of requests per unit time, you can apply rate limiting to an
HTTPX client using the provided transport. If you want to be able to make ten
requests per second, for example, use the following:

```python
import httpx
from httpx_limiter import AsyncRateLimitedTransport, Rate

async def main():
    async with httpx.AsyncClient(
        transport=AsyncRateLimitedTransport.create(rate=Rate.create(magnitude=10)),
    ) as client:
        response = await client.get("https://httpbin.org")
```

## Copyright

- Copyright © 2024,2025 Moritz E. Beber.
- Free software distributed under the [Apache Software License 2.0](./LICENSE).
