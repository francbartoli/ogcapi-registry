# OGC API Registry

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
