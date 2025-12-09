"""Registry for validation strategies with auto-detection."""

from typing import TYPE_CHECKING, Any, cast

from .models import ValidationResult
from .strategies.base import ValidationStrategy
from .ogc_types import (
    ConformanceClass,
    OGCAPIType,
    OGCSpecificationKey,
    get_specification_keys,
    parse_conformance_classes,
)
from .protocols import ValidationStrategyProtocol
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
)

if TYPE_CHECKING:
    from .ogc_registry import OGCSpecificationRegistry


class StrategyRegistry:
    """Registry for OGC API validation strategies.

    This registry maintains a collection of validation strategies and
    provides auto-detection based on conformance classes.

    Supports duck typing: any object implementing ValidationStrategyProtocol
    can be registered, not just subclasses of ValidationStrategy.

    Example:
        class CustomStrategy:
            api_type = OGCAPIType.FEATURES

            def validate(self, document, conformance_classes):
                return ValidationResult.success()

            def get_required_paths(self, conformance_classes):
                return ["/collections"]

            def get_required_operations(self, conformance_classes):
                return {}

            def matches_conformance(self, conformance_classes):
                return True

        registry = StrategyRegistry()
        registry.register(CustomStrategy())  # Works without inheritance!
    """

    def __init__(self) -> None:
        """Initialize the registry with default strategies."""
        self._strategies: dict[OGCAPIType, ValidationStrategyProtocol] = {}
        self._register_default_strategies()

    def _register_default_strategies(self) -> None:
        """Register all default OGC API strategies."""
        self.register(CommonStrategy())
        self.register(FeaturesStrategy())
        self.register(TilesStrategy())
        self.register(ProcessesStrategy())
        self.register(RecordsStrategy())
        self.register(CoveragesStrategy())
        self.register(EDRStrategy())
        self.register(MapsStrategy())
        self.register(StylesStrategy())
        self.register(RoutesStrategy())

    def register(self, strategy: ValidationStrategyProtocol) -> None:
        """Register a validation strategy.

        Args:
            strategy: The strategy to register. Can be any object implementing
                     ValidationStrategyProtocol (duck typing supported).
        """
        self._strategies[strategy.api_type] = strategy

    def get(self, api_type: OGCAPIType) -> ValidationStrategyProtocol | None:
        """Get a strategy by API type.

        Args:
            api_type: The OGC API type

        Returns:
            The registered strategy, or None if not found
        """
        return self._strategies.get(api_type)

    def get_for_conformance(
        self,
        conformance_classes: list[ConformanceClass],
    ) -> ValidationStrategyProtocol:
        """Get the best strategy for the given conformance classes.

        If multiple strategies match, returns a CompositeValidationStrategy
        that combines all matching strategies.

        Args:
            conformance_classes: List of conformance classes

        Returns:
            The best matching strategy (may be composite)
        """
        matching_strategies: list[tuple[int, ValidationStrategyProtocol]] = []

        for strategy in self._strategies.values():
            if strategy.matches_conformance(conformance_classes):
                score = strategy.get_conformance_score(conformance_classes)
                matching_strategies.append((score, strategy))

        if not matching_strategies:
            # Fall back to CommonStrategy
            return self._strategies.get(OGCAPIType.COMMON, CommonStrategy())

        # Sort by score (highest first)
        matching_strategies.sort(key=lambda x: x[0], reverse=True)

        if len(matching_strategies) == 1:
            return matching_strategies[0][1]

        # Multiple matches - create composite strategy
        # Exclude CommonStrategy if we have more specific ones
        strategies = [
            s for _, s in matching_strategies if s.api_type != OGCAPIType.COMMON
        ]

        if not strategies:
            strategies = [matching_strategies[0][1]]

        if len(strategies) == 1:
            return strategies[0]

        # Cast to satisfy CompositeValidationStrategy type requirements
        return CompositeValidationStrategy(cast(list[ValidationStrategy], strategies))

    def detect_and_validate(
        self,
        document: dict[str, Any],
        conformance_classes: list[ConformanceClass]
        | list[str]
        | dict[str, Any]
        | None = None,
    ) -> ValidationResult:
        """Detect the appropriate strategy and validate a document.

        If conformance classes are not provided, attempts to extract them
        from the document's x-]conformance extension or paths.

        Args:
            document: The OpenAPI document to validate
            conformance_classes: Optional conformance classes (various formats)

        Returns:
            ValidationResult with validation outcome
        """
        # Parse conformance classes if needed
        cc_list: list[ConformanceClass]

        if conformance_classes is None:
            cc_list = self._extract_conformance_from_document(document)
        elif isinstance(conformance_classes, dict):
            cc_list = parse_conformance_classes(conformance_classes)
        elif conformance_classes and isinstance(conformance_classes[0], str):
            cc_list = parse_conformance_classes(conformance_classes)  # type: ignore
        else:
            cc_list = conformance_classes  # type: ignore

        # Get the appropriate strategy
        strategy = self.get_for_conformance(cc_list)

        # Validate
        return strategy.validate(document, cc_list)

    def _extract_conformance_from_document(
        self,
        document: dict[str, Any],
    ) -> list[ConformanceClass]:
        """Try to extract conformance classes from the document.

        Looks for:
        - x-conformance extension in info
        - Infers from paths structure

        Args:
            document: The OpenAPI document

        Returns:
            List of detected conformance classes
        """
        conformance_classes: list[ConformanceClass] = []

        # Check for x-conformance extension
        info = document.get("info", {})
        x_conformance = info.get("x-conformance", [])
        if x_conformance:
            conformance_classes.extend(parse_conformance_classes(x_conformance))

        # Also check top-level x-conformsTo
        x_conforms_to = document.get("x-conformsTo", [])
        if x_conforms_to:
            conformance_classes.extend(parse_conformance_classes(x_conforms_to))

        # If no conformance found, infer from paths
        if not conformance_classes:
            conformance_classes = self._infer_conformance_from_paths(document)

        return conformance_classes

    def _infer_conformance_from_paths(
        self,
        document: dict[str, Any],
    ) -> list[ConformanceClass]:
        """Infer conformance classes from the paths in the document.

        This is a heuristic approach when explicit conformance is not provided.

        Args:
            document: The OpenAPI document

        Returns:
            List of inferred conformance classes
        """
        paths = document.get("paths", {})
        path_set = set(paths.keys())

        inferred: list[ConformanceClass] = []

        # Always add common core if we have basic OGC API structure
        if "/" in path_set and "/conformance" in path_set:
            inferred.append(
                ConformanceClass(
                    uri="http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core"
                )
            )

        # Check for Features patterns
        has_collections = "/collections" in path_set
        has_items = any("/items" in p for p in path_set)
        if has_collections and has_items:
            # Check if it looks like Features (has featureId) vs Records (has recordId)
            has_feature_id = any("featureId" in p for p in path_set)
            has_record_id = any("recordId" in p for p in path_set)

            if has_feature_id or (not has_record_id and has_items):
                inferred.append(
                    ConformanceClass(
                        uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core"
                    )
                )

            if has_record_id:
                inferred.append(
                    ConformanceClass(
                        uri="http://www.opengis.net/spec/ogcapi-records-1/1.0/conf/core"
                    )
                )

        # Check for Tiles patterns
        has_tiles = any("/tiles" in p for p in path_set)
        has_tile_matrix = any("tileMatrix" in p for p in path_set)
        if has_tiles and has_tile_matrix:
            inferred.append(
                ConformanceClass(
                    uri="http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/core"
                )
            )

        # Check for Processes patterns
        has_processes = "/processes" in path_set
        has_execution = any("/execution" in p for p in path_set)
        if has_processes and has_execution:
            inferred.append(
                ConformanceClass(
                    uri="http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/core"
                )
            )

        # Check for Maps patterns
        has_map = any("/map" in p for p in path_set)
        if has_map and has_collections:
            inferred.append(
                ConformanceClass(
                    uri="http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/core"
                )
            )

        # Check for Coverages patterns
        has_coverage = any("/coverage" in p for p in path_set)
        if has_coverage and has_collections:
            inferred.append(
                ConformanceClass(
                    uri="http://www.opengis.net/spec/ogcapi-coverages-1/1.0/conf/core"
                )
            )

        # Check for EDR patterns
        edr_queries = ["position", "area", "cube", "trajectory", "corridor"]
        has_edr = any(any(q in p for q in edr_queries) for p in path_set)
        if has_edr and has_collections:
            inferred.append(
                ConformanceClass(
                    uri="http://www.opengis.net/spec/ogcapi-edr-1/1.0/conf/core"
                )
            )

        # Check for Styles patterns
        has_styles = "/styles" in path_set
        if has_styles:
            inferred.append(
                ConformanceClass(
                    uri="http://www.opengis.net/spec/ogcapi-styles-1/1.0/conf/core"
                )
            )

        # Check for Routes patterns
        has_routes = "/routes" in path_set
        if has_routes:
            inferred.append(
                ConformanceClass(
                    uri="http://www.opengis.net/spec/ogcapi-routes-1/1.0/conf/core"
                )
            )

        return inferred

    def list_strategies(self) -> list[ValidationStrategyProtocol]:
        """List all registered strategies.

        Returns:
            List of all registered strategies
        """
        return list(self._strategies.values())

    def list_api_types(self) -> list[OGCAPIType]:
        """List all registered API types.

        Returns:
            List of all registered API types
        """
        return list(self._strategies.keys())

    def validate_against_spec(
        self,
        document: dict[str, Any],
        spec_key: OGCSpecificationKey,
        ogc_registry: "OGCSpecificationRegistry",
        conformance_classes: list[ConformanceClass]
        | list[str]
        | dict[str, Any]
        | None = None,
    ) -> ValidationResult:
        """Validate a document against a specific OGC specification version.

        This method validates the document using:
        1. The appropriate strategy for the spec's API type
        2. Comparison with the reference specification from the OGC registry

        Args:
            document: The OpenAPI document to validate
            spec_key: The OGC specification key to validate against
            ogc_registry: Registry containing reference specifications
            conformance_classes: Optional conformance classes

        Returns:
            ValidationResult with validation outcome
        """

        # Parse conformance classes if needed
        cc_list: list[ConformanceClass]
        if conformance_classes is None:
            cc_list = self._extract_conformance_from_document(document)
        elif isinstance(conformance_classes, dict):
            cc_list = parse_conformance_classes(conformance_classes)
        elif conformance_classes and isinstance(conformance_classes[0], str):
            cc_list = parse_conformance_classes(conformance_classes)  # type: ignore
        else:
            cc_list = conformance_classes  # type: ignore

        # Get the strategy for the API type
        strategy = self.get(spec_key.api_type)
        if strategy is None:
            strategy = CommonStrategy()

        # Check version support
        if not strategy.supports_version(spec_key.spec_version):
            return ValidationResult.failure(
                [
                    {
                        "path": "",
                        "message": f"Strategy does not support version {spec_key.spec_version}",
                        "type": "unsupported_version",
                    }
                ]
            )

        # Validate using strategy
        result = strategy.validate(document, cc_list)

        # If reference spec is available, do additional path comparison
        try:
            ref_spec = ogc_registry.get(
                api_type=spec_key.api_type,
                spec_version=spec_key.spec_version,
                part=spec_key.part,
            )

            # Compare paths with reference
            ref_paths = set(ref_spec.paths.keys())
            doc_paths = set(document.get("paths", {}).keys())

            # Check for paths in ref that are not in document (potential missing required paths)
            additional_warnings = []
            for ref_path in ref_paths:
                # Only warn for paths that look like they might be required
                # (not template paths or obviously optional)
                if ref_path not in doc_paths and "{" not in ref_path:
                    additional_warnings.append(
                        {
                            "path": f"paths/{ref_path}",
                            "message": f"Path '{ref_path}' from reference spec not found",
                            "type": "missing_reference_path",
                        }
                    )

            # Add warnings to result if any
            if additional_warnings:
                all_warnings = list(result.warnings) + additional_warnings
                if result.is_valid:
                    return ValidationResult.success(
                        warnings=tuple(all_warnings),
                        validated_against=result.validated_against,
                    )
                else:
                    return ValidationResult.failure(
                        errors=list(result.errors),
                        warnings=tuple(all_warnings),
                        validated_against=result.validated_against,
                    )

        except Exception:
            # Reference spec not available, just return strategy result
            pass

        return result

    def get_detected_spec_keys(
        self,
        document: dict[str, Any],
        conformance_classes: list[ConformanceClass]
        | list[str]
        | dict[str, Any]
        | None = None,
    ) -> set[OGCSpecificationKey]:
        """Detect OGC specification keys from a document's conformance classes.

        Args:
            document: The OpenAPI document
            conformance_classes: Optional conformance classes

        Returns:
            Set of detected OGCSpecificationKey objects
        """
        # Parse conformance classes if needed
        cc_list: list[ConformanceClass]
        if conformance_classes is None:
            cc_list = self._extract_conformance_from_document(document)
        elif isinstance(conformance_classes, dict):
            cc_list = parse_conformance_classes(conformance_classes)
        elif conformance_classes and isinstance(conformance_classes[0], str):
            cc_list = parse_conformance_classes(conformance_classes)  # type: ignore
        else:
            cc_list = conformance_classes  # type: ignore

        return get_specification_keys(cc_list)


# Global default registry instance
_default_registry: StrategyRegistry | None = None


def get_default_registry() -> StrategyRegistry:
    """Get the default global strategy registry.

    Returns:
        The default StrategyRegistry instance
    """
    global _default_registry
    if _default_registry is None:
        _default_registry = StrategyRegistry()
    return _default_registry


def validate_ogc_api(
    document: dict[str, Any],
    conformance_classes: list[ConformanceClass]
    | list[str]
    | dict[str, Any]
    | None = None,
) -> ValidationResult:
    """Validate an OpenAPI document as an OGC API implementation.

    This is a convenience function that uses the default registry.

    Args:
        document: The OpenAPI document to validate
        conformance_classes: Optional conformance classes

    Returns:
        ValidationResult with validation outcome
    """
    registry = get_default_registry()
    return registry.detect_and_validate(document, conformance_classes)
