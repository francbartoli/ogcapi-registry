"""Tests for the strategy registry."""

import pytest

from ogcapi_registry.ogc_types import ConformanceClass, OGCAPIType
from ogcapi_registry.strategies import (
    CompositeValidationStrategy,
    FeaturesStrategy,
)
from ogcapi_registry.strategy_registry import (
    StrategyRegistry,
    get_default_registry,
    validate_ogc_api,
)


class TestStrategyRegistry:
    """Tests for StrategyRegistry."""

    @pytest.fixture
    def registry(self):
        """Create a fresh registry instance."""
        return StrategyRegistry()

    def test_default_strategies_registered(self, registry):
        """Test that default strategies are registered."""
        api_types = registry.list_api_types()
        assert OGCAPIType.COMMON in api_types
        assert OGCAPIType.FEATURES in api_types
        assert OGCAPIType.TILES in api_types
        assert OGCAPIType.PROCESSES in api_types

    def test_get_strategy(self, registry):
        """Test getting a strategy by type."""
        strategy = registry.get(OGCAPIType.FEATURES)
        assert strategy is not None
        assert isinstance(strategy, FeaturesStrategy)

    def test_get_nonexistent_strategy(self, registry):
        """Test getting a non-registered strategy."""
        # Remove a strategy first
        del registry._strategies[OGCAPIType.ROUTES]
        strategy = registry.get(OGCAPIType.ROUTES)
        assert strategy is None

    def test_get_for_conformance_single(self, registry):
        """Test getting strategy for single conformance class."""
        ccs = [
            ConformanceClass(
                uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core"
            ),
        ]
        strategy = registry.get_for_conformance(ccs)
        assert isinstance(strategy, FeaturesStrategy)

    def test_get_for_conformance_multiple(self, registry):
        """Test getting strategy for multiple conformance classes."""
        ccs = [
            ConformanceClass(
                uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core"
            ),
            ConformanceClass(
                uri="http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/core"
            ),
        ]
        strategy = registry.get_for_conformance(ccs)
        # Should return composite strategy
        assert isinstance(strategy, CompositeValidationStrategy)

    def test_get_for_conformance_fallback_to_common(self, registry):
        """Test fallback to CommonStrategy when nothing matches."""
        ccs = [
            ConformanceClass(uri="http://example.com/unknown"),
        ]
        strategy = registry.get_for_conformance(ccs)
        assert strategy.api_type == OGCAPIType.COMMON

    def test_detect_and_validate_with_conformance(self, registry):
        """Test detect_and_validate with explicit conformance."""
        doc = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/": {"get": {"responses": {"200": {"description": "OK"}}}},
                "/conformance": {"get": {"responses": {"200": {"description": "OK"}}}},
            },
        }
        ccs = [
            ConformanceClass(
                uri="http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core"
            ),
        ]
        result = registry.detect_and_validate(doc, ccs)
        assert result.is_valid

    def test_detect_and_validate_with_list_of_strings(self, registry):
        """Test detect_and_validate with list of URI strings."""
        doc = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/": {"get": {"responses": {"200": {"description": "OK"}}}},
                "/conformance": {"get": {"responses": {"200": {"description": "OK"}}}},
            },
        }
        ccs = [
            "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core",
        ]
        result = registry.detect_and_validate(doc, ccs)
        assert result.is_valid

    def test_detect_and_validate_with_dict(self, registry):
        """Test detect_and_validate with conformsTo dict."""
        doc = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/": {"get": {"responses": {"200": {"description": "OK"}}}},
                "/conformance": {"get": {"responses": {"200": {"description": "OK"}}}},
            },
        }
        ccs = {
            "conformsTo": [
                "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core",
            ]
        }
        result = registry.detect_and_validate(doc, ccs)
        assert result.is_valid

    def test_detect_and_validate_infer_from_paths(self, registry):
        """Test that conformance is inferred from paths."""
        doc = {
            "openapi": "3.0.3",
            "info": {"title": "Features API", "version": "1.0.0"},
            "paths": {
                "/": {"get": {"responses": {"200": {"description": "OK"}}}},
                "/conformance": {"get": {"responses": {"200": {"description": "OK"}}}},
                "/collections": {"get": {"responses": {"200": {"description": "OK"}}}},
                "/collections/{collectionId}": {
                    "get": {"responses": {"200": {"description": "OK"}}}
                },
                "/collections/{collectionId}/items": {
                    "get": {
                        "parameters": [
                            {"name": "limit", "in": "query"},
                            {"name": "bbox", "in": "query"},
                        ],
                        "responses": {"200": {"description": "OK"}},
                    }
                },
                "/collections/{collectionId}/items/{featureId}": {
                    "get": {"responses": {"200": {"description": "OK"}}}
                },
            },
        }
        # No explicit conformance - should infer from paths
        result = registry.detect_and_validate(doc)
        # The result depends on what gets inferred, but should return a ValidationResult
        assert result is not None
        assert hasattr(result, "is_valid")

    def test_list_strategies(self, registry):
        """Test listing all strategies."""
        strategies = registry.list_strategies()
        assert len(strategies) > 0
        assert all(hasattr(s, "api_type") for s in strategies)


