"""Validation functions for OpenAPI documents."""

from typing import Any

import yaml
from openapi_pydantic import OpenAPI as OpenAPI31
from openapi_pydantic.v3.v3_0 import OpenAPI as OpenAPI30
from pydantic import ValidationError as PydanticValidationError

from .exceptions import ParseError
from .models import (
    RegisteredSpecification,
    SpecificationKey,
    SpecificationType,
    ValidationResult,
)
from .registry import SpecificationRegistry


def parse_openapi_content(
    content: str | bytes, format_hint: str | None = None
) -> dict[str, Any]:
    """Parse OpenAPI content from JSON or YAML string.

    Args:
        content: The content to parse (string or bytes)
        format_hint: Optional hint about format ('json' or 'yaml')

    Returns:
        Parsed content as a dictionary

    Raises:
        ParseError: If parsing fails
    """
    if isinstance(content, bytes):
        content = content.decode("utf-8")

    try:
        if format_hint == "json":
            import json

            return json.loads(content)
        elif format_hint == "yaml":
            return yaml.safe_load(content)
        else:
            # Try JSON first, fall back to YAML
            import json

            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return yaml.safe_load(content)
    except Exception as e:
        raise ParseError(f"Failed to parse content: {e}")


def validate_openapi_structure(
    document: dict[str, Any],
    target_version: SpecificationType | None = None,
) -> ValidationResult:
    """Validate the basic structure of an OpenAPI document.

    This performs initial checks on the OpenAPI document structure
    before full Pydantic validation.

    Args:
        document: The OpenAPI document to validate
        target_version: Expected OpenAPI version type (inferred if not provided)

    Returns:
        ValidationResult with validation outcome
    """
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    # Check for openapi field
    if "openapi" not in document:
        errors.append(
            {
                "path": "openapi",
                "message": "Missing required 'openapi' field",
                "type": "missing_required",
            }
        )
        return ValidationResult.failure(errors)

    openapi_version = document["openapi"]
    if not isinstance(openapi_version, str):
        errors.append(
            {
                "path": "openapi",
                "message": "'openapi' field must be a string",
                "type": "invalid_type",
            }
        )
        return ValidationResult.failure(errors)

    # Determine target version
    try:
        detected_type = SpecificationType.from_version(openapi_version)
    except ValueError:
        errors.append(
            {
                "path": "openapi",
                "message": f"Unsupported OpenAPI version: {openapi_version}",
                "type": "unsupported_version",
            }
        )
        return ValidationResult.failure(errors)

    if target_version and detected_type != target_version:
        warnings.append(
            {
                "path": "openapi",
                "message": f"Expected {target_version.value} but found {detected_type.value}",
                "type": "version_mismatch",
            }
        )

    # Check for required fields based on version
    if detected_type == SpecificationType.OPENAPI_3_0:
        # OpenAPI 3.0.x requires paths
        if "paths" not in document:
            errors.append(
                {
                    "path": "paths",
                    "message": "Missing required 'paths' field for OpenAPI 3.0.x",
                    "type": "missing_required",
                }
            )
    # OpenAPI 3.1.x doesn't require paths (can use webhooks instead)

    # Check for info field (required in both versions)
    if "info" not in document:
        errors.append(
            {
                "path": "info",
                "message": "Missing required 'info' field",
                "type": "missing_required",
            }
        )
    elif isinstance(document.get("info"), dict):
        info = document["info"]
        if "title" not in info:
            errors.append(
                {
                    "path": "info/title",
                    "message": "Missing required 'title' field in info",
                    "type": "missing_required",
                }
            )
        if "version" not in info:
            errors.append(
                {
                    "path": "info/version",
                    "message": "Missing required 'version' field in info",
                    "type": "missing_required",
                }
            )

    key = SpecificationKey(spec_type=detected_type, version=openapi_version)

    if errors:
        return ValidationResult.failure(
            errors, validated_against=key, warnings=tuple(warnings)
        )
    return ValidationResult.success(validated_against=key, warnings=tuple(warnings))


