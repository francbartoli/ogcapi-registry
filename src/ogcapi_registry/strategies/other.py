"""Validation strategies for other OGC API types."""

from typing import Any, ClassVar

from ..models import ValidationResult
from ..ogc_types import ConformanceClass, OGCAPIType
from .base import ValidationStrategy


class EDRStrategy(ValidationStrategy):
    """Validation strategy for OGC API - Environmental Data Retrieval."""

    api_type: ClassVar[OGCAPIType] = OGCAPIType.EDR
    required_conformance_patterns: ClassVar[list[str]] = [
        "ogcapi-edr",
        "/edr-",
    ]
    optional_conformance_patterns: ClassVar[list[str]] = [
        "/conf/collections",
        "/conf/queries",
        "/conf/position",
        "/conf/area",
        "/conf/cube",
        "/conf/trajectory",
        "/conf/corridor",
    ]

    def validate(
        self,
        document: dict[str, Any],
        conformance_classes: list[ConformanceClass],
    ) -> ValidationResult:
        errors: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []

        required_paths = self.get_required_paths(conformance_classes)
        errors.extend(self.validate_paths_exist(document, required_paths))

        required_ops = self.get_required_operations(conformance_classes)
        errors.extend(self.validate_operations_exist(document, required_ops))

        # Validate query endpoints based on conformance
        query_errors = self._validate_query_endpoints(document, conformance_classes)
        errors.extend(query_errors)

        if errors:
            return ValidationResult.failure(errors, warnings=tuple(warnings))
        return ValidationResult.success(warnings=tuple(warnings))

    def get_required_paths(
        self, conformance_classes: list[ConformanceClass]
    ) -> list[str]:
        paths = ["/", "/conformance", "/collections"]

        # Add query-specific paths based on conformance
        query_types = ["position", "area", "cube", "trajectory", "corridor"]
        for query in query_types:
            if self._has_conformance_class(conformance_classes, f"/conf/{query}"):
                paths.append(f"/collections/{{collectionId}}/{query}")

        return paths

    def get_required_operations(
        self, conformance_classes: list[ConformanceClass]
    ) -> dict[str, list[str]]:
        operations: dict[str, list[str]] = {
            "/": ["get"],
            "/conformance": ["get"],
            "/collections": ["get"],
        }

        query_types = ["position", "area", "cube", "trajectory", "corridor"]
        for query in query_types:
            if self._has_conformance_class(conformance_classes, f"/conf/{query}"):
                operations[f"/collections/{{collectionId}}/{query}"] = ["get"]

        return operations

    def _validate_query_endpoints(
        self,
        document: dict[str, Any],
        conformance_classes: list[ConformanceClass],
    ) -> list[dict[str, Any]]:
        errors: list[dict[str, Any]] = []
        paths = document.get("paths", {})

        query_types = ["position", "area", "cube", "trajectory", "corridor"]
        for query in query_types:
            if self._has_conformance_class(conformance_classes, f"/conf/{query}"):
                # Find matching path
                for path in paths:
                    if query in path and "{collectionId}" in path:
                        get_op = paths[path].get("get", {})
                        if get_op:
                            responses = get_op.get("responses", {})
                            if "200" not in responses and "2XX" not in responses:
                                errors.append(
                                    {
                                        "path": f"paths/{path}.get.responses",
                                        "message": f"EDR {query} query should have 200 response",
                                        "type": "missing_response",
                                    }
                                )
                        break

        return errors

    @staticmethod
    def _has_conformance_class(
        conformance_classes: list[ConformanceClass], pattern: str
    ) -> bool:
        pattern_lower = pattern.lower()
        return any(pattern_lower in cc.uri.lower() for cc in conformance_classes)


class CoveragesStrategy(ValidationStrategy):
    """Validation strategy for OGC API - Coverages."""

    api_type: ClassVar[OGCAPIType] = OGCAPIType.COVERAGES
    required_conformance_patterns: ClassVar[list[str]] = [
        "ogcapi-coverages",
        "/coverages-",
    ]
    optional_conformance_patterns: ClassVar[list[str]] = [
        "/conf/geodata-coverage",
        "/conf/coverage-subset",
        "/conf/coverage-rangesubset",
        "/conf/coverage-scaling",
    ]

    def validate(
        self,
        document: dict[str, Any],
        conformance_classes: list[ConformanceClass],
    ) -> ValidationResult:
        errors: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []

        required_paths = self.get_required_paths(conformance_classes)
        errors.extend(self.validate_paths_exist(document, required_paths))

        required_ops = self.get_required_operations(conformance_classes)
        errors.extend(self.validate_operations_exist(document, required_ops))

        if errors:
            return ValidationResult.failure(errors, warnings=tuple(warnings))
        return ValidationResult.success(warnings=tuple(warnings))

    def get_required_paths(
        self, conformance_classes: list[ConformanceClass]
    ) -> list[str]:
        paths = [
            "/",
            "/conformance",
            "/collections",
            "/collections/{collectionId}",
            "/collections/{collectionId}/coverage",
        ]
        return paths

    def get_required_operations(
        self, conformance_classes: list[ConformanceClass]
    ) -> dict[str, list[str]]:
        return {
            "/": ["get"],
            "/conformance": ["get"],
            "/collections": ["get"],
            "/collections/{collectionId}": ["get"],
            "/collections/{collectionId}/coverage": ["get"],
        }


