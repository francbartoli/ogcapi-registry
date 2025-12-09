# Architecture

This document describes the architecture of the OGC API Registry library, including the design patterns used and the component structure.

## Overview

The library is built around two main architectural patterns:

1. **Registry Pattern**: For storing and retrieving OpenAPI specifications
2. **Strategy Pattern**: For validating documents based on OGC API conformance classes

## High-Level Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        OC[OpenAPIClient]
        AOC[AsyncOpenAPIClient]
    end

    subgraph "Registry Layer"
        SR[SpecificationRegistry]
        ASR[AsyncSpecificationRegistry]
        OGCR[OGCSpecificationRegistry]
    end

    subgraph "Validation Layer"
        STR[StrategyRegistry]
        OV[OpenAPIValidator]
    end

    subgraph "Strategy Layer"
        VS[ValidationStrategy]
        CS[CommonStrategy]
        FS[FeaturesStrategy]
        TS[TilesStrategy]
        PS[ProcessesStrategy]
        OS[Other Strategies...]
    end

    subgraph "OGC Types"
        SK[OGCSpecificationKey]
        CC[ConformanceClass]
        AT[OGCAPIType]
    end

    OC --> SR
    OC --> OGCR
    AOC --> ASR
    SR --> OV
    OGCR --> STR
    STR --> VS
    VS --> CS
    VS --> FS
    VS --> TS
    VS --> PS
    VS --> OS
    OV --> STR
    CC --> SK
    SK --> OGCR
    AT --> SK
```

## Strategy Pattern Implementation

The Strategy pattern is the core of the OGC API validation system. It allows different validation logic to be applied based on the conformance classes declared by an API implementation.

### Class Diagram

```mermaid
classDiagram
    class ValidationStrategy {
        <<abstract>>
        +api_type: OGCAPIType
        +required_conformance_patterns: list
        +optional_conformance_patterns: list
        +validate(document, conformance_classes) ValidationResult
        +get_required_paths(conformance_classes) list
        +get_required_operations(conformance_classes) dict
        +matches_conformance(conformance_classes) bool
        +get_conformance_score(conformance_classes) int
    }

    class CommonStrategy {
        +api_type = COMMON
        +validate()
        +get_required_paths()
        +get_required_operations()
    }

    class FeaturesStrategy {
        +api_type = FEATURES
        +validate()
        +get_required_paths()
        +get_required_operations()
        -_validate_collections_endpoint()
        -_validate_items_endpoint()
        -_validate_crs_support()
    }

    class TilesStrategy {
        +api_type = TILES
        +validate()
        +get_required_paths()
        +get_required_operations()
        -_validate_tileset_endpoint()
        -_validate_tile_endpoint()
    }

    class ProcessesStrategy {
        +api_type = PROCESSES
        +validate()
        +get_required_paths()
        +get_required_operations()
        -_validate_execution_endpoint()
        -_validate_jobs_endpoint()
    }

    class CompositeValidationStrategy {
        -strategies: list
        +validate()
        +get_required_paths()
        +get_required_operations()
    }

    class StrategyRegistry {
        -strategies: dict
        +register(strategy)
        +get(api_type) ValidationStrategy
        +get_for_conformance(conformance_classes) ValidationStrategy
        +detect_and_validate(document, conformance_classes) ValidationResult
    }

    ValidationStrategy <|-- CommonStrategy
    ValidationStrategy <|-- FeaturesStrategy
    ValidationStrategy <|-- TilesStrategy
    ValidationStrategy <|-- ProcessesStrategy
    ValidationStrategy <|-- CompositeValidationStrategy
    StrategyRegistry o-- ValidationStrategy
```

### Strategy Selection Flow

```mermaid
sequenceDiagram
    participant Client
    participant StrategyRegistry
    participant Strategy
    participant Document

    Client->>StrategyRegistry: detect_and_validate(document, conformance_classes)

    alt No conformance classes provided
        StrategyRegistry->>Document: Extract from x-conformance
        StrategyRegistry->>Document: Infer from paths
    end

    StrategyRegistry->>StrategyRegistry: get_for_conformance(conformance_classes)

    loop For each registered strategy
        StrategyRegistry->>Strategy: matches_conformance(conformance_classes)
        Strategy-->>StrategyRegistry: true/false
    end

    alt Multiple strategies match
        StrategyRegistry->>StrategyRegistry: Create CompositeValidationStrategy
    end

    StrategyRegistry->>Strategy: validate(document, conformance_classes)
    Strategy->>Strategy: get_required_paths()
    Strategy->>Strategy: validate_paths_exist()
    Strategy->>Strategy: validate_operations_exist()
    Strategy-->>StrategyRegistry: ValidationResult
    StrategyRegistry-->>Client: ValidationResult
