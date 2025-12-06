# Usage Guide

This guide covers all the ways to use the OGC API Registry library for fetching, storing, and validating OpenAPI documents.

## Installation

=== "uv"

    ```bash
    uv add ogcapi-registry
    ```

=== "pip"

    ```bash
    pip install ogcapi-registry
    ```

## Quick Start

The simplest way to validate an OGC API document:

```python
from ogcapi_registry import validate_ogc_api

document = {
    "openapi": "3.0.3",
    "info": {"title": "My Features API", "version": "1.0.0"},
    "paths": {
        "/": {"get": {"responses": {"200": {"description": "OK"}}}},
        "/conformance": {"get": {"responses": {"200": {"description": "OK"}}}},
        "/collections": {"get": {"responses": {"200": {"description": "OK"}}}},
        # ... more paths
    }
}

result = validate_ogc_api(document, [
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core"
])

if result.is_valid:
    print("Valid OGC API - Features document!")
else:
    for error in result.errors:
        print(f"Error at {error['path']}: {error['message']}")
```

## Fetching Remote Specifications

### Synchronous Client

```python
from ogcapi_registry import OpenAPIClient

client = OpenAPIClient(
    timeout=30.0,  # Request timeout in seconds
    follow_redirects=True
)

# Fetch and parse a specification
content, metadata = client.fetch("https://example.com/api/openapi.json")

print(f"Fetched from: {metadata.source_url}")
print(f"Content type: {metadata.content_type}")
print(f"ETag: {metadata.etag}")
print(f"API Title: {content['info']['title']}")
```

### Asynchronous Client

```python
import asyncio
from ogcapi_registry import AsyncOpenAPIClient

async def fetch_spec():
    client = AsyncOpenAPIClient(timeout=30.0)
    content, metadata = await client.fetch("https://example.com/api/openapi.yaml")
    return content

document = asyncio.run(fetch_spec())
```

### Fetch with Structural Validation

```python
from ogcapi_registry import OpenAPIClient
from ogcapi_registry.exceptions import ParseError

client = OpenAPIClient()

try:
    # This validates basic OpenAPI structure (openapi field, info, etc.)
    content, metadata = client.fetch_and_validate_structure(
        "https://example.com/api/openapi.json"
    )
except ParseError as e:
    print(f"Invalid specification: {e}")
```

## Specification Registry

The registry stores OpenAPI specifications as immutable objects indexed by type and version.

### Registering Specifications

```python
from ogcapi_registry import (
    SpecificationRegistry,
    SpecificationType,
    SpecificationMetadata,
)

registry = SpecificationRegistry()

# Register from a URL (auto-detects type and version)
spec = registry.register_from_url("https://example.com/openapi.json")
print(f"Registered: {spec.key.spec_type} v{spec.key.version}")

# Register manually with explicit type/version
registry.register(
    content={
        "openapi": "3.0.3",
        "info": {"title": "Reference API", "version": "1.0.0"},
        "paths": {}
    },
    spec_type=SpecificationType.OPENAPI_3_0,
    version="3.0.3",
    metadata=SpecificationMetadata(source_url="local"),
)

# Overwrite existing specification
registry.register(
    content=updated_content,
    spec_type=SpecificationType.OPENAPI_3_0,
    version="3.0.3",
    overwrite=True,  # Required to replace existing
)
```

### Querying the Registry

```python
from ogcapi_registry import SpecificationRegistry, SpecificationType

registry = SpecificationRegistry()
# ... register some specs ...

# Check if a spec exists
if registry.exists(SpecificationType.OPENAPI_3_0, "3.0.3"):
    spec = registry.get(SpecificationType.OPENAPI_3_0, "3.0.3")
    print(f"Found: {spec.info_title}")

# List all registered specs
for spec in registry:
    print(f"{spec.key.spec_type}: {spec.key.version}")

# Get all keys
keys = registry.list_keys()

# Remove a specification
registry.remove(SpecificationType.OPENAPI_3_0, "3.0.3")

# Clear all specifications
registry.clear()
```

### Async Registry

```python
import asyncio
from ogcapi_registry import AsyncSpecificationRegistry

async def main():
    registry = AsyncSpecificationRegistry()

    # Async fetch and register
    spec = await registry.register_from_url("https://example.com/openapi.json")

    # Sync operations still work
    if registry.exists(spec.key.spec_type, spec.key.version):
        print("Registered successfully!")

asyncio.run(main())
```