def validate_openapi_with_pydantic(
    document: dict[str, Any],
) -> ValidationResult:
    """Validate an OpenAPI document using Pydantic models.

    This provides comprehensive validation using the openapi-pydantic library,
    which supports both OpenAPI 3.0.x and 3.1.x versions.

    Args:
        document: The OpenAPI document to validate

    Returns:
        ValidationResult with validation outcome
    """
    errors: list[dict[str, Any]] = []

    # Determine version for the key
    openapi_version = document.get("openapi", "")
    try:
        spec_type = SpecificationType.from_version(openapi_version)
        key = SpecificationKey(spec_type=spec_type, version=openapi_version)
    except ValueError:
        # If we can't determine version, skip Pydantic validation
        return ValidationResult.success()

    # Validate with appropriate OpenAPI model based on version
    try:
        if spec_type == SpecificationType.OPENAPI_3_0:
            OpenAPI30.model_validate(document)
        else:
            OpenAPI31.model_validate(document)
    except PydanticValidationError as e:
        for error in e.errors():
            loc = "/".join(str(p) for p in error["loc"]) or "/"
            errors.append(
                {
                    "path": loc,
                    "message": error["msg"],
                    "type": error["type"],
                }
            )

    if errors:
        return ValidationResult.failure(errors, validated_against=key)

    return ValidationResult.success(validated_against=key)


def validate_against_reference(
    document: dict[str, Any],
    reference: RegisteredSpecification,
    strict: bool = False,
) -> ValidationResult:
    """Validate an OpenAPI document against a reference specification.

    This validates that the document conforms to the same OpenAPI version
    and structure as the reference specification.

    Args:
        document: The OpenAPI document to validate
        reference: The reference specification to validate against
        strict: If True, require exact version match

    Returns:
        ValidationResult with validation outcome
    """
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    # Check OpenAPI version compatibility
    doc_version = document.get("openapi", "")
    ref_version = reference.openapi_version

    if not doc_version:
        errors.append(
            {
                "path": "openapi",
                "message": "Missing 'openapi' version field",
                "type": "missing_required",
            }
        )
        return ValidationResult.failure(errors, validated_against=reference.key)

    try:
        doc_type = SpecificationType.from_version(doc_version)
        ref_type = reference.key.spec_type

        if strict and doc_version != ref_version:
            errors.append(
                {
                    "path": "openapi",
                    "message": f"Version mismatch: expected {ref_version}, got {doc_version}",
                    "type": "version_mismatch",
                }
            )
        elif doc_type != ref_type:
            errors.append(
                {
                    "path": "openapi",
                    "message": f"Incompatible OpenAPI type: expected {ref_type.value}, got {doc_type.value}",
                    "type": "type_mismatch",
                }
            )
    except ValueError as e:
        errors.append(
            {
                "path": "openapi",
                "message": str(e),
                "type": "unsupported_version",
            }
        )

    if errors:
        return ValidationResult.failure(
            errors, validated_against=reference.key, warnings=tuple(warnings)
        )

    # Perform structural validation
    structure_result = validate_openapi_structure(document, reference.key.spec_type)

    if not structure_result.is_valid:
        return ValidationResult.failure(
            list(structure_result.errors),
            validated_against=reference.key,
            warnings=tuple(list(structure_result.warnings) + warnings),
        )

    # Perform Pydantic validation
    pydantic_result = validate_openapi_with_pydantic(document)

    if not pydantic_result.is_valid:
        return ValidationResult.failure(
            list(pydantic_result.errors),
            validated_against=reference.key,
            warnings=tuple(list(structure_result.warnings) + warnings),
        )

    all_warnings = tuple(
        list(structure_result.warnings) + list(pydantic_result.warnings) + warnings
    )
    return ValidationResult.success(
        validated_against=reference.key, warnings=all_warnings
    )


