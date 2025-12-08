"""Tests for validation strategies."""

import pytest

from ogcapi_registry.ogc_types import ConformanceClass, OGCAPIType
from ogcapi_registry.strategies import (
    CommonStrategy,
    CompositeValidationStrategy,
    FeaturesStrategy,
    ProcessesStrategy,
    TilesStrategy,
)


class TestCommonStrategy:
    """Tests for CommonStrategy."""

    @pytest.fixture
    def strategy(self):
        """Create a CommonStrategy instance."""
        return CommonStrategy()

    @pytest.fixture
    def conformance_classes(self):
        """Create common conformance classes."""
        return [
            ConformanceClass(
                uri="http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core"
            ),
            ConformanceClass(
                uri="http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/oas30"
            ),
        ]

    def test_api_type(self, strategy):
        """Test that strategy has correct API type."""
        assert strategy.api_type == OGCAPIType.COMMON

    def test_matches_conformance(self, strategy, conformance_classes):
        """Test conformance matching."""
        assert strategy.matches_conformance(conformance_classes) is True

    def test_get_required_paths(self, strategy, conformance_classes):
        """Test getting required paths."""
        paths = strategy.get_required_paths(conformance_classes)
        assert "/" in paths
        assert "/conformance" in paths

    def test_validate_valid_document(self, strategy, conformance_classes):
        """Test validating a valid document."""
        doc = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/": {"get": {"responses": {"200": {"description": "OK"}}}},
                "/conformance": {"get": {"responses": {"200": {"description": "OK"}}}},
                "/api": {"get": {"responses": {"200": {"description": "OK"}}}},
            },
        }
        result = strategy.validate(doc, conformance_classes)
        assert result.is_valid

    def test_validate_missing_landing_page(self, strategy, conformance_classes):
        """Test validation fails when landing page is missing."""
        doc = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/conformance": {"get": {"responses": {"200": {"description": "OK"}}}},
            },
        }
        result = strategy.validate(doc, conformance_classes)
        assert not result.is_valid
        assert any("/" in e["path"] for e in result.errors)


class TestFeaturesStrategy:
    """Tests for FeaturesStrategy."""

    @pytest.fixture
    def strategy(self):
        """Create a FeaturesStrategy instance."""
        return FeaturesStrategy()

    @pytest.fixture
    def conformance_classes(self):
        """Create Features conformance classes."""
        return [
            ConformanceClass(
                uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core"
            ),
            ConformanceClass(
                uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson"
            ),
        ]

    def test_api_type(self, strategy):
        """Test that strategy has correct API type."""
        assert strategy.api_type == OGCAPIType.FEATURES

    def test_matches_conformance(self, strategy, conformance_classes):
        """Test conformance matching."""
        assert strategy.matches_conformance(conformance_classes) is True

    def test_get_required_paths(self, strategy, conformance_classes):
        """Test getting required paths."""
        paths = strategy.get_required_paths(conformance_classes)
        assert "/collections" in paths
        assert "/collections/{collectionId}" in paths
        assert "/collections/{collectionId}/items" in paths

    def test_get_required_operations(self, strategy, conformance_classes):
        """Test getting required operations."""
        ops = strategy.get_required_operations(conformance_classes)
        assert "get" in ops["/collections"]
        assert "get" in ops["/collections/{collectionId}/items"]

    def test_validate_valid_document(self, strategy, conformance_classes):
        """Test validating a valid Features document."""
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
        result = strategy.validate(doc, conformance_classes)
        assert result.is_valid

    def test_validate_missing_collections(self, strategy, conformance_classes):
        """Test validation fails when collections is missing."""
        doc = {
            "openapi": "3.0.3",
            "info": {"title": "Features API", "version": "1.0.0"},
            "paths": {
                "/": {"get": {"responses": {"200": {"description": "OK"}}}},
            },
        }
        result = strategy.validate(doc, conformance_classes)
        assert not result.is_valid
        assert any("collections" in e["path"] for e in result.errors)


