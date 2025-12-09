# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and uses [Conventional Commits](https://www.conventionalcommits.org/).

## [0.1.0] - 2024-12-09

### Features

- Initial release of ogcapi-registry
- HTTP client for fetching OpenAPI specifications (sync and async)
- In-memory registry for storing specifications
- OpenAPI validation using openapi-pydantic (supports 3.0.x and 3.1.x)
- OGC API validation strategies for:
  - OGC API - Common
  - OGC API - Features
  - OGC API - Tiles
  - OGC API - Processes
  - OGC API - Records
  - OGC API - Coverages
  - OGC API - EDR
  - OGC API - Maps
  - OGC API - Styles
  - OGC API - Routes
- Conformance-based API type detection
- Error severity levels (critical, warning, info)
- Composite validation strategy for multi-API servers
- Protocol classes for duck-typed extensibility

### Documentation

- Full documentation with MkDocs Material
- Usage guide with examples
- Architecture documentation
