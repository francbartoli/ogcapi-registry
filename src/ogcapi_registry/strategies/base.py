"""Base classes and protocols for validation strategies."""

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from ..models import ValidationResult
from ..ogc_types import ConformanceClass, OGCAPIType


class ValidationStrategy(ABC):
    """Abstract base class for OGC API validation strategies.

    Each strategy implements validation logic specific to an OGC API type.
    Strategies are selected based on the conformance classes declared
    in the OpenAPI document.
    """

    # Class-level attributes to be overridden by subclasses
    api_type: ClassVar[OGCAPIType]
    required_conformance_patterns: ClassVar[list[str]] = []
    optional_conformance_patterns: ClassVar[list[str]] = []

    @abstractmethod
    def validate(
        self,
        document: dict[str, Any],
        conformance_classes: list[ConformanceClass],
    ) -> ValidationResult:
        """Validate an OpenAPI document according to this strategy.

        Args:
            document: The OpenAPI document to validate
            conformance_classes: Conformance classes declared by the implementation

        Returns:
            ValidationResult with validation outcome
        """
        ...

    @abstractmethod
    def get_required_paths(
        self,
        conformance_classes: list[ConformanceClass],
    ) -> list[str]:
        """Get the required API paths for this strategy.

        The required paths depend on which conformance classes are declared.

        Args:
            conformance_classes: Conformance classes declared by the implementation

        Returns:
            List of required path patterns (e.g., "/collections", "/conformance")
        """
        ...

    @abstractmethod
    def get_required_operations(
        self,
        conformance_classes: list[ConformanceClass],
    ) -> dict[str, list[str]]:
        """Get required operations for each path.

        Args:
            conformance_classes: Conformance classes declared by the implementation

        Returns:
            Dict mapping path patterns to required HTTP methods
            e.g., {"/collections": ["get"], "/collections/{collectionId}": ["get"]}
        """
        ...

    def matches_conformance(
        self,
        conformance_classes: list[ConformanceClass],
    ) -> bool:
        """Check if this strategy matches the given conformance classes.

        A strategy matches if at least one of its required conformance
        patterns is present in the conformance classes.

        Args:
            conformance_classes: Conformance classes to check

        Returns:
            True if this strategy should handle these conformance classes
        """
        if not self.required_conformance_patterns:
            return False

        cc_uris = {cc.uri.lower() for cc in conformance_classes}

        for pattern in self.required_conformance_patterns:
            pattern_lower = pattern.lower()
            # Check for exact match or pattern contained in URI
            for uri in cc_uris:
                if pattern_lower in uri or uri == pattern_lower:
                    return True

        return False

    def get_conformance_score(
        self,
        conformance_classes: list[ConformanceClass],
    ) -> int:
        """Calculate a score indicating how well this strategy matches.

        Higher scores indicate better matches. Used to select the best
        strategy when multiple strategies could apply.

        Args:
            conformance_classes: Conformance classes to score against

        Returns:
            Integer score (higher = better match)
        """
        score = 0
        cc_uris = {cc.uri.lower() for cc in conformance_classes}

        for pattern in self.required_conformance_patterns:
            pattern_lower = pattern.lower()
            for uri in cc_uris:
                if pattern_lower in uri:
                    score += 10  # Required patterns worth more

        for pattern in self.optional_conformance_patterns:
            pattern_lower = pattern.lower()
            for uri in cc_uris:
                if pattern_lower in uri:
                    score += 1  # Optional patterns worth less

        return score

    def validate_paths_exist(
        self,
        document: dict[str, Any],
        required_paths: list[str],
    ) -> list[dict[str, Any]]:
        """Check that required paths exist in the document.

        Args:
            document: The OpenAPI document
            required_paths: List of required path patterns

        Returns:
            List of error dicts for missing paths
        """
        errors: list[dict[str, Any]] = []
        paths = document.get("paths", {})

        for required_path in required_paths:
            # Handle path parameters like {collectionId}
            if "{" in required_path:
                # Check if any path matches the pattern
                pattern_found = False
                for path in paths:
                    if self._path_matches_pattern(path, required_path):
                        pattern_found = True
                        break
                if not pattern_found:
                    errors.append({
                        "path": f"paths/{required_path}",
                        "message": f"Required path pattern '{required_path}' not found",
                        "type": "missing_required_path",
                    })
            else:
                if required_path not in paths:
                    errors.append({
                        "path": f"paths/{required_path}",
                        "message": f"Required path '{required_path}' not found",
                        "type": "missing_required_path",
                    })

        return errors

    def validate_operations_exist(
        self,
        document: dict[str, Any],
        required_operations: dict[str, list[str]],
    ) -> list[dict[str, Any]]:
        """Check that required operations exist for paths.

        Args:
            document: The OpenAPI document
            required_operations: Dict mapping paths to required methods

        Returns:
            List of error dicts for missing operations
        """
        errors: list[dict[str, Any]] = []
        paths = document.get("paths", {})

        for path_pattern, methods in required_operations.items():
            # Find matching path(s)
            matching_paths = []
            for path in paths:
                if self._path_matches_pattern(path, path_pattern):
                    matching_paths.append(path)

            if not matching_paths:
                continue  # Path validation handles missing paths

            for path in matching_paths:
                path_item = paths.get(path, {})
                for method in methods:
                    if method.lower() not in path_item:
                        errors.append({
                            "path": f"paths/{path}/{method}",
                            "message": f"Required operation '{method.upper()}' not found for path '{path}'",
                            "type": "missing_required_operation",
                        })

        return errors

    @staticmethod
    def _path_matches_pattern(path: str, pattern: str) -> bool:
        """Check if a path matches a pattern with placeholders.

        Args:
            path: Actual path from OpenAPI document
            pattern: Pattern with {placeholder} syntax

        Returns:
            True if path matches the pattern
        """
        import re

        # Convert pattern to regex
        # Replace {anything} with a regex that matches path segments
        regex_pattern = re.sub(r"\{[^}]+\}", r"[^/]+", pattern)
        regex_pattern = f"^{regex_pattern}$"

        return bool(re.match(regex_pattern, path))