## OGC API Validation

### Using Conformance Classes

The library validates documents based on OGC API conformance classes. You can provide them in several formats:

```python
from ogcapi_registry import validate_ogc_api, ConformanceClass

# As a list of strings
result = validate_ogc_api(document, [
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson",
])

# As ConformanceClass objects
result = validate_ogc_api(document, [
    ConformanceClass(uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core"),
])

# As a dict with conformsTo key (like /conformance response)
result = validate_ogc_api(document, {
    "conformsTo": [
        "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
    ]
})

# Auto-detect from document (infers from paths or x-conformance extension)
result = validate_ogc_api(document)
```

### Working with Conformance Classes

```python
from ogcapi_registry import (
    ConformanceClass,
    OGCAPIType,
    parse_conformance_classes,
    detect_api_types,
    get_primary_api_type,
)

# Parse conformance classes
ccs = parse_conformance_classes([
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/core",
])

# Detect all API types
types = detect_api_types(ccs)
print(types)  # {OGCAPIType.FEATURES, OGCAPIType.TILES}

# Get the primary (most specific) type
primary = get_primary_api_type(ccs)
print(primary)  # OGCAPIType.FEATURES

# Inspect a conformance class
cc = ConformanceClass(uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core")
print(cc.api_type)   # OGCAPIType.FEATURES
print(cc.is_core)    # True
print(cc.version)    # "1.0"
```

### Validation Results

```python
from ogcapi_registry import validate_ogc_api

result = validate_ogc_api(document, conformance_classes)

# Check validity
if result.is_valid:
    print("Document is valid!")
    if result.warnings:
        print("But there are warnings:")
        for warning in result.warnings:
            print(f"  - {warning['message']}")
else:
    print("Validation failed:")
    for error in result.errors:
        print(f"  [{error['path']}] {error['message']} (type: {error['type']})")

# Access validation metadata
if result.validated_against:
    print(f"Validated as: {result.validated_against.spec_type}")
```

### Using the Strategy Registry

For more control over validation, use the `StrategyRegistry` directly:

```python
from ogcapi_registry import (
    StrategyRegistry,
    ConformanceClass,
    OGCAPIType,
)

# Create a registry with all default strategies
registry = StrategyRegistry()

# List available strategies
for strategy in registry.list_strategies():
    print(f"{strategy.api_type}: {strategy.required_conformance_patterns}")

# Get a specific strategy
features_strategy = registry.get(OGCAPIType.FEATURES)

# Get the best strategy for conformance classes
ccs = [ConformanceClass(uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core")]
strategy = registry.get_for_conformance(ccs)
print(f"Selected strategy: {strategy.api_type}")

# Validate with auto-detection
result = registry.detect_and_validate(document, ccs)
```

### Using Individual Strategies

```python
from ogcapi_registry import FeaturesStrategy, ConformanceClass

strategy = FeaturesStrategy()

# Check what paths are required
ccs = [
    ConformanceClass(uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core"),
    ConformanceClass(uri="http://www.opengis.net/spec/ogcapi-features-2/1.0/conf/crs"),
]

required_paths = strategy.get_required_paths(ccs)
print("Required paths:", required_paths)
# ['/collections', '/collections/{collectionId}', '/collections/{collectionId}/items', ...]

required_ops = strategy.get_required_operations(ccs)
print("Required operations:", required_ops)
# {'/collections': ['get'], '/collections/{collectionId}/items': ['get'], ...}

# Validate a document
result = strategy.validate(document, ccs)
```

## Basic OpenAPI Validation

For non-OGC-specific OpenAPI validation:

```python
from ogcapi_registry import (
    validate_document,
    validate_openapi_structure,
    validate_openapi_with_pydantic,
    parse_openapi_content,
)

# Parse content (JSON or YAML)
content = parse_openapi_content(yaml_string, format_hint="yaml")

# Validate structure (JSON Schema validation)
result = validate_openapi_structure(content)

# Validate with Pydantic (stricter, OpenAPI 3.1 only)
result = validate_openapi_with_pydantic(content)

# Combined validation
result = validate_document(content)
```

## Validating Against Reference Specifications