```

## Component Details

### OGC API Types

The `OGCAPIType` enum defines all supported OGC API specification types:

```python
class OGCAPIType(str, Enum):
    COMMON = "ogcapi-common"
    FEATURES = "ogcapi-features"
    TILES = "ogcapi-tiles"
    MAPS = "ogcapi-maps"
    PROCESSES = "ogcapi-processes"
    RECORDS = "ogcapi-records"
    COVERAGES = "ogcapi-coverages"
    EDR = "ogcapi-edr"
    STYLES = "ogcapi-styles"
    ROUTES = "ogcapi-routes"
```

### Conformance Classes

Conformance classes are URIs that identify specific capabilities an API supports. The library uses them to:

1. **Detect API Type**: Each conformance class URI contains patterns that identify the API type
2. **Select Validation Strategy**: The appropriate strategy is chosen based on matching conformance patterns
3. **Determine Required Features**: Within a strategy, conformance classes determine which paths and operations are required

```mermaid
graph LR
    CC[Conformance Class URI] --> DT{Detect Type}
    DT -->|"contains 'features'"| F[Features]
    DT -->|"contains 'tiles'"| T[Tiles]
    DT -->|"contains 'processes'"| P[Processes]
    DT -->|"contains 'common'"| C[Common]
    DT -->|"unknown"| C
```

### Validation Strategy Behavior

Each strategy validates documents according to conformance class requirements:

| Strategy | Core Requirements | Conformance-Dependent |
|----------|-------------------|----------------------|
| Common | `/`, `/conformance` | `/api` (oas30) |
| Features | `/collections`, `/collections/{id}/items` | CRS params (crs), Filter params (filter) |
| Tiles | `/tiles` (dataset) or collection tiles | TileMatrixSets list (tilesets-list) |
| Processes | `/processes`, `/processes/{id}/execution` | `/jobs` list (job-list), DELETE job (dismiss) |
| Records | `/collections/{id}/items` with `q` param | Sorting, CQL filter |
| EDR | Collection query endpoints | Position, Area, Cube, Trajectory, Corridor |

### Composite Strategy

When an API declares conformance to multiple OGC API types (e.g., Features + Tiles), the `CompositeValidationStrategy` combines validation from all relevant strategies:

```mermaid
graph TB
    subgraph "Composite Strategy"
        CV[CompositeValidationStrategy]
        CV --> FS[FeaturesStrategy]
        CV --> TS[TilesStrategy]
    end

    FS --> FR[Features Results]
    TS --> TR[Tiles Results]
    FR --> MR[Merged Results]
    TR --> MR
```

## Data Models

### Immutable Models

All data models use Pydantic with `frozen=True` for immutability:

```mermaid
classDiagram
    class SpecificationKey {
        <<frozen>>
        +spec_type: SpecificationType
        +version: str
    }

    class SpecificationMetadata {
        <<frozen>>
        +source_url: str
        +fetched_at: datetime
        +content_type: str
        +etag: str
    }

    class RegisteredSpecification {
        <<frozen>>
        +key: SpecificationKey
        +metadata: SpecificationMetadata
        +raw_content: dict
        +openapi_version: str
        +info_title: str
    }

    class ValidationResult {
        <<frozen>>
        +is_valid: bool
        +errors: tuple
        +warnings: tuple
        +validated_against: SpecificationKey
    }

    class ConformanceClass {
        <<frozen>>
        +uri: str
        +api_type: OGCAPIType
        +is_core: bool
        +version: str
    }

    RegisteredSpecification --> SpecificationKey
    RegisteredSpecification --> SpecificationMetadata
```

## Thread Safety

The `SpecificationRegistry` uses a reentrant lock (`threading.RLock`) to ensure thread-safe operations:

- All read/write operations acquire the lock
- Iteration returns a copy of the data to avoid modification during iteration
- Immutable models prevent accidental modifications

## OGC Specification Registry

The `OGCSpecificationRegistry` stores reference OGC API specifications indexed by API type, version, and part number.

### Class Diagram

```mermaid
classDiagram
    class OGCSpecificationKey {
        <<frozen>>
        +api_type: OGCAPIType
        +spec_version: str
        +part: int | None
        +matches(other, strict) bool
        +__hash__() int
        +__str__() str
    }

    class OGCRegisteredSpecification {
        +key: OGCSpecificationKey
        +raw_content: dict
        +metadata: SpecificationMetadata
        +openapi_version: str
        +info_title: str
        +paths: dict
    }

    class OGCSpecificationRegistry {
        -specs: dict
        -lock: RLock
        +register(api_type, version, content) OGCRegisteredSpecification
        +register_from_url(api_type, version, url) OGCRegisteredSpecification
        +get(api_type, version, part) OGCRegisteredSpecification
        +get_latest(api_type) OGCRegisteredSpecification
        +list_versions(api_type) list
        +list_by_type(api_type) list
    }

    OGCSpecificationRegistry o-- OGCRegisteredSpecification
    OGCRegisteredSpecification --> OGCSpecificationKey
