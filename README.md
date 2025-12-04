# OpenAPI Registry Validator

A Python library for fetching, storing, and validating OpenAPI v3 specifications.

## Features

- **HTTP Client**: Fetch remote OpenAPI specifications in JSON or YAML format
- **In-Memory Registry**: Store specifications as immutable Pydantic objects indexed by type and version
- **Validation Functions**: Validate OpenAPI documents against stored specifications or standalone

## Installation

```bash
uv add openapi-registry-validator
```

Or with pip:

```bash
pip install openapi-registry-validator
```

## Quick Start

### Fetching and Registering Specifications

```python
from openapi_registry_validator import SpecificationRegistry, SpecificationType

# Create a registry
registry = SpecificationRegistry()

# Fetch and register a specification from a URL
spec = registry.register_from_url("https://example.com/openapi.json")
print(f"Registered: {spec.key.spec_type.value} version {spec.key.version}")

# Or register a specification manually
registry.register(
    content={
        "openapi": "3.0.3",
        "info": {"title": "My API", "version": "1.0.0"},
        "paths": {},
    },
    spec_type=SpecificationType.OPENAPI_3_0,
    version="3.0.3",
)
```

### Validating Documents

```python
from openapi_registry_validator import validate_document, OpenAPIValidator

# Simple validation
result = validate_document({
    "openapi": "3.0.3",
    "info": {"title": "My API", "version": "1.0.0"},
    "paths": {},
})

if result.is_valid:
    print("Document is valid!")
else:
    for error in result.errors:
        print(f"Error at {error['path']}: {error['message']}")

# Validate against a registered specification
validator = OpenAPIValidator(registry)
result = validator.validate_against(
    document=my_doc,
    spec_type=SpecificationType.OPENAPI_3_0,
    version="3.0.3",
)
```

### Async Support

```python
import asyncio
from openapi_registry_validator import AsyncSpecificationRegistry

async def main():
    registry = AsyncSpecificationRegistry()
    spec = await registry.register_from_url("https://example.com/openapi.json")
    print(f"Fetched: {spec.info_title}")

asyncio.run(main())
```

## API Reference

### Models

- `SpecificationType`: Enum for OpenAPI versions (`OPENAPI_3_0`, `OPENAPI_3_1`)
- `SpecificationKey`: Immutable key combining spec type and version
- `SpecificationMetadata`: Metadata about fetched specifications (URL, timestamp, ETag)
- `RegisteredSpecification`: Immutable specification stored in the registry
- `ValidationResult`: Result of validation with errors and warnings

### Registry

- `SpecificationRegistry`: Thread-safe in-memory registry for specifications
- `AsyncSpecificationRegistry`: Async-compatible registry

### Validation Functions

- `validate_document()`: Validate an OpenAPI document
- `validate_openapi_structure()`: Validate basic OpenAPI structure
- `validate_openapi_with_pydantic()`: Validate using Pydantic models (3.1 only)
- `validate_against_reference()`: Validate against a reference specification

### Client

- `OpenAPIClient`: Synchronous HTTP client for fetching specifications
- `AsyncOpenAPIClient`: Asynchronous HTTP client

## Notes

- The `openapi-pydantic` library only supports OpenAPI 3.1.x. For 3.0.x specifications, validation is performed using JSON Schema only.
- The `to_openapi()` method on `RegisteredSpecification` raises `ValueError` for 3.0.x specs.

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest -v

# Run tests with coverage
uv run pytest --cov=openapi_registry_validator
```

## License

MIT