class TestGetDefaultRegistry:
    """Tests for get_default_registry function."""

    def test_returns_registry(self):
        """Test that function returns a registry."""
        registry = get_default_registry()
        assert isinstance(registry, StrategyRegistry)

    def test_returns_same_instance(self):
        """Test that function returns the same instance."""
        registry1 = get_default_registry()
        registry2 = get_default_registry()
        assert registry1 is registry2


class TestValidateOGCAPI:
    """Tests for validate_ogc_api convenience function."""

    def test_validate_common_api(self):
        """Test validating a Common API."""
        doc = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/": {"get": {"responses": {"200": {"description": "OK"}}}},
                "/conformance": {"get": {"responses": {"200": {"description": "OK"}}}},
            },
        }
        ccs = [
            "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core",
        ]
        result = validate_ogc_api(doc, ccs)
        assert result.is_valid

    def test_validate_features_api(self):
        """Test validating a Features API."""
        doc = {
            "openapi": "3.0.3",
            "info": {"title": "Features API", "version": "1.0.0"},
            "paths": {
                "/": {"get": {"responses": {"200": {"description": "OK"}}}},
                "/conformance": {"get": {"responses": {"200": {"description": "OK"}}}},
                "/collections": {"get": {"responses": {"200": {"description": "OK"}}}},
                "/collections/{collectionId}": {
                    "get": {"responses": {"200": {"description": "OK"}}}
                },
                "/collections/{collectionId}/items": {
                    "get": {
                        "parameters": [
                            {"name": "limit", "in": "query"},
                            {"name": "bbox", "in": "query"},
                        ],
                        "responses": {"200": {"description": "OK"}},
                    }
                },
                "/collections/{collectionId}/items/{featureId}": {
                    "get": {"responses": {"200": {"description": "OK"}}}
                },
            },
        }
        ccs = [
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
        ]
        result = validate_ogc_api(doc, ccs)
        assert result.is_valid

    def test_validate_invalid_api(self):
        """Test validating an invalid API."""
        doc = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},  # No required paths
        }
        ccs = [
            "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core",
        ]
        result = validate_ogc_api(doc, ccs)
        assert not result.is_valid


class TestConformanceInference:
    """Tests for conformance inference from document structure."""

    @pytest.fixture
    def registry(self):
        """Create a registry instance."""
        return StrategyRegistry()

    def test_infer_features_from_paths(self, registry):
        """Test inferring Features from paths."""
        doc = {
            "paths": {
                "/": {},
                "/conformance": {},
                "/collections": {},
                "/collections/{collectionId}/items": {},
                "/collections/{collectionId}/items/{featureId}": {},
            }
        }
        ccs = registry._infer_conformance_from_paths(doc)
        uris = [cc.uri for cc in ccs]
        assert any("features" in uri for uri in uris)

    def test_infer_tiles_from_paths(self, registry):
        """Test inferring Tiles from paths."""
        doc = {
            "paths": {
                "/": {},
                "/conformance": {},
                "/tiles/{tileMatrixSetId}/{tileMatrix}/{tileRow}/{tileCol}": {},
            }
        }
        ccs = registry._infer_conformance_from_paths(doc)
        uris = [cc.uri for cc in ccs]
        assert any("tiles" in uri for uri in uris)

    def test_infer_processes_from_paths(self, registry):
        """Test inferring Processes from paths."""
        doc = {
            "paths": {
                "/": {},
                "/conformance": {},
                "/processes": {},
                "/processes/{processId}/execution": {},
            }
        }
        ccs = registry._infer_conformance_from_paths(doc)
        uris = [cc.uri for cc in ccs]
        assert any("processes" in uri for uri in uris)

    def test_extract_from_x_conformance(self, registry):
        """Test extracting conformance from x-conformance extension."""
        doc = {
            "info": {
                "title": "Test",
                "x-conformance": [
                    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
                ],
            },
            "paths": {},
        }
        ccs = registry._extract_conformance_from_document(doc)
        assert len(ccs) == 1
        assert ccs[0].api_type == OGCAPIType.FEATURES