class MapsStrategy(ValidationStrategy):
    """Validation strategy for OGC API - Maps."""

    api_type: ClassVar[OGCAPIType] = OGCAPIType.MAPS
    required_conformance_patterns: ClassVar[list[str]] = [
        "ogcapi-maps",
        "/maps-",
    ]
    optional_conformance_patterns: ClassVar[list[str]] = [
        "/conf/display-resolution",
        "/conf/spatial-subsetting",
        "/conf/scaling",
        "/conf/background",
    ]

    def validate(
        self,
        document: dict[str, Any],
        conformance_classes: list[ConformanceClass],
    ) -> ValidationResult:
        errors: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []

        required_paths = self.get_required_paths(conformance_classes)
        errors.extend(self.validate_paths_exist(document, required_paths))

        required_ops = self.get_required_operations(conformance_classes)
        errors.extend(self.validate_operations_exist(document, required_ops))

        if errors:
            return ValidationResult.failure(errors, warnings=tuple(warnings))
        return ValidationResult.success(warnings=tuple(warnings))

    def get_required_paths(
        self, conformance_classes: list[ConformanceClass]
    ) -> list[str]:
        paths = [
            "/",
            "/conformance",
            "/collections",
            "/collections/{collectionId}",
            "/collections/{collectionId}/map",
        ]
        return paths

    def get_required_operations(
        self, conformance_classes: list[ConformanceClass]
    ) -> dict[str, list[str]]:
        return {
            "/": ["get"],
            "/conformance": ["get"],
            "/collections": ["get"],
            "/collections/{collectionId}": ["get"],
            "/collections/{collectionId}/map": ["get"],
        }


class StylesStrategy(ValidationStrategy):
    """Validation strategy for OGC API - Styles."""

    api_type: ClassVar[OGCAPIType] = OGCAPIType.STYLES
    required_conformance_patterns: ClassVar[list[str]] = [
        "ogcapi-styles",
        "/styles-",
    ]
    optional_conformance_patterns: ClassVar[list[str]] = [
        "/conf/manage-styles",
        "/conf/style-validation",
    ]

    def validate(
        self,
        document: dict[str, Any],
        conformance_classes: list[ConformanceClass],
    ) -> ValidationResult:
        errors: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []

        required_paths = self.get_required_paths(conformance_classes)
        errors.extend(self.validate_paths_exist(document, required_paths))

        required_ops = self.get_required_operations(conformance_classes)
        errors.extend(self.validate_operations_exist(document, required_ops))

        if errors:
            return ValidationResult.failure(errors, warnings=tuple(warnings))
        return ValidationResult.success(warnings=tuple(warnings))

    def get_required_paths(
        self, conformance_classes: list[ConformanceClass]
    ) -> list[str]:
        paths = ["/", "/conformance", "/styles", "/styles/{styleId}"]

        if self._has_conformance_class(conformance_classes, "/conf/manage-styles"):
            # Management requires POST/PUT/DELETE
            pass

        return paths

    def get_required_operations(
        self, conformance_classes: list[ConformanceClass]
    ) -> dict[str, list[str]]:
        operations: dict[str, list[str]] = {
            "/": ["get"],
            "/conformance": ["get"],
            "/styles": ["get"],
            "/styles/{styleId}": ["get"],
        }

        if self._has_conformance_class(conformance_classes, "/conf/manage-styles"):
            operations["/styles"] = ["get", "post"]
            operations["/styles/{styleId}"] = ["get", "put", "delete"]

        return operations

    @staticmethod
    def _has_conformance_class(
        conformance_classes: list[ConformanceClass], pattern: str
    ) -> bool:
        pattern_lower = pattern.lower()
        return any(pattern_lower in cc.uri.lower() for cc in conformance_classes)


class RoutesStrategy(ValidationStrategy):
    """Validation strategy for OGC API - Routes."""

    api_type: ClassVar[OGCAPIType] = OGCAPIType.ROUTES
    required_conformance_patterns: ClassVar[list[str]] = [
        "ogcapi-routes",
        "/routes-",
    ]
    optional_conformance_patterns: ClassVar[list[str]] = []

    def validate(
        self,
        document: dict[str, Any],
        conformance_classes: list[ConformanceClass],
    ) -> ValidationResult:
        errors: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []

        required_paths = self.get_required_paths(conformance_classes)
        errors.extend(self.validate_paths_exist(document, required_paths))

        required_ops = self.get_required_operations(conformance_classes)
        errors.extend(self.validate_operations_exist(document, required_ops))

        if errors:
            return ValidationResult.failure(errors, warnings=tuple(warnings))
        return ValidationResult.success(warnings=tuple(warnings))

    def get_required_paths(
        self, conformance_classes: list[ConformanceClass]
    ) -> list[str]:
        return ["/", "/conformance", "/routes"]

    def get_required_operations(
        self, conformance_classes: list[ConformanceClass]
    ) -> dict[str, list[str]]:
        return {
            "/": ["get"],
            "/conformance": ["get"],
            "/routes": ["post"],
        }