class CompositeValidationStrategy(ValidationStrategy):
    """A strategy that combines multiple sub-strategies.

    Use this when an implementation declares conformance to multiple
    OGC API types (e.g., Features + Tiles).
    """

    api_type: ClassVar[OGCAPIType] = OGCAPIType.COMMON

    def __init__(self, strategies: list[ValidationStrategy]) -> None:
        """Initialize with a list of sub-strategies.

        Args:
            strategies: List of strategies to combine
        """
        self._strategies = strategies

    @property
    def strategies(self) -> list[ValidationStrategy]:
        """Get the list of sub-strategies."""
        return self._strategies

    def validate(
        self,
        document: dict[str, Any],
        conformance_classes: list[ConformanceClass],
    ) -> ValidationResult:
        """Validate using all sub-strategies.

        Args:
            document: The OpenAPI document to validate
            conformance_classes: Conformance classes declared by the implementation

        Returns:
            Combined ValidationResult from all strategies
        """
        all_errors: list[dict[str, Any]] = []
        all_warnings: list[dict[str, Any]] = []

        for strategy in self._strategies:
            result = strategy.validate(document, conformance_classes)
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)

        if all_errors:
            return ValidationResult.failure(
                all_errors,
                warnings=tuple(all_warnings),
            )

        return ValidationResult.success(warnings=tuple(all_warnings))

    def get_required_paths(
        self,
        conformance_classes: list[ConformanceClass],
    ) -> list[str]:
        """Get combined required paths from all strategies."""
        paths: set[str] = set()
        for strategy in self._strategies:
            paths.update(strategy.get_required_paths(conformance_classes))
        return list(paths)

    def get_required_operations(
        self,
        conformance_classes: list[ConformanceClass],
    ) -> dict[str, list[str]]:
        """Get combined required operations from all strategies."""
        operations: dict[str, set[str]] = {}
        for strategy in self._strategies:
            for path, methods in strategy.get_required_operations(conformance_classes).items():
                if path not in operations:
                    operations[path] = set()
                operations[path].update(methods)
        return {path: list(methods) for path, methods in operations.items()}

    def matches_conformance(
        self,
        conformance_classes: list[ConformanceClass],
    ) -> bool:
        """Check if any sub-strategy matches."""
        return any(s.matches_conformance(conformance_classes) for s in self._strategies)