def validate_document(
    document: dict[str, Any] | str | bytes,
    format_hint: str | None = None,
) -> ValidationResult:
    """Validate an OpenAPI document.

    This is a convenience function that parses and validates in one step.

    Args:
        document: The document to validate (dict, JSON string, or YAML string)
        format_hint: Optional hint about format ('json' or 'yaml')

    Returns:
        ValidationResult with validation outcome
    """
    if isinstance(document, (str, bytes)):
        try:
            document = parse_openapi_content(document, format_hint)
        except ParseError as e:
            return ValidationResult.failure(
                [
                    {
                        "path": "/",
                        "message": str(e),
                        "type": "parse_error",
                    }
                ]
            )

    # First validate structure
    structure_result = validate_openapi_structure(document)
    if not structure_result.is_valid:
        return structure_result

    # Then validate with Pydantic
    pydantic_result = validate_openapi_with_pydantic(document)
    if not pydantic_result.is_valid:
        return ValidationResult.failure(
            list(pydantic_result.errors),
            validated_against=structure_result.validated_against,
            warnings=structure_result.warnings,
        )

    return ValidationResult.success(
        validated_against=structure_result.validated_against,
        warnings=tuple(
            list(structure_result.warnings) + list(pydantic_result.warnings)
        ),
    )


class OpenAPIValidator:
    """Validator that uses a registry of reference specifications.

    This class provides validation methods that can validate documents
    against specifications stored in a registry.
    """

    def __init__(self, registry: SpecificationRegistry | None = None) -> None:
        """Initialize the validator.

        Args:
            registry: Optional registry to use. If not provided, a new one is created.
        """
        self._registry = registry or SpecificationRegistry()

    @property
    def registry(self) -> SpecificationRegistry:
        """Get the underlying registry."""
        return self._registry

    def validate(
        self,
        document: dict[str, Any] | str | bytes,
        format_hint: str | None = None,
    ) -> ValidationResult:
        """Validate an OpenAPI document.

        Args:
            document: The document to validate
            format_hint: Optional format hint ('json' or 'yaml')

        Returns:
            ValidationResult with validation outcome
        """
        return validate_document(document, format_hint)

    def validate_against(
        self,
        document: dict[str, Any] | str | bytes,
        spec_type: SpecificationType,
        version: str,
        strict: bool = False,
        format_hint: str | None = None,
    ) -> ValidationResult:
        """Validate a document against a specific registered specification.

        Args:
            document: The document to validate
            spec_type: Type of reference specification
            version: Version of reference specification
            strict: If True, require exact version match
            format_hint: Optional format hint

        Returns:
            ValidationResult with validation outcome

        Raises:
            SpecificationNotFoundError: If reference specification not found
        """
        if isinstance(document, (str, bytes)):
            try:
                document = parse_openapi_content(document, format_hint)
            except ParseError as e:
                return ValidationResult.failure(
                    [
                        {
                            "path": "/",
                            "message": str(e),
                            "type": "parse_error",
                        }
                    ]
                )

        reference = self._registry.get(spec_type, version)
        return validate_against_reference(document, reference, strict=strict)

    def validate_against_latest(
        self,
        document: dict[str, Any] | str | bytes,
        spec_type: SpecificationType,
        strict: bool = False,
        format_hint: str | None = None,
    ) -> ValidationResult:
        """Validate a document against the latest version of a specification type.

        Args:
            document: The document to validate
            spec_type: Type of reference specification
            strict: If True, require exact version match
            format_hint: Optional format hint

        Returns:
            ValidationResult with validation outcome

        Raises:
            SpecificationNotFoundError: If no specifications of this type exist
        """
        # Find latest version for this type
        specs = [
            s
            for s in self._registry.list_specifications()
            if s.key.spec_type == spec_type
        ]

        if not specs:
            from .exceptions import SpecificationNotFoundError

            raise SpecificationNotFoundError(spec_type.value, "any")

        # Sort by version and get latest
        specs.sort(key=lambda s: s.key.version, reverse=True)
        latest = specs[0]

        if isinstance(document, (str, bytes)):
            try:
                document = parse_openapi_content(document, format_hint)
            except ParseError as e:
                return ValidationResult.failure(
                    [
                        {
                            "path": "/",
                            "message": str(e),
                            "type": "parse_error",
                        }
                    ]
                )

        return validate_against_reference(document, latest, strict=strict)


def create_validator_with_specs(
    *urls: str,
) -> OpenAPIValidator:
    """Create a validator pre-loaded with specifications from URLs.

    Args:
        *urls: URLs of OpenAPI specifications to load

    Returns:
        OpenAPIValidator with loaded specifications
    """
    registry = SpecificationRegistry()
    for url in urls:
        registry.register_from_url(url, overwrite=True)
    return OpenAPIValidator(registry)
