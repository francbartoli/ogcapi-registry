"""Validation strategy for OGC API - Common."""

from typing import Any, ClassVar

from ..models import ErrorSeverity, ValidationResult
from ..ogc_types import ConformanceClass, OGCAPIType
from .base import ValidationStrategy


class CommonStrategy(ValidationStrategy):
    """Validation strategy for OGC API - Common.

    This is the base strategy that validates common requirements
    shared by all OGC API implementations.
    """

    api_type: ClassVar[OGCAPIType] = OGCAPIType.COMMON
    required_conformance_patterns: ClassVar[list[str]] = [
        "ogcapi-common",
        "/common-",
    ]
    optional_conformance_patterns: ClassVar[list[str]] = [
        "/conf/landing-page",
        "/conf/oas30",
        "/conf/html",
        "/conf/json",
    ]

    def validate(
        self,
        document: dict[str, Any],
        conformance_classes: list[ConformanceClass],
    ) -> ValidationResult:
        """Validate an OpenAPI document for OGC API - Common compliance.

        Args:
            document: The OpenAPI document to validate
            conformance_classes: Conformance classes declared by the implementation

        Returns:
            ValidationResult with validation outcome
        """
        errors: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []

        # Get required paths based on conformance classes
        required_paths = self.get_required_paths(conformance_classes)
        errors.extend(self.validate_paths_exist(document, required_paths))

        # Validate required operations
        required_ops = self.get_required_operations(conformance_classes)
        errors.extend(self.validate_operations_exist(document, required_ops))

        # Validate landing page response schema
        landing_page_errors = self._validate_landing_page(document)
        errors.extend(landing_page_errors)

        # Check for conformance endpoint
        if self._has_conformance_class(conformance_classes, "/conf/core"):
            conformance_errors = self._validate_conformance_endpoint(document)
            errors.extend(conformance_errors)

        if errors:
            return ValidationResult.failure(errors, warnings=tuple(warnings))

        return ValidationResult.success(warnings=tuple(warnings))

    def get_required_paths(
        self,
        conformance_classes: list[ConformanceClass],
    ) -> list[str]:
        """Get required paths for OGC API - Common.

        Args:
            conformance_classes: Conformance classes declared by the implementation

        Returns:
            List of required path patterns
        """
        paths = ["/"]  # Landing page is always required

        # Conformance endpoint required for core
        if self._has_conformance_class(conformance_classes, "/conf/core"):
            paths.append("/conformance")

        # API definition endpoint (usually /api)
        if self._has_conformance_class(conformance_classes, "/conf/oas30"):
            paths.append("/api")

        return paths

    def get_required_operations(
        self,
        conformance_classes: list[ConformanceClass],
    ) -> dict[str, list[str]]:
        """Get required operations for OGC API - Common paths.

        Args:
            conformance_classes: Conformance classes declared by the implementation

        Returns:
            Dict mapping paths to required HTTP methods
        """
        operations: dict[str, list[str]] = {
            "/": ["get"],
        }

        if self._has_conformance_class(conformance_classes, "/conf/core"):
            operations["/conformance"] = ["get"]

        return operations

    def _validate_landing_page(self, document: dict[str, Any]) -> list[dict[str, Any]]:
        """Validate the landing page endpoint.

        Args:
            document: The OpenAPI document

        Returns:
            List of validation errors
        """
        errors: list[dict[str, Any]] = []
        paths = document.get("paths", {})

        landing_page = paths.get("/", {})
        get_op = landing_page.get("get", {})

        if not get_op:
            return errors  # Path validation handles missing path

        # Check for 200 response
        responses = get_op.get("responses", {})
        if "200" not in responses and "2XX" not in responses:
            errors.append(
                self.create_error(
                    path="paths//.get.responses",
                    message="Landing page GET should have a 200 response",
                    error_type="missing_response",
                    severity=ErrorSeverity.CRITICAL,
                )
            )

        return errors

    def _validate_conformance_endpoint(
        self, document: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Validate the conformance endpoint.

        Args:
            document: The OpenAPI document

        Returns:
            List of validation errors
        """
        errors: list[dict[str, Any]] = []
        paths = document.get("paths", {})

        conformance = paths.get("/conformance", {})
        get_op = conformance.get("get", {})

        if not get_op:
            return errors  # Path validation handles missing path

        # Check for 200 response
        responses = get_op.get("responses", {})
        if "200" not in responses and "2XX" not in responses:
            errors.append(
                self.create_error(
                    path="paths//conformance.get.responses",
                    message="Conformance GET should have a 200 response",
                    error_type="missing_response",
                    severity=ErrorSeverity.CRITICAL,
                )
            )

        return errors

    @staticmethod
    def _has_conformance_class(
        conformance_classes: list[ConformanceClass],
        pattern: str,
    ) -> bool:
        """Check if a conformance class matching the pattern exists.

        Args:
            conformance_classes: List of conformance classes
            pattern: Pattern to match (substring)

        Returns:
            True if a matching conformance class exists
        """
        pattern_lower = pattern.lower()
        return any(pattern_lower in cc.uri.lower() for cc in conformance_classes)
