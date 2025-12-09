"""Validation strategy for OGC API - Records."""

from typing import Any, ClassVar

from ..models import ValidationResult
from ..ogc_types import ConformanceClass, OGCAPIType
from .base import ValidationStrategy


class RecordsStrategy(ValidationStrategy):
    """Validation strategy for OGC API - Records.

    Validates OpenAPI documents for compliance with the OGC API - Records
    specification (catalog/metadata services).
    """

    api_type: ClassVar[OGCAPIType] = OGCAPIType.RECORDS
    required_conformance_patterns: ClassVar[list[str]] = [
        "ogcapi-records",
        "/records-",
    ]
    optional_conformance_patterns: ClassVar[list[str]] = [
        "/conf/sorting",
        "/conf/cql-filter",
        "/conf/json",
        "/conf/html",
    ]

    def validate(
        self,
        document: dict[str, Any],
        conformance_classes: list[ConformanceClass],
    ) -> ValidationResult:
        """Validate an OpenAPI document for OGC API - Records compliance."""
        errors: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []

        required_paths = self.get_required_paths(conformance_classes)
        errors.extend(self.validate_paths_exist(document, required_paths))

        required_ops = self.get_required_operations(conformance_classes)
        errors.extend(self.validate_operations_exist(document, required_ops))

        # Validate records-specific requirements
        records_errors = self._validate_records_endpoint(document, conformance_classes)
        errors.extend(records_errors)

        if errors:
            return ValidationResult.failure(errors, warnings=tuple(warnings))

        return ValidationResult.success(warnings=tuple(warnings))

    def get_required_paths(
        self,
        conformance_classes: list[ConformanceClass],
    ) -> list[str]:
        """Get required paths for OGC API - Records."""
        return [
            "/",
            "/conformance",
            "/collections",
            "/collections/{catalogId}",
            "/collections/{catalogId}/items",
            "/collections/{catalogId}/items/{recordId}",
        ]

    def get_required_operations(
        self,
        conformance_classes: list[ConformanceClass],
    ) -> dict[str, list[str]]:
        """Get required operations for OGC API - Records paths."""
        return {
            "/": ["get"],
            "/conformance": ["get"],
            "/collections": ["get"],
            "/collections/{catalogId}": ["get"],
            "/collections/{catalogId}/items": ["get"],
            "/collections/{catalogId}/items/{recordId}": ["get"],
        }

    def _validate_records_endpoint(
        self,
        document: dict[str, Any],
        conformance_classes: list[ConformanceClass],
    ) -> list[dict[str, Any]]:
        """Validate records-specific requirements."""
        errors: list[dict[str, Any]] = []
        paths = document.get("paths", {})

        # Find items path for records
        for path in paths:
            if "/items" in path and "{" in path and "recordId" not in path:
                get_op = paths[path].get("get", {})
                if not get_op:
                    continue

                parameters = get_op.get("parameters", [])
                param_names = {
                    p.get("name", "") for p in parameters if isinstance(p, dict)
                }

                # Records should support q parameter for text search
                if "q" not in param_names:
                    errors.append(
                        {
                            "path": f"paths/{path}.get.parameters",
                            "message": "Records endpoint should have 'q' query parameter for text search",
                            "type": "missing_parameter",
                        }
                    )

        return errors

    @staticmethod
    def _has_conformance_class(
        conformance_classes: list[ConformanceClass],
        pattern: str,
    ) -> bool:
        pattern_lower = pattern.lower()
        return any(pattern_lower in cc.uri.lower() for cc in conformance_classes)
