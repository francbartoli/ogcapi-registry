"""Tests for Protocol compliance and duck typing support."""

import pytest

from ogcapi_registry import (
    AsyncOpenAPIClient,
    CommonStrategy,
    ConformanceClass,
    FeaturesStrategy,
    OGCAPIType,
    OpenAPIClient,
    SpecificationRegistry,
    StrategyRegistry,
    ValidationResult,
    ValidationStrategy,
)
from ogcapi_registry.protocols import (
    AsyncOpenAPIClientProtocol,
    ConformanceClassProtocol,
    OpenAPIClientProtocol,
    RegistryProtocol,
    ValidationStrategyProtocol,
    VersionAwareStrategyProtocol,
)


class TestValidationStrategyProtocol:
    """Tests for ValidationStrategyProtocol duck typing support."""

    def test_builtin_strategies_satisfy_protocol(self) -> None:
        """Test that built-in strategies satisfy the protocol."""
        strategies = [
            CommonStrategy(),
            FeaturesStrategy(),
        ]

        for strategy in strategies:
            assert isinstance(strategy, ValidationStrategyProtocol)

    def test_builtin_strategies_satisfy_version_aware_protocol(self) -> None:
        """Test that built-in strategies satisfy the version-aware protocol."""
        strategy = FeaturesStrategy()
        assert isinstance(strategy, VersionAwareStrategyProtocol)

    def test_duck_typed_strategy_works(self) -> None:
        """Test that a duck-typed strategy (no inheritance) works."""

        class CustomStrategy:
            """A strategy that doesn't inherit from ValidationStrategy."""

            api_type = OGCAPIType.COMMON

            def validate(
                self,
                document: dict,
                conformance_classes: list,
            ) -> ValidationResult:
                return ValidationResult.success()

            def get_required_paths(self, conformance_classes: list) -> list:
                return ["/"]

            def get_required_operations(self, conformance_classes: list) -> dict:
                return {"/": ["get"]}

            def matches_conformance(self, conformance_classes: list) -> bool:
                return True

        custom = CustomStrategy()

        # Should satisfy the protocol
        assert isinstance(custom, ValidationStrategyProtocol)

        # Should work with StrategyRegistry
        registry = StrategyRegistry()
        registry.register(custom)

        # Verify it was registered
        assert registry.get(OGCAPIType.COMMON) is custom

    def test_duck_typed_strategy_validates_document(self) -> None:
        """Test that a duck-typed strategy can validate documents."""

        class MinimalFeaturesStrategy:
            """Minimal Features strategy without inheritance."""

            api_type = OGCAPIType.FEATURES

            def validate(
                self,
                document: dict,
                conformance_classes: list,
            ) -> ValidationResult:
                paths = document.get("paths", {})
                if "/collections" not in paths:
                    return ValidationResult.failure([{
                        "path": "paths",
                        "message": "Missing /collections path",
                        "type": "missing_path",
                    }])
                return ValidationResult.success()

            def get_required_paths(self, conformance_classes: list) -> list:
                return ["/collections"]

            def get_required_operations(self, conformance_classes: list) -> dict:
                return {"/collections": ["get"]}

            def matches_conformance(self, conformance_classes: list) -> bool:
                return any("features" in str(cc).lower() for cc in conformance_classes)

        registry = StrategyRegistry()
        registry.register(MinimalFeaturesStrategy())

        # Test validation with the custom strategy
        valid_doc = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {"/collections": {"get": {}}},
        }

        invalid_doc = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {},
        }

        ccs = [
            ConformanceClass(uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core")
        ]

        # Get the strategy and validate
        strategy = registry.get(OGCAPIType.FEATURES)
        assert strategy is not None

        result_valid = strategy.validate(valid_doc, ccs)
        assert result_valid.is_valid

        result_invalid = strategy.validate(invalid_doc, ccs)
        assert not result_invalid.is_valid


class TestConformanceClassProtocol:
    """Tests for ConformanceClassProtocol."""

    def test_conformance_class_satisfies_protocol(self) -> None:
        """Test that ConformanceClass satisfies its protocol."""
        cc = ConformanceClass(
            uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core"
        )
        assert isinstance(cc, ConformanceClassProtocol)

    def test_duck_typed_conformance_class(self) -> None:
        """Test that a duck-typed conformance class works."""

        class SimpleConformance:
            """Simple conformance class without inheritance."""

            def __init__(self, uri: str):
                self._uri = uri

            @property
            def uri(self) -> str:
                return self._uri

            @property
            def api_type(self) -> OGCAPIType:
                return OGCAPIType.COMMON

            @property
            def is_core(self) -> bool:
                return "core" in self._uri.lower()

        simple = SimpleConformance("http://example.com/conf/core")
        assert isinstance(simple, ConformanceClassProtocol)


class TestOpenAPIClientProtocol:
    """Tests for OpenAPIClientProtocol."""

    def test_sync_client_satisfies_protocol(self) -> None:
        """Test that OpenAPIClient satisfies the protocol."""
        client = OpenAPIClient()
        assert isinstance(client, OpenAPIClientProtocol)

    def test_async_client_satisfies_protocol(self) -> None:
        """Test that AsyncOpenAPIClient satisfies its protocol."""
        client = AsyncOpenAPIClient()
        assert isinstance(client, AsyncOpenAPIClientProtocol)


class TestRegistryProtocol:
    """Tests for RegistryProtocol."""

    def test_specification_registry_partial_protocol(self) -> None:
        """Test SpecificationRegistry methods align with protocol patterns.

        Note: SpecificationRegistry uses different method names (get vs get_by_key)
        so it doesn't directly satisfy RegistryProtocol, but follows similar patterns.
        """
        registry = SpecificationRegistry()

        # Has similar methods
        assert hasattr(registry, "clear")
        assert hasattr(registry, "list_keys")
        assert callable(getattr(registry, "__len__", None))
        assert callable(getattr(registry, "__contains__", None))


class TestProtocolRuntimeChecking:
    """Tests for runtime protocol checking with isinstance."""

    def test_runtime_checkable_works(self) -> None:
        """Test that @runtime_checkable protocols work with isinstance."""

        # This should work because ValidationStrategyProtocol is @runtime_checkable
        assert isinstance(CommonStrategy(), ValidationStrategyProtocol)

        # Non-conforming objects should fail
        class NotAStrategy:
            pass

        assert not isinstance(NotAStrategy(), ValidationStrategyProtocol)

    def test_incomplete_implementation_fails_check(self) -> None:
        """Test that incomplete implementations fail the protocol check."""

        class IncompleteStrategy:
            """Missing required methods."""

            api_type = OGCAPIType.COMMON

            def validate(self, document, conformance_classes):
                return ValidationResult.success()

            # Missing: get_required_paths, get_required_operations, matches_conformance

        incomplete = IncompleteStrategy()

        # Should NOT satisfy the protocol because methods are missing
        assert not isinstance(incomplete, ValidationStrategyProtocol)


class TestProtocolDocumentation:
    """Tests ensuring protocol documentation examples work."""

    def test_strategy_protocol_example(self) -> None:
        """Test the example from ValidationStrategyProtocol docstring."""

        class CustomStrategy:
            api_type = OGCAPIType.FEATURES

            def validate(self, document, conformance_classes):
                return ValidationResult.success()

            def get_required_paths(self, conformance_classes):
                return ["/collections"]

            def get_required_operations(self, conformance_classes):
                return {"/collections": ["get"]}

            def matches_conformance(self, conformance_classes):
                return True

        # Should work as documented
        strategy = CustomStrategy()
        assert isinstance(strategy, ValidationStrategyProtocol)

        # Should be usable with StrategyRegistry
        registry = StrategyRegistry()
        registry.register(strategy)
        assert registry.get(OGCAPIType.FEATURES) is strategy
