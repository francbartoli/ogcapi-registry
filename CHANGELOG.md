# CHANGELOG


## v0.1.0 (2025-12-09)

### Bug Fixes

- Add missing methods to duck-typed strategy tests
  ([`ed45cae`](https://github.com/francbartoli/ogcapi-registry/commit/ed45cae1b75617de5830e517054e09ec44348f7c))

- Add get_conformance_score and supports_version methods to test custom strategies - Update protocol
  docstring example to include all required methods - Format protocols.py

These methods were added to ValidationStrategyProtocol but the test custom strategies were not
  updated to implement them, causing isinstance checks to fail.

- Add write permissions to docs workflow for PR preview deployment
  ([`f043b26`](https://github.com/francbartoli/ogcapi-registry/commit/f043b2622016aa75907755e72f302877c91d8738))

- Add contents: write permission for peaceiris/actions-gh-pages - Add pull-requests: write
  permission for commenting on PRs

- Resolve CI linting, formatting, and type checking failures
  ([`0d9bb01`](https://github.com/francbartoli/ogcapi-registry/commit/0d9bb0144e47fa4ab5be7dd570141fc5b8ee4eeb))

- Fix ruff linting errors (unused imports and variables) - Apply ruff formatting to 24 files - Add
  missing methods to ValidationStrategyProtocol (get_conformance_score, supports_version) - Fix
  RegistryProtocol type variance by using covariant type variable - Add mypy configuration with
  pydantic plugin to pyproject.toml - Remove redundant uv add commands from GitHub Actions workflow
  - Add pytest-cov to dev dependencies

- Simplify docs workflow - remove complex PR preview deployment
  ([`d47bb38`](https://github.com/francbartoli/ogcapi-registry/commit/d47bb3843e16470d648e58dca773578b64dff578))

The PR preview deployment was failing because: - gh-pages branch doesn't exist yet - GitHub Pages
  needs to be configured first

Simplified workflow to: - Build docs on PRs (to verify they build correctly) - Deploy only on push
  to main

Once the PR is merged and main deploys successfully, docs will be available at
  https://francbartoli.github.io/ogcapi-registry/

- **ci**: Disable build in semantic-release action
  ([`d86c18f`](https://github.com/francbartoli/ogcapi-registry/commit/d86c18fd171b0a91f291737066a54c1312ea3356))

- Add build: false to semantic-release action (build handled by publish job) - Remove build_command
  from pyproject.toml - Fix changelog_file deprecation warning

- **ci**: Remove uv cache to avoid GitHub Actions cache errors
  ([`b285b9f`](https://github.com/francbartoli/ogcapi-registry/commit/b285b9fccf21a33f7d582330c8aed64cd05013f6))

### Features

- Add automated semantic versioning and changelog
  ([`be42713`](https://github.com/francbartoli/ogcapi-registry/commit/be427133f429de03fd5641bb9e11757305443141))

- Configure python-semantic-release for automatic versioning - Add release workflow that runs on
  push to main - Semantic release parses conventional commits to determine version bumps - Automatic
  CHANGELOG.md generation and updates - Automatic GitHub release creation - Automatic PyPI
  publishing after successful release - Simplify publish.yml to TestPyPI-only manual workflow - Add
  initial CHANGELOG.md with v0.1.0 release notes

Commit message format: - feat: -> minor version bump (0.1.0 -> 0.2.0) - fix: -> patch version bump
  (0.1.0 -> 0.1.1) - feat!: or BREAKING CHANGE: -> major bump (0.1.0 -> 1.0.0)

Requires GH_TOKEN secret with repo and workflow permissions.

- Add automated semantic versioning and changelog
  ([`417cb7a`](https://github.com/francbartoli/ogcapi-registry/commit/417cb7a51a2d22f025e9e0f391f91a7141166f94))

- Configure python-semantic-release for automatic versioning - Add release workflow that runs on
  push to main - Semantic release parses conventional commits to determine version bumps - Automatic
  CHANGELOG.md generation and updates - Automatic GitHub release creation - Automatic PyPI
  publishing after successful release - Simplify publish.yml to TestPyPI-only manual workflow - Add
  initial CHANGELOG.md with v0.1.0 release notes

Commit message format: - feat: -> minor version bump (0.1.0 -> 0.2.0) - fix: -> patch version bump
  (0.1.0 -> 0.1.1) - feat!: or BREAKING CHANGE: -> major bump (0.1.0 -> 1.0.0)

Requires GH_TOKEN secret with repo and workflow permissions.

- Add error severity levels for distinguishing critical vs optional issues
  ([`f41e246`](https://github.com/francbartoli/ogcapi-registry/commit/f41e246be844ce7037d61d8aabf120a7095b29d3))

Add ErrorSeverity enum with CRITICAL, WARNING, and INFO levels to help users prioritize validation
  errors:

- CRITICAL: Required OGC conformance class violations (must fix) - WARNING: Optional conformance
  class issues (recommended to fix) - INFO: Best practices and recommendations (informational)

Changes: - Add ErrorSeverity enum to models.py - Add severity filtering methods to ValidationResult:
  - get_errors_by_severity() - critical_errors, warning_errors, info_errors properties -
  has_critical_errors property - is_compliant property (True if no critical errors) - get_summary()
  for error counts by severity - Update base strategy with create_error() helper method - Update
  CommonStrategy and FeaturesStrategy to use severity levels - Add comprehensive tests in
  test_error_severity.py - Document severity filtering in usage.md

- Add OGC API version-aware validation with OGCSpecificationRegistry
  ([`a6ab250`](https://github.com/francbartoli/ogcapi-registry/commit/a6ab2504fd6ee419a4e3f5afb7bcedfb0f77565c))

- Add OGCSpecificationKey model for identifying OGC API specs by type, version, and part - Add
  OGCSpecificationRegistry for storing reference OGC API specifications - Enhance ConformanceClass
  with spec_version, part, and conformance_class_name properties - Add helper functions:
  get_specification_keys, get_specification_versions, group_conformance_by_spec - Add version-aware
  validation support in ValidationStrategy and StrategyRegistry - Add validate_against_spec method
  for validating against specific OGC API versions - Update documentation with OGC Specification
  Registry usage and architecture diagrams - Add comprehensive tests for new functionality (191
  tests passing)

- Add OpenAPI Registry Validator library
  ([`59da482`](https://github.com/francbartoli/ogcapi-registry/commit/59da48262ca917be5ef6244e115cf4f9fa63ab46))

Implement a Python library for fetching, storing, and validating OpenAPI v3 specifications using uv
  as the project manager.

Features: - HTTP client (sync/async) for fetching remote OpenAPI specs in JSON/YAML - In-memory
  registry for storing specs as immutable Pydantic objects - Validation functions for validating
  OpenAPI documents - Support for both OpenAPI 3.0.x and 3.1.x versions - Comprehensive test suite
  with 87 tests

Note: openapi-pydantic only supports 3.1.x, so 3.0.x uses JSON Schema validation.

- Add Protocol support for duck typing
  ([`ab7ae3c`](https://github.com/francbartoli/ogcapi-registry/commit/ab7ae3c7da428b64be6ca94e3f61abd5eb811705))

- Add protocols.py module with Protocol definitions for structural subtyping -
  ValidationStrategyProtocol: enables duck-typed validation strategies -
  VersionAwareStrategyProtocol: extends with version support methods - RegistryProtocol: generic
  interface for specification registries - OpenAPIClientProtocol/AsyncOpenAPIClientProtocol: HTTP
  client interfaces - ConformanceClassProtocol: conformance class interface -
  SpecificationKeyProtocol: specification key interface - Update StrategyRegistry to accept
  ValidationStrategyProtocol - Add comprehensive tests for protocol compliance (203 tests passing) -
  Enables custom strategies without inheritance from ValidationStrategy

- Add Strategy pattern for OGC API validation
  ([`68d1aee`](https://github.com/francbartoli/ogcapi-registry/commit/68d1aee18982e855f7632ad799c83990c25401e3))

Implement the Strategy pattern to validate OpenAPI documents based on their declared conformance
  classes. Each OGC API type (Features, Tiles, Processes, Records, EDR, Coverages, Maps, Styles,
  Routes) has its own validation strategy with specific requirements.

Key additions: - OGCAPIType enum and ConformanceClass model for type detection - ValidationStrategy
  base class with conformance-based validation - Concrete strategies for all major OGC API types -
  StrategyRegistry with auto-detection from conformance classes - Path inference when explicit
  conformance is not provided - CompositeValidationStrategy for multi-API implementations - 69 new
  tests for the strategy pattern (156 total)

Usage: from ogcapi_registry import validate_ogc_api result = validate_ogc_api(document,
  conformance_classes)

- Add surge.sh preview deployments for PR documentation
  ([`1aac78a`](https://github.com/francbartoli/ogcapi-registry/commit/1aac78af8892606176ffc22b5ebd30863f594f45))

- Use surge.sh for PR preview deployments (free service) - Each PR gets unique URL:
  ogcapi-registry-pr-{number}.surge.sh - Bot comments on PR with preview link - Reuse build artifact
  from build job (no duplicate builds)

Requires SURGE_TOKEN secret to be configured in repository settings. To get a token: npm install -g
  surge && surge token

### Refactoring

- Use openapi-pydantic for both OpenAPI 3.0.x and 3.1.x validation
  ([`5fcca21`](https://github.com/francbartoli/ogcapi-registry/commit/5fcca2103bd5c9dd63cee7d82dcb92c925006d79))

- Remove jsonschema dependency (no longer needed) - Use openapi_pydantic.v3.v3_0.OpenAPI for 3.0.x
  validation - Use openapi_pydantic.OpenAPI (3.1.x) for 3.1.x validation - Update models.py
  to_openapi() to return appropriate model for version - Update tests to reflect new 3.0.x support -
  Simplify validate_openapi_structure() by removing JSON Schema validation

This provides consistent Pydantic-based validation for both OpenAPI versions.
