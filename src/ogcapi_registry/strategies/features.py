"""Validation strategy for OGC API - Features."""

from typing import Any, ClassVar

from ..models import ErrorSeverity, ValidationResult
from ..ogc_types import ConformanceClass, OGCAPIType
from .base import ValidationStrategy


class FeaturesStrategy(ValidationStrategy):
    """Validation strategy for OGC API - Features.

    Validates OpenAPI documents for compliance with the OGC API - Features
    specification, including Part 1 (Core), Part 2 (CRS), and Part 3 (Filtering).
    """

    api_type: ClassVar[OGCAPIType] = OGCAPIType.FEATURES
    required_conformance_patterns: ClassVar[list[str]] = [
        "ogcapi-features",
        "/features-",
    ]
    optional_conformance_patterns: ClassVar[list[str]] = [
        "/conf/geojson",
        "/conf/html",
        "/conf/crs",
        "/conf/filter",
        "/conf/features-filter",
    ]

    def validate(
        self,
        document: dict[str, Any],
        conformance_classes: list[ConformanceClass],
    ) -> ValidationResult:
        """Validate an OpenAPI document for OGC API - Features compliance.

        Args:
            document: The OpenAPI document to validate
            conformance_classes: Conformance classes declared by the implementation

        Returns:
            ValidationResult with validation outcome
        """
        errors: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []

        # Validate required paths
        required_paths = self.get_required_paths(conformance_classes)
        errors.extend(self.validate_paths_exist(document, required_paths))

        # Validate required operations
        required_ops = self.get_required_operations(conformance_classes)
        errors.extend(self.validate_operations_exist(document, required_ops))

        # Validate collections endpoint
        collections_errors = self._validate_collections_endpoint(document)
        errors.extend(collections_errors)

        # Validate items endpoint
        items_errors = self._validate_items_endpoint(document, conformance_classes)
        errors.extend(items_errors)

        # Validate CRS support if declared
        if self._has_conformance_class(conformance_classes, "/conf/crs"):
            crs_errors = self._validate_crs_support(document)
            errors.extend(crs_errors)

        # Validate filtering support if declared
        if self._has_conformance_class(conformance_classes, "/conf/filter"):
            filter_warnings = self._validate_filter_support(document)
            warnings.extend(filter_warnings)

        if errors:
            return ValidationResult.failure(errors, warnings=tuple(warnings))

        return ValidationResult.success(warnings=tuple(warnings))

    def get_required_paths(
        self,
        conformance_classes: list[ConformanceClass],
    ) -> list[str]:
        """Get required paths for OGC API - Features.

        Args:
            conformance_classes: Conformance classes declared by the implementation

        Returns:
            List of required path patterns
        """
        paths = [
            "/",
            "/conformance",
            "/collections",
            "/collections/{collectionId}",
            "/collections/{collectionId}/items",
            "/collections/{collectionId}/items/{featureId}",
        ]

        return paths

    def get_required_operations(
        self,
        conformance_classes: list[ConformanceClass],
    ) -> dict[str, list[str]]:
        """Get required operations for OGC API - Features paths.

        Args:
            conformance_classes: Conformance classes declared by the implementation

        Returns:
            Dict mapping paths to required HTTP methods
        """
        operations = {
            "/": ["get"],
            "/conformance": ["get"],
            "/collections": ["get"],
            "/collections/{collectionId}": ["get"],
            "/collections/{collectionId}/items": ["get"],
            "/collections/{collectionId}/items/{featureId}": ["get"],
        }

        return operations

    def _validate_collections_endpoint(
        self, document: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Validate the collections endpoint.

        Args:
            document: The OpenAPI document

        Returns:
            List of validation errors
        """
        errors: list[dict[str, Any]] = []
        paths = document.get("paths", {})

        collections = paths.get("/collections", {})
        get_op = collections.get("get", {})

        if not get_op:
            return errors

        # Check for 200 response
        responses = get_op.get("responses", {})
        if "200" not in responses and "2XX" not in responses:
            errors.append(
                self.create_error(
                    path="paths//collections.get.responses",
                    message="Collections GET should have a 200 response",
                    error_type="missing_response",
                    severity=ErrorSeverity.CRITICAL,
                )
            )

        return errors

    def _validate_items_endpoint(
        self,
        document: dict[str, Any],
        conformance_classes: list[ConformanceClass],
    ) -> list[dict[str, Any]]:
        """Validate the items endpoint.

        Args:
            document: The OpenAPI document
            conformance_classes: Conformance classes

        Returns:
            List of validation errors
        """
        errors: list[dict[str, Any]] = []
        paths = document.get("paths", {})

        # Find the items path
        items_path = None
        for path in paths:
            if "/items" in path and "{" in path and "featureId" not in path:
                items_path = path
                break

        if not items_path:
            return errors

        get_op = paths[items_path].get("get", {})
        if not get_op:
            return errors

        # Check for required query parameters
        parameters = get_op.get("parameters", [])
        param_names = set()

        for param in parameters:
            if isinstance(param, dict):
                param_names.add(param.get("name", ""))
            elif "$ref" in str(param):
                # Handle referenced parameters - add common ones
                pass

        # Features Core requires limit parameter (CRITICAL)
        if "limit" not in param_names:
            errors.append(
                self.create_error(
                    path=f"paths/{items_path}.get.parameters",
                    message="Items endpoint should have 'limit' query parameter",
                    error_type="missing_parameter",
                    severity=ErrorSeverity.CRITICAL,
                )
            )

        # Check for bbox parameter (recommended, not required - WARNING)
        if "bbox" not in param_names:
            errors.append(
                self.create_error(
                    path=f"paths/{items_path}.get.parameters",
                    message="Items endpoint should have 'bbox' query parameter for spatial filtering",
                    error_type="missing_parameter",
                    severity=ErrorSeverity.WARNING,
                )
            )

        return errors

    def _validate_crs_support(self, document: dict[str, Any]) -> list[dict[str, Any]]:
        """Validate CRS support for Features Part 2.

        Args:
            document: The OpenAPI document

        Returns:
            List of validation errors (WARNING level - optional conformance class)
        """
        errors: list[dict[str, Any]] = []
        paths = document.get("paths", {})

        # Find items path
        for path, path_item in paths.items():
            if "/items" in path and "{" in path:
                get_op = path_item.get("get", {})
                if not get_op:
                    continue

                parameters = get_op.get("parameters", [])
                param_names = {
                    p.get("name", "") for p in parameters if isinstance(p, dict)
                }

                # CRS Part 2 requires crs and bbox-crs parameters
                # These are WARNING because CRS is an optional conformance class
                if "crs" not in param_names:
                    errors.append(
                        self.create_error(
                            path=f"paths/{path}.get.parameters",
                            message="CRS conformance requires 'crs' query parameter",
                            error_type="missing_parameter",
                            severity=ErrorSeverity.WARNING,
                            conformance_class="http://www.opengis.net/spec/ogcapi-features-2/1.0/conf/crs",
                        )
                    )

                if "bbox-crs" not in param_names:
                    errors.append(
                        self.create_error(
                            path=f"paths/{path}.get.parameters",
                            message="CRS conformance requires 'bbox-crs' query parameter",
                            error_type="missing_parameter",
                            severity=ErrorSeverity.WARNING,
                            conformance_class="http://www.opengis.net/spec/ogcapi-features-2/1.0/conf/crs",
                        )
                    )

        return errors

    def _validate_filter_support(
        self, document: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Validate filtering support for Features Part 3.

        Args:
            document: The OpenAPI document

        Returns:
            List of validation warnings (INFO level - filtering details are complex)
        """
        warnings: list[dict[str, Any]] = []
        paths = document.get("paths", {})

        # Find items path
        for path, path_item in paths.items():
            if "/items" in path and "{" in path:
                get_op = path_item.get("get", {})
                if not get_op:
                    continue

                parameters = get_op.get("parameters", [])
                param_names = {
                    p.get("name", "") for p in parameters if isinstance(p, dict)
                }

                # Check for filter parameter (INFO level - informational)
                if "filter" not in param_names:
                    warnings.append(
                        self.create_error(
                            path=f"paths/{path}.get.parameters",
                            message="Filter conformance typically includes 'filter' query parameter",
                            error_type="missing_optional_parameter",
                            severity=ErrorSeverity.INFO,
                            conformance_class="http://www.opengis.net/spec/ogcapi-features-3/1.0/conf/filter",
                        )
                    )

                if "filter-lang" not in param_names:
                    warnings.append(
                        self.create_error(
                            path=f"paths/{path}.get.parameters",
                            message="Filter conformance typically includes 'filter-lang' query parameter",
                            error_type="missing_optional_parameter",
                            severity=ErrorSeverity.INFO,
                            conformance_class="http://www.opengis.net/spec/ogcapi-features-3/1.0/conf/filter",
                        )
                    )

        return warnings

    @staticmethod
    def _has_conformance_class(
        conformance_classes: list[ConformanceClass],
        pattern: str,
    ) -> bool:
        """Check if a conformance class matching the pattern exists."""
        pattern_lower = pattern.lower()
        return any(pattern_lower in cc.uri.lower() for cc in conformance_classes)