class TestTilesStrategy:
    """Tests for TilesStrategy."""

    @pytest.fixture
    def strategy(self):
        """Create a TilesStrategy instance."""
        return TilesStrategy()

    @pytest.fixture
    def conformance_classes(self):
        """Create Tiles conformance classes."""
        return [
            ConformanceClass(
                uri="http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/core"
            ),
            ConformanceClass(
                uri="http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/dataset-tilesets"
            ),
        ]

    def test_api_type(self, strategy):
        """Test that strategy has correct API type."""
        assert strategy.api_type == OGCAPIType.TILES

    def test_matches_conformance(self, strategy, conformance_classes):
        """Test conformance matching."""
        assert strategy.matches_conformance(conformance_classes) is True

    def test_get_required_paths_with_dataset_tilesets(
        self, strategy, conformance_classes
    ):
        """Test getting required paths with dataset-tilesets conformance."""
        paths = strategy.get_required_paths(conformance_classes)
        assert "/tiles" in paths
        assert "/tiles/{tileMatrixSetId}" in paths


class TestProcessesStrategy:
    """Tests for ProcessesStrategy."""

    @pytest.fixture
    def strategy(self):
        """Create a ProcessesStrategy instance."""
        return ProcessesStrategy()

    @pytest.fixture
    def conformance_classes(self):
        """Create Processes conformance classes."""
        return [
            ConformanceClass(
                uri="http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/core"
            ),
            ConformanceClass(
                uri="http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/job-list"
            ),
        ]

    def test_api_type(self, strategy):
        """Test that strategy has correct API type."""
        assert strategy.api_type == OGCAPIType.PROCESSES

    def test_matches_conformance(self, strategy, conformance_classes):
        """Test conformance matching."""
        assert strategy.matches_conformance(conformance_classes) is True

    def test_get_required_paths(self, strategy, conformance_classes):
        """Test getting required paths."""
        paths = strategy.get_required_paths(conformance_classes)
        assert "/processes" in paths
        assert "/processes/{processId}" in paths
        assert "/processes/{processId}/execution" in paths
        assert "/jobs" in paths  # Because job-list conformance

    def test_get_required_operations(self, strategy, conformance_classes):
        """Test getting required operations."""
        ops = strategy.get_required_operations(conformance_classes)
        assert "get" in ops["/processes"]
        assert "post" in ops["/processes/{processId}/execution"]
        assert "get" in ops["/jobs"]


class TestCompositeValidationStrategy:
    """Tests for CompositeValidationStrategy."""

    @pytest.fixture
    def composite(self):
        """Create a composite strategy with Features and Tiles."""
        return CompositeValidationStrategy(
            [
                FeaturesStrategy(),
                TilesStrategy(),
            ]
        )

    @pytest.fixture
    def conformance_classes(self):
        """Create conformance classes for both Features and Tiles."""
        return [
            ConformanceClass(
                uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core"
            ),
            ConformanceClass(
                uri="http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/core"
            ),
        ]

    def test_combines_required_paths(self, composite, conformance_classes):
        """Test that composite combines paths from all strategies."""
        paths = composite.get_required_paths(conformance_classes)
        # Should have Features paths
        assert "/collections" in paths
        # Tiles paths depend on specific conformance

    def test_matches_conformance(self, composite, conformance_classes):
        """Test that composite matches if any sub-strategy matches."""
        assert composite.matches_conformance(conformance_classes) is True

    def test_strategies_property(self, composite):
        """Test accessing the strategies list."""
        assert len(composite.strategies) == 2
        assert any(isinstance(s, FeaturesStrategy) for s in composite.strategies)
        assert any(isinstance(s, TilesStrategy) for s in composite.strategies)


class TestPathMatching:
    """Tests for path pattern matching."""

    @pytest.fixture
    def strategy(self):
        """Create a strategy for testing."""
        return CommonStrategy()

    def test_exact_match(self, strategy):
        """Test exact path matching."""
        assert strategy._path_matches_pattern("/collections", "/collections")

    def test_parameter_match(self, strategy):
        """Test path with parameter matching."""
        assert strategy._path_matches_pattern(
            "/collections/my-collection", "/collections/{collectionId}"
        )

    def test_multiple_parameters(self, strategy):
        """Test path with multiple parameters."""
        assert strategy._path_matches_pattern(
            "/collections/my-collection/items/feature-1",
            "/collections/{collectionId}/items/{featureId}",
        )

    def test_no_match(self, strategy):
        """Test non-matching paths."""
        assert not strategy._path_matches_pattern("/other/path", "/collections")