```

### Version-Aware Validation Flow

```mermaid
sequenceDiagram
    participant Client
    participant StrategyRegistry
    participant OGCRegistry as OGCSpecificationRegistry
    participant Strategy

    Client->>StrategyRegistry: validate_against_spec(doc, spec_key, ogc_registry)
    StrategyRegistry->>StrategyRegistry: get(spec_key.api_type)
    StrategyRegistry->>Strategy: supports_version(spec_key.spec_version)
    Strategy-->>StrategyRegistry: true

    StrategyRegistry->>Strategy: validate(doc, conformance_classes)
    Strategy-->>StrategyRegistry: ValidationResult

    StrategyRegistry->>OGCRegistry: get(api_type, version, part)
    OGCRegistry-->>StrategyRegistry: OGCRegisteredSpecification

    StrategyRegistry->>StrategyRegistry: Compare paths with reference
    StrategyRegistry-->>Client: ValidationResult with warnings
```

### Specification Key Matching

The `OGCSpecificationKey` supports two matching modes:

| Mode | Description | Example |
|------|-------------|---------|
| Strict | Exact version and part match | `1.0` matches `1.0` only |
| Non-strict | Major.minor version match | `1.0` matches `1.0.1` |

## Protocols and Duck Typing

The library uses Python's `Protocol` classes to enable structural subtyping (duck typing). This allows custom implementations without inheritance.

### Protocol Hierarchy

```mermaid
classDiagram
    class ValidationStrategyProtocol {
        <<protocol>>
        +api_type: OGCAPIType
        +validate(document, conformance_classes) ValidationResult
        +get_required_paths(conformance_classes) list
        +get_required_operations(conformance_classes) dict
        +matches_conformance(conformance_classes) bool
    }

    class VersionAwareStrategyProtocol {
        <<protocol>>
        +supports_version(spec_version) bool
        +get_spec_version_from_conformance(conformance_classes) str
        +get_specification_key(conformance_classes) OGCSpecificationKey
    }

    class OpenAPIClientProtocol {
        <<protocol>>
        +fetch(url) tuple
        +fetch_and_validate_structure(url) tuple
    }

    class RegistryProtocol~K, V~ {
        <<protocol>>
        +get_by_key(key) V
        +exists_by_key(key) bool
        +remove_by_key(key) bool
        +list_keys() list~K~
        +clear() None
    }

    ValidationStrategyProtocol <|-- VersionAwareStrategyProtocol
    ValidationStrategy ..|> ValidationStrategyProtocol : implements
    ValidationStrategy ..|> VersionAwareStrategyProtocol : implements
```

### Runtime Checkable Protocols

All protocols are decorated with `@runtime_checkable`, enabling isinstance() checks:

```python
from ogcapi_registry import ValidationStrategyProtocol

class MyStrategy:
    api_type = OGCAPIType.FEATURES
    # ... implement required methods ...

# Works at runtime
assert isinstance(MyStrategy(), ValidationStrategyProtocol)
```

## Extension Points

The architecture supports several extension points:

### Custom Strategies

You have two options for creating custom strategies:

**Option 1: Inherit from ValidationStrategy (ABC)**

```python
class CustomStrategy(ValidationStrategy):
    api_type = OGCAPIType.CUSTOM  # Add to enum first
    required_conformance_patterns = ["my-custom-api"]

    def validate(self, document, conformance_classes):
        # Custom validation logic
        pass

    def get_required_paths(self, conformance_classes):
        return ["/custom-endpoint"]

    def get_required_operations(self, conformance_classes):
        return {"/custom-endpoint": ["get", "post"]}
```

**Option 2: Duck Typing with Protocol (No Inheritance)**

```python
class CustomStrategy:
    """No inheritance required - just implement the interface."""

    api_type = OGCAPIType.FEATURES

    def validate(self, document, conformance_classes):
        return ValidationResult.success()

    def get_required_paths(self, conformance_classes):
        return ["/custom-endpoint"]

    def get_required_operations(self, conformance_classes):
        return {"/custom-endpoint": ["get", "post"]}

    def matches_conformance(self, conformance_classes):
        return True

# Register without inheritance
registry = StrategyRegistry()
registry.register(CustomStrategy())  # Works!
```

### Custom Conformance Detection

Override `_infer_conformance_from_paths` in `StrategyRegistry` to add custom path-based detection.

### Pre/Post Validation Hooks

Wrap strategies or extend `CompositeValidationStrategy` to add hooks before/after validation.