```python
from ogcapi_registry import (
    SpecificationRegistry,
    OpenAPIValidator,
    validate_against_reference,
    SpecificationType,
)

# Using OpenAPIValidator with a registry
registry = SpecificationRegistry()
registry.register_from_url("https://example.com/reference-api.json")

validator = OpenAPIValidator(registry)

# Validate against a specific registered spec
result = validator.validate_against(
    document,
    spec_type=SpecificationType.OPENAPI_3_0,
    version="3.0.3",
    strict=True,  # Require exact version match
)

# Validate against the latest version of a type
result = validator.validate_against_latest(
    document,
    spec_type=SpecificationType.OPENAPI_3_0,
)
```

## Error Handling

```python
from ogcapi_registry import (
    OpenAPIClient,
    SpecificationRegistry,
    SpecificationType,
)
from ogcapi_registry.exceptions import (
    FetchError,
    ParseError,
    SpecificationNotFoundError,
    SpecificationAlreadyExistsError,
    ValidationError,
)

client = OpenAPIClient()
registry = SpecificationRegistry()

# Handle fetch errors
try:
    content, metadata = client.fetch("https://invalid-url.example.com/api.json")
except FetchError as e:
    print(f"Failed to fetch from {e.url}: {e.reason}")

# Handle parse errors
try:
    content, metadata = client.fetch_and_validate_structure("https://example.com/api.json")
except ParseError as e:
    print(f"Parse error: {e.reason} (source: {e.source})")

# Handle registry errors
try:
    registry.register(content, SpecificationType.OPENAPI_3_0, "3.0.3")
    registry.register(content, SpecificationType.OPENAPI_3_0, "3.0.3")  # Duplicate!
except SpecificationAlreadyExistsError as e:
    print(f"Spec already exists: {e.spec_type} v{e.version}")

try:
    spec = registry.get(SpecificationType.OPENAPI_3_0, "9.9.9")
except SpecificationNotFoundError as e:
    print(f"Spec not found: {e.spec_type} v{e.version}")
```

## Complete Example: Validating an OGC API - Features Implementation

```python
import json
from ogcapi_registry import (
    OpenAPIClient,
    SpecificationRegistry,
    StrategyRegistry,
    validate_ogc_api,
    OGCAPIType,
)

# 1. Fetch the OpenAPI document
client = OpenAPIClient()
document, metadata = client.fetch_and_validate_structure(
    "https://my-ogc-api.example.com/api"
)

print(f"Fetched: {document['info']['title']}")

# 2. Fetch conformance classes from the API
conformance_response, _ = client.fetch(
    "https://my-ogc-api.example.com/conformance"
)
conformance_classes = conformance_response.get("conformsTo", [])

print(f"Conformance classes: {len(conformance_classes)}")

# 3. Validate the document
result = validate_ogc_api(document, conformance_classes)

# 4. Report results
if result.is_valid:
    print("✅ Document is valid!")
    print(f"   Validated as: {result.validated_against.spec_type if result.validated_against else 'unknown'}")
else:
    print("❌ Validation failed:")
    for error in result.errors:
        print(f"   - [{error['type']}] {error['path']}: {error['message']}")

# 5. Show warnings if any
if result.warnings:
    print("⚠️ Warnings:")
    for warning in result.warnings:
        print(f"   - {warning['message']}")
```

## Tips and Best Practices

### 1. Always Provide Conformance Classes

While the library can infer API types from paths, providing explicit conformance classes ensures accurate validation:

```python
# Good: explicit conformance
result = validate_ogc_api(document, conformance_classes)

# Less accurate: auto-detection
result = validate_ogc_api(document)  # May miss some requirements
```

### 2. Use the Appropriate Validation Level

- `validate_ogc_api()`: Full OGC API validation with conformance-aware strategies
- `validate_document()`: Basic OpenAPI validation
- `validate_openapi_structure()`: Lightweight structural validation only

### 3. Handle Multi-API Implementations

For APIs that implement multiple OGC API types, the library automatically uses a composite strategy:

```python
# This API implements both Features and Tiles
conformance = [
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/core",
]

# Both Features and Tiles requirements will be validated
result = validate_ogc_api(document, conformance)
```

### 4. Store Specifications for Reference

Use the registry to cache specifications and avoid repeated fetches:

```python
from ogcapi_registry import SpecificationRegistry

registry = SpecificationRegistry()

# Fetch once
if not registry.exists(SpecificationType.OPENAPI_3_0, "3.0.3"):
    registry.register_from_url("https://example.com/openapi.json")

# Use cached version
spec = registry.get(SpecificationType.OPENAPI_3_0, "3.0.3")
```
