# OGC API Registry

<p align="center">
  <a href="https://pypi.org/project/ogcapi-registry/"><img src="https://img.shields.io/pypi/v/ogcapi-registry?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI version"></a>
  <a href="https://pypi.org/project/ogcapi-registry/"><img src="https://img.shields.io/pypi/pyversions/ogcapi-registry?style=for-the-badge&logo=python&logoColor=white" alt="Python versions"></a>
  <a href="https://github.com/francbartoli/ogcapi-registry/blob/main/LICENSE"><img src="https://img.shields.io/github/license/francbartoli/ogcapi-registry?style=for-the-badge" alt="License"></a>
</p>

<p align="center">
  <a href="https://github.com/francbartoli/ogcapi-registry/actions/workflows/test.yml"><img src="https://img.shields.io/github/actions/workflow/status/francbartoli/ogcapi-registry/test.yml?branch=main&style=for-the-badge&logo=github&label=CI" alt="CI"></a>
  <a href="https://pypi.org/project/ogcapi-registry/"><img src="https://img.shields.io/pypi/dm/ogcapi-registry?style=for-the-badge&logo=pypi&logoColor=white" alt="Downloads"></a>
</p>

<p align="center">
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/badge/code%20style-ruff-261230?style=for-the-badge&logo=ruff&logoColor=white" alt="Ruff"></a>
  <a href="https://mypy-lang.org/"><img src="https://img.shields.io/badge/type%20checked-mypy-blue?style=for-the-badge&logo=python&logoColor=white" alt="mypy"></a>
  <a href="https://docs.pydantic.dev/"><img src="https://img.shields.io/badge/Pydantic-v2-E92063?style=for-the-badge&logo=pydantic&logoColor=white" alt="Pydantic v2"></a>
</p>

---

A Python library for fetching, storing, and validating OGC API OpenAPI documents.

## Features

- **HTTP Client**: Fetch remote OpenAPI specifications in JSON or YAML format
- **In-Memory Registry**: Store specifications as immutable Pydantic objects indexed by type and version
- **Strategy Pattern Validation**: Validate OpenAPI documents based on OGC API conformance classes
- **Auto-Detection**: Automatically detect OGC API types from conformance classes or document structure

## Supported OGC API Types

| API Type | Description |
|----------|-------------|
| Common | Base functionality shared by all OGC APIs |
| Features | Vector feature data access (Part 1, 2, 3) |
| Tiles | Tiled data access |
| Maps | Map image generation |
| Processes | Processing services |
| Records | Catalog/metadata services |
| Coverages | Coverage data access |
| EDR | Environmental Data Retrieval |
| Styles | Style management |
| Routes | Routing services |

## Quick Start

```python
from ogcapi_registry import validate_ogc_api

# Validate an OpenAPI document
result = validate_ogc_api(
    document,
    conformance_classes=[
        "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
    ]
)

if result.is_valid:
    print("Document is valid!")
else:
    for error in result.errors:
        print(f"Error: {error['message']}")
```

## Installation

```bash
# Using uv
uv add ogcapi-registry

# Using pip
pip install ogcapi-registry
```

## Documentation

- [Architecture](architecture.md) - System design and patterns
- [Usage Guide](usage.md) - Detailed API usage examples
