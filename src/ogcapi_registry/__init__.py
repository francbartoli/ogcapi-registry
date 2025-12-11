"""OGC API Registry - A library for validating OGC API OpenAPI documents.

This library provides:
- HTTP client for fetching remote OpenAPI specifications (JSON/YAML)
- In-memory registry for storing specifications as immutable Pydantic objects
- Validation functions for validating OpenAPI documents
- Strategy pattern for OGC API-specific validation based on conformance classes
"""

from .client import AsyncOpenAPIClient, OpenAPIClient
from .exceptions import (
    FetchError,
    OpenAPIRegistryError,
    ParseError,
    RegistryError,
    SpecificationAlreadyExistsError,
    SpecificationNotFoundError,
    ValidationError,
)
from .models import (
    ErrorSeverity,
    RegisteredSpecification,
    SpecificationKey,
    SpecificationMetadata,
    SpecificationType,
    ValidationResult,
)
from .ogc_registry import (
    OGC_SPEC_URLS,
    OGCRegisteredSpecification,
    OGCSpecificationRegistry,
    create_default_ogc_registry,
    populate_ogc_registry,
)
from .ogc_types import (
    CONFORMANCE_PATTERNS,
    ConformanceClass,
    OGCAPIType,
    OGCSpecificationKey,
    detect_api_types,
    get_primary_api_type,
    get_specification_keys,
    get_specification_versions,
    group_conformance_by_spec,
    parse_conformance_classes,
)
from .protocols import (
    AsyncOpenAPIClientProtocol,
    ConformanceClassProtocol,
    OpenAPIClientProtocol,
    RegistryProtocol,
    SpecificationKeyProtocol,
    ValidationStrategyProtocol,
    VersionAwareStrategyProtocol,
)
from .registry import AsyncSpecificationRegistry, SpecificationRegistry
from .strategies import (
    CommonStrategy,
    CompositeValidationStrategy,
    CoveragesStrategy,
    EDRStrategy,
    FeaturesStrategy,
    MapsStrategy,
    ProcessesStrategy,
    RecordsStrategy,
    RoutesStrategy,
    StylesStrategy,
    TilesStrategy,
    ValidationStrategy,
)
from .strategy_registry import (
    StrategyRegistry,
    get_default_registry,
    validate_ogc_api,
)
from .validator import (
    OpenAPIValidator,
    create_validator_with_specs,
    parse_openapi_content,
    validate_against_reference,
    validate_document,
    validate_openapi_structure,
    validate_openapi_with_pydantic,
)

__version__ = "0.3.0"

__all__ = [
    # Version
    "__version__",
    # Client
    "OpenAPIClient",
    "AsyncOpenAPIClient",
    # Registry
    "SpecificationRegistry",
    "AsyncSpecificationRegistry",
    # Models
    "ErrorSeverity",
    "SpecificationType",
    "SpecificationKey",
    "SpecificationMetadata",
    "RegisteredSpecification",
    "ValidationResult",
    # OGC Types
    "OGCAPIType",
    "OGCSpecificationKey",
    "ConformanceClass",
    "CONFORMANCE_PATTERNS",
    "parse_conformance_classes",
    "detect_api_types",
    "get_primary_api_type",
    "get_specification_keys",
    "get_specification_versions",
    "group_conformance_by_spec",
    # OGC Registry
    "OGCSpecificationRegistry",
    "OGCRegisteredSpecification",
    "OGC_SPEC_URLS",
    "create_default_ogc_registry",
    "populate_ogc_registry",
    # Strategies
    "ValidationStrategy",
    "CompositeValidationStrategy",
    "CommonStrategy",
    "FeaturesStrategy",
    "TilesStrategy",
    "ProcessesStrategy",
    "RecordsStrategy",
    "CoveragesStrategy",
    "EDRStrategy",
    "MapsStrategy",
    "StylesStrategy",
    "RoutesStrategy",
    # Strategy Registry
    "StrategyRegistry",
    "get_default_registry",
    "validate_ogc_api",
    # Validator
    "OpenAPIValidator",
    "validate_document",
    "validate_openapi_structure",
    "validate_openapi_with_pydantic",
    "validate_against_reference",
    "parse_openapi_content",
    "create_validator_with_specs",
    # Exceptions
    "OpenAPIRegistryError",
    "FetchError",
    "ParseError",
    "RegistryError",
    "SpecificationNotFoundError",
    "SpecificationAlreadyExistsError",
    "ValidationError",
    # Protocols (for duck typing)
    "ValidationStrategyProtocol",
    "VersionAwareStrategyProtocol",
    "RegistryProtocol",
    "OpenAPIClientProtocol",
    "AsyncOpenAPIClientProtocol",
    "ConformanceClassProtocol",
    "SpecificationKeyProtocol",
]
