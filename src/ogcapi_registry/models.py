"""Immutable Pydantic models for OpenAPI specifications."""

from datetime import datetime
from enum import Enum
from typing import Any

from openapi_pydantic import OpenAPI as OpenAPI31
from openapi_pydantic.v3.v3_0 import OpenAPI as OpenAPI30
from pydantic import BaseModel, Field


class ErrorSeverity(str, Enum):
    """Severity levels for validation errors.

    Used to distinguish between critical errors that must be fixed
    and informational warnings that may be acceptable.
    """

    CRITICAL = "critical"
    """Critical errors that violate required OGC conformance classes.
    These must be fixed for the API to be considered compliant."""

    WARNING = "warning"
    """Warnings for optional conformance class violations.
    The API may still be functional without addressing these."""

    INFO = "info"
    """Informational messages about best practices or recommendations.
    These do not affect compliance status."""


class SpecificationType(str, Enum):
    """Enumeration of supported OpenAPI specification types."""

    OPENAPI_3_0 = "openapi-3.0"
    OPENAPI_3_1 = "openapi-3.1"

    @classmethod
    def from_version(cls, version: str) -> "SpecificationType":
        """Determine specification type from OpenAPI version string.

        Args:
            version: OpenAPI version string (e.g., "3.0.3", "3.1.0")

        Returns:
            The corresponding SpecificationType

        Raises:
            ValueError: If the version is not supported
        """
        if version.startswith("3.0"):
            return cls.OPENAPI_3_0
        elif version.startswith("3.1"):
            return cls.OPENAPI_3_1
        else:
            raise ValueError(f"Unsupported OpenAPI version: {version}")


class SpecificationKey(BaseModel):
    """Unique key for identifying a specification in the registry.

    This is an immutable model that serves as a composite key.
    """

    model_config = {"frozen": True}

    spec_type: SpecificationType = Field(
        ..., description="Type of the OpenAPI specification"
    )
    version: str = Field(
        ..., description="Semantic version of the specification (e.g., '3.0.3')"
    )

    def __hash__(self) -> int:
        return hash((self.spec_type, self.version))


class SpecificationMetadata(BaseModel):
    """Metadata about a stored OpenAPI specification.

    This is an immutable model containing information about when and where
    the specification was fetched from.
    """

    model_config = {"frozen": True}

    source_url: str | None = Field(
        None,
        description="Original URL from which the specification was fetched",
    )
    fetched_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the specification was fetched",
    )
    content_type: str | None = Field(
        None, description="Original content type (e.g., 'application/json')"
    )
    etag: str | None = Field(None, description="ETag header from the HTTP response")


class RegisteredSpecification(BaseModel):
    """An immutable OpenAPI specification stored in the registry.

    This model wraps the OpenAPI specification with its key and metadata,
    making the entire object immutable for thread-safe registry operations.
    """

    model_config = {"frozen": True}

    key: SpecificationKey = Field(..., description="Unique identifier for this spec")
    metadata: SpecificationMetadata = Field(
        ..., description="Metadata about the specification"
    )
    raw_content: dict[str, Any] = Field(
        ..., description="Raw parsed content of the specification"
    )

    @property
    def openapi_version(self) -> str:
        """Get the OpenAPI version string from the raw content."""
        return str(self.raw_content.get("openapi", ""))

    @property
    def info_title(self) -> str | None:
        """Get the API title from the specification."""
        info = self.raw_content.get("info", {})
        return info.get("title")

    @property
    def info_version(self) -> str | None:
        """Get the API version from the specification."""
        info = self.raw_content.get("info", {})
        return info.get("version")

    def to_openapi(self) -> OpenAPI31 | OpenAPI30:
        """Convert to an openapi-pydantic OpenAPI model.

        Returns:
            An OpenAPI model instance (OpenAPI30 for 3.0.x, OpenAPI31 for 3.1.x)

        Note:
            This creates a new OpenAPI instance on each call for safety.
        """
        if self.key.spec_type == SpecificationType.OPENAPI_3_0:
            return OpenAPI30.model_validate(self.raw_content)
        return OpenAPI31.model_validate(self.raw_content)


class ValidationResult(BaseModel):
    """Result of validating an OpenAPI document.

    This is an immutable model representing the outcome of a validation
    operation.
    """

    model_config = {"frozen": True}

    is_valid: bool = Field(..., description="Whether the document is valid")
    errors: tuple[dict[str, Any], ...] = Field(
        default=(), description="List of validation errors, if any"
    )
    warnings: tuple[dict[str, Any], ...] = Field(
        default=(), description="List of validation warnings, if any"
    )
    validated_against: SpecificationKey | None = Field(
        None, description="The specification key used for validation"
    )

    @classmethod
    def success(
        cls,
        validated_against: SpecificationKey | None = None,
        warnings: tuple[dict[str, Any], ...] = (),
    ) -> "ValidationResult":
        """Create a successful validation result."""
        return cls(
            is_valid=True,
            errors=(),
            warnings=warnings,
            validated_against=validated_against,
        )

    @classmethod
    def failure(
        cls,
        errors: list[dict[str, Any]],
        validated_against: SpecificationKey | None = None,
        warnings: tuple[dict[str, Any], ...] = (),
    ) -> "ValidationResult":
        """Create a failed validation result."""
        return cls(
            is_valid=False,
            errors=tuple(errors),
            warnings=warnings,
            validated_against=validated_against,
        )

    def get_errors_by_severity(
        self, severity: "ErrorSeverity"
    ) -> tuple[dict[str, Any], ...]:
        """Get errors filtered by severity level.

        Args:
            severity: The severity level to filter by

        Returns:
            Tuple of error dicts matching the severity
        """
        return tuple(
            error for error in self.errors if error.get("severity") == severity.value
        )

    @property
    def critical_errors(self) -> tuple[dict[str, Any], ...]:
        """Get only critical errors that must be fixed."""
        return self.get_errors_by_severity(ErrorSeverity.CRITICAL)

    @property
    def warning_errors(self) -> tuple[dict[str, Any], ...]:
        """Get only warning-level errors for optional conformance."""
        return self.get_errors_by_severity(ErrorSeverity.WARNING)

    @property
    def info_errors(self) -> tuple[dict[str, Any], ...]:
        """Get only informational errors."""
        return self.get_errors_by_severity(ErrorSeverity.INFO)

    @property
    def has_critical_errors(self) -> bool:
        """Check if there are any critical errors."""
        return len(self.critical_errors) > 0

    @property
    def is_compliant(self) -> bool:
        """Check if the document is compliant (no critical errors).

        A document is considered compliant if it has no critical errors,
        even if it has warnings or informational messages. This is different
        from is_valid which requires zero errors of any kind.
        """
        return not self.has_critical_errors

    def get_summary(self) -> dict[str, int]:
        """Get a summary of errors by severity.

        Returns:
            Dict with counts for each severity level
        """
        return {
            "critical": len(self.critical_errors),
            "warning": len(self.warning_errors),
            "info": len(self.info_errors),
            "total": len(self.errors),
        }
