# OGC API Registry Validator

[![PyPI version](https://img.shields.io/pypi/v/ogcapi-registry?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/ogcapi-registry/)
[![Python versions](https://img.shields.io/pypi/pyversions/ogcapi-registry?style=for-the-badge&logo=python&logoColor=white)](https://pypi.org/project/ogcapi-registry/)
[![License](https://img.shields.io/github/license/francbartoli/ogcapi-registry?style=for-the-badge)](https://github.com/francbartoli/ogcapi-registry/blob/main/LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/francbartoli/ogcapi-registry/test.yml?branch=main&style=for-the-badge&logo=github&label=CI)](https://github.com/francbartoli/ogcapi-registry/actions/workflows/test.yml)
[![Docs](https://img.shields.io/github/actions/workflow/status/francbartoli/ogcapi-registry/docs.yml?branch=main&style=for-the-badge&logo=materialformkdocs&logoColor=white&label=Docs)](https://francbartoli.github.io/ogcapi-registry/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/ogcapi-registry?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/ogcapi-registry/)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-ruff-261230?style=for-the-badge&logo=ruff&logoColor=white)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue?style=for-the-badge&logo=python&logoColor=white)](https://mypy-lang.org/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-E92063?style=for-the-badge&logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)

A Python library for validating OpenAPI documents published by OGC API servers against OGC specification requirements.

## Why This Library?

OGC API standards (Features, Tiles, Processes, Records, etc.) define specific requirements for the OpenAPI documents that servers must publish. These requirements include:

- **Required endpoints** (e.g., `/collections`, `/conformance`)
- **Required HTTP operations** (GET, POST, etc.)
- **Conformance class declarations**
- **Response schemas and content types**

This library performs **static validation** of these OpenAPI documents, helping you verify that your OGC API server's published specification meets the standard requirements before deployment.

### Difference from OGC CITE Test Suite

| Aspect | ogcapi-registry | OGC CITE Test Suite |
|--------|-----------------|---------------------|
| **Type** | Static analysis | Runtime testing |
| **What it validates** | OpenAPI document structure | Actual server behavior |
| **Requires running server** | No (only the OpenAPI doc) | Yes |
| **Speed** | Fast (seconds) | Slow (minutes to hours) |
| **When to use** | CI/CD, pre-deployment | Certification, compliance |
| **Catches** | Missing paths, wrong methods, schema errors | 500 errors, wrong responses, bugs |

**Use both tools together:**

1. **ogcapi-registry** → Fast feedback during development, catches specification errors early
2. **OGC CITE** → Full compliance certification, validates actual server responses

```
Development Workflow:
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│ Write Code  │ --> │ ogcapi-registry  │ --> │  OGC CITE   │
│             │     │ (static check)   │     │ (runtime)   │
└─────────────┘     └──────────────────┘     └─────────────┘
      Fast              Seconds                 Minutes+
```

## Features

- **OGC API Validation**: Validate against OGC API - Features, Tiles, Processes, Records, Coverages, EDR, Maps, Styles, Routes
- **Conformance-Based Detection**: Automatically detect API type from conformance classes
- **Error Severity Levels**: Distinguish between critical errors, warnings, and informational messages
- **Extensible Strategy Pattern**: Add custom validation strategies for new specifications
- **Async Support**: Full async/await support for high-performance validation

## Installation

```bash
pip install ogcapi-registry
```

Or with uv:

```bash
uv add ogcapi-registry
```

## Quick Start

### Validating an OGC API Server

```python
from ogcapi_registry import (
    OpenAPIClient,
    validate_ogc_api,
    parse_conformance_classes,
)

# Fetch the OpenAPI document from your server
client = OpenAPIClient()
openapi_doc, metadata = client.fetch("https://demo.pygeoapi.io/master/openapi")

# Parse conformance classes (usually from /conformance endpoint)
conformance_uris = [
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson",
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/oas30",
]
conformance_classes = parse_conformance_classes(conformance_uris)

# Validate against OGC API requirements
result = validate_ogc_api(openapi_doc, conformance_classes)

if result.is_valid:
    print("OpenAPI document is fully compliant!")
else:
    # Check error severity
    for error in result.critical_errors:
        print(f"CRITICAL: {error['message']}")

    for warning in result.warnings:
        print(f"WARNING: {warning['message']}")
```

### Understanding Error Severity

The library classifies validation errors by severity:

```python
from ogcapi_registry import ErrorSeverity

# Critical errors: Must be fixed for OGC compliance
result.critical_errors  # Missing required endpoints, wrong HTTP methods

# Warnings: Should be fixed but API may still function
result.warnings  # Missing recommended features like CRS support

# Info: Optional improvements
result.info_errors  # Missing optional features like filtering

# Check if API is compliant (no critical errors)
if result.is_compliant:
    print("API meets minimum OGC requirements")
```

### Automatic API Type Detection

```python
from ogcapi_registry import detect_api_types, get_primary_api_type

# Detect all API types from conformance classes
api_types = detect_api_types(conformance_classes)
# e.g., {OGCAPIType.FEATURES, OGCAPIType.TILES}

# Get the primary (most specific) API type
primary = get_primary_api_type(conformance_classes)
# e.g., OGCAPIType.FEATURES
```

## Application Example: CI/CD Validation

Integrate OGC API validation into your deployment pipeline to catch specification errors before they reach production.

### Using the Example Script

The library includes a ready-to-use validation script in `examples/validate_ogc_api_server.py`:

```bash
# Clone the repository
git clone https://github.com/francbartoli/ogcapi-registry.git
cd ogcapi-registry

# Install dependencies
uv sync --all-extras --dev

# Run validation against a real OGC API server
uv run python -c "
from examples.validate_ogc_api_server import validate_server, print_report
report = validate_server('https://demo.ldproxy.net/daraa')
print_report(report)
"
```

The script will:
1. Fetch the OpenAPI document from `/api`
2. Fetch conformance classes from `/conformance`
3. Analyze conformance coverage
4. Validate against OGC API requirements
5. Print a detailed report with errors by severity

### Custom CI/CD Script

```python
#!/usr/bin/env python
"""validate_ogc_server.py - CI/CD validation script"""

import sys
import httpx
from ogcapi_registry import (
    OpenAPIClient,
    validate_ogc_api,
    parse_conformance_classes,
)


def validate_server(base_url: str) -> bool:
    """Validate an OGC API server's OpenAPI document."""

    # 1. Fetch conformance classes
    response = httpx.get(f"{base_url}/conformance")
    response.raise_for_status()
    conformance_uris = response.json().get("conformsTo", [])

    if not conformance_uris:
        print("ERROR: No conformance classes declared")
        return False

    conformance_classes = parse_conformance_classes(conformance_uris)
    print(f"Found {len(conformance_classes)} conformance classes")

    # 2. Fetch and validate OpenAPI document
    client = OpenAPIClient()
    openapi_doc, metadata = client.fetch(f"{base_url}/openapi")

    print(f"Validating OpenAPI {openapi_doc.get('openapi', 'unknown')}")

    # 3. Run OGC API validation
    result = validate_ogc_api(openapi_doc, conformance_classes)

    # 4. Report results
    print(f"\n{'='*50}")
    print(f"Validation Result: {'PASSED' if result.is_valid else 'FAILED'}")
    print(f"{'='*50}")

    if result.critical_errors:
        print(f"\nCritical Errors ({len(result.critical_errors)}):")
        for err in result.critical_errors:
            print(f"  - {err['path']}: {err['message']}")

    if result.warnings:
        print(f"\nWarnings ({len(result.warnings)}):")
        for warn in result.warnings:
            print(f"  - {warn['path']}: {warn['message']}")

    summary = result.get_summary()
    print(f"\nSummary: {summary['critical']} critical, "
          f"{summary['warning']} warnings, {summary['info']} info")

    # Return True only if no critical errors
    return result.is_compliant


if __name__ == "__main__":
    server_url = sys.argv[1] if len(sys.argv) > 1 else "https://demo.pygeoapi.io/master"

    success = validate_server(server_url)
    sys.exit(0 if success else 1)
```

Use in GitHub Actions:

```yaml
- name: Install ogcapi-registry
  run: pip install ogcapi-registry

- name: Validate OGC API Compliance
  run: python validate_ogc_server.py ${{ env.SERVER_URL }}
```

Or using the library's example script directly:

```yaml
- name: Checkout ogcapi-registry
  uses: actions/checkout@v4
  with:
    repository: francbartoli/ogcapi-registry
    path: ogcapi-registry

- name: Install uv
  uses: astral-sh/setup-uv@v4

- name: Install dependencies
  run: cd ogcapi-registry && uv sync --all-extras --dev

- name: Validate OGC API Server
  run: |
    cd ogcapi-registry
    uv run python -c "
    from examples.validate_ogc_api_server import validate_server, print_report
    report = validate_server('${{ env.SERVER_URL }}')
    print_report(report)
    exit(0 if report['status'] in ['valid', 'compliant'] else 1)
    "
```

## Supported OGC API Standards

| Standard | Strategy Class | Key Validations |
|----------|---------------|-----------------|
| OGC API - Common | `CommonStrategy` | Landing page, conformance, API definition |
| OGC API - Features | `FeaturesStrategy` | Collections, items, bbox, CRS |
| OGC API - Tiles | `TilesStrategy` | Tile matrix sets, tile endpoints |
| OGC API - Processes | `ProcessesStrategy` | Process list, execution, jobs |
| OGC API - Records | `RecordsStrategy` | Catalog, record queries |
| OGC API - Coverages | `CoveragesStrategy` | Coverage data access |
| OGC API - EDR | `EDRStrategy` | Environmental data queries |
| OGC API - Maps | `MapsStrategy` | Map rendering endpoints |
| OGC API - Styles | `StylesStrategy` | Style management |
| OGC API - Routes | `RoutesStrategy` | Routing endpoints |

## Advanced Usage

### Custom Validation Strategy

```python
from ogcapi_registry import ValidationStrategy, OGCAPIType, ValidationResult

class MyCustomStrategy(ValidationStrategy):
    """Custom validation for organization-specific requirements."""

    api_type = OGCAPIType.FEATURES

    def validate(self, document, conformance_classes):
        errors = []

        # Add custom validation logic
        if "/health" not in document.get("paths", {}):
            errors.append({
                "path": "paths",
                "message": "Missing /health endpoint (org requirement)",
                "severity": "warning",
            })

        return ValidationResult.success() if not errors else ValidationResult.failure(errors)
```

### Async Validation

```python
import asyncio
from ogcapi_registry import AsyncOpenAPIClient, validate_ogc_api

async def validate_multiple_servers(urls: list[str]):
    client = AsyncOpenAPIClient()

    async def validate_one(url):
        doc, _ = await client.fetch(f"{url}/openapi")
        # ... fetch conformance and validate
        return url, result

    results = await asyncio.gather(*[validate_one(url) for url in urls])
    return dict(results)
```

## Documentation

Full documentation: [https://francbartoli.github.io/ogcapi-registry/](https://francbartoli.github.io/ogcapi-registry/)

## Development

```bash
# Clone and install
git clone https://github.com/francbartoli/ogcapi-registry.git
cd ogcapi-registry
uv sync --all-extras --dev

# Run tests
uv run pytest -v

# Run linting
uv run ruff check src/ tests/
uv run mypy src/ogcapi_registry
```

## License

MIT
