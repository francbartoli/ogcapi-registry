"""OpenAPI Registry Validator - A library for validating OpenAPI v3 documents.

This library provides:
- HTTP client for fetching remote OpenAPI specifications (JSON/YAML)
- In-memory registry for storing specifications as immutable Pydantic objects
- Validation functions for validating OpenAPI documents
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
    RegisteredSpecification,
    SpecificationKey,
    SpecificationMetadata,
    SpecificationType,
    ValidationResult,
)
from .registry import AsyncSpecificationRegistry, SpecificationRegistry
from .validator import (
    OpenAPIValidator,
    create_validator_with_specs,
    parse_openapi_content,
    validate_against_reference,
    validate_document,
    validate_openapi_structure,
    validate_openapi_with_pydantic,
)

__version__ = "0.1.0"

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
    "SpecificationType",
    "SpecificationKey",
    "SpecificationMetadata",
    "RegisteredSpecification",
    "ValidationResult",
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
]
