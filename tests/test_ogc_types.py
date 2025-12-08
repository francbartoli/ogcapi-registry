"""Tests for the ogc_types module."""

import pytest

from ogcapi_registry.ogc_types import (
    ConformanceClass,
    OGCAPIType,
    detect_api_types,
    get_primary_api_type,
    parse_conformance_classes,
)


class TestOGCAPIType:
    """Tests for OGCAPIType enum."""

    def test_display_names(self):
        """Test that all types have display names."""
        for api_type in OGCAPIType:
            assert api_type.display_name is not None
            assert len(api_type.display_name) > 0

    def test_features_display_name(self):
        """Test Features display name."""
        assert OGCAPIType.FEATURES.display_name == "OGC API - Features"

    def test_tiles_display_name(self):
        """Test Tiles display name."""
        assert OGCAPIType.TILES.display_name == "OGC API - Tiles"


class TestConformanceClass:
    """Tests for ConformanceClass model."""

    def test_creation(self):
        """Test creating a conformance class."""
        cc = ConformanceClass(
            uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core"
        )
        assert cc.uri == "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core"

    def test_api_type_detection_features(self):
        """Test detecting Features API type."""
        cc = ConformanceClass(
            uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core"
        )
        assert cc.api_type == OGCAPIType.FEATURES

    def test_api_type_detection_tiles(self):
        """Test detecting Tiles API type."""
        cc = ConformanceClass(
            uri="http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/core"
        )
        assert cc.api_type == OGCAPIType.TILES

    def test_api_type_detection_processes(self):
        """Test detecting Processes API type."""
        cc = ConformanceClass(
            uri="http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/core"
        )
        assert cc.api_type == OGCAPIType.PROCESSES

    def test_api_type_detection_common(self):
        """Test detecting Common API type."""
        cc = ConformanceClass(
            uri="http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core"
        )
        assert cc.api_type == OGCAPIType.COMMON

    def test_api_type_detection_unknown(self):
        """Test that unknown URIs return None."""
        cc = ConformanceClass(uri="http://example.com/unknown")
        assert cc.api_type is None

    def test_is_core(self):
        """Test is_core property."""
        core = ConformanceClass(
            uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core"
        )
        assert core.is_core is True

        non_core = ConformanceClass(
            uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson"
        )
        assert non_core.is_core is False

    def test_version_extraction(self):
        """Test version extraction from URI."""
        cc = ConformanceClass(
            uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core"
        )
        assert cc.version == "1.0"

        cc2 = ConformanceClass(
            uri="http://www.opengis.net/spec/ogcapi-features-2/1.0.1/conf/crs"
        )
        assert cc2.version == "1.0.1"

    def test_hashable(self):
        """Test that conformance classes are hashable."""
        cc1 = ConformanceClass(
            uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core"
        )
        cc2 = ConformanceClass(
            uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core"
        )
        assert hash(cc1) == hash(cc2)
        assert cc1 == cc2

    def test_equality_with_string(self):
        """Test equality comparison with string."""
        cc = ConformanceClass(
            uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core"
        )
        assert cc == "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core"

    def test_immutability(self):
        """Test that conformance class is immutable."""
        cc = ConformanceClass(
            uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core"
        )
        with pytest.raises(Exception):  # ValidationError from Pydantic
            cc.uri = "http://example.com/other"


class TestParseConformanceClasses:
    """Tests for parse_conformance_classes function."""

    def test_parse_list(self):
        """Test parsing a list of URIs."""
        uris = [
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson",
        ]
        result = parse_conformance_classes(uris)
        assert len(result) == 2
        assert all(isinstance(cc, ConformanceClass) for cc in result)

    def test_parse_dict_with_conforms_to(self):
        """Test parsing a dict with conformsTo key."""
        data = {
            "conformsTo": [
                "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
            ]
        }
        result = parse_conformance_classes(data)
        assert len(result) == 1

    def test_parse_empty(self):
        """Test parsing empty list."""
        result = parse_conformance_classes([])
        assert len(result) == 0


class TestDetectAPITypes:
    """Tests for detect_api_types function."""

    def test_detect_single_type(self):
        """Test detecting a single API type."""
        ccs = [
            ConformanceClass(
                uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core"
            ),
        ]
        types = detect_api_types(ccs)
        assert types == {OGCAPIType.FEATURES}

    def test_detect_multiple_types(self):
        """Test detecting multiple API types."""
        ccs = [
            ConformanceClass(
                uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core"
            ),
            ConformanceClass(
                uri="http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/core"
            ),
        ]
        types = detect_api_types(ccs)
        assert types == {OGCAPIType.FEATURES, OGCAPIType.TILES}

    def test_detect_empty(self):
        """Test detecting from empty list."""
        types = detect_api_types([])
        assert types == set()


class TestGetPrimaryAPIType:
    """Tests for get_primary_api_type function."""

    def test_features_is_primary(self):
        """Test that Features takes priority."""
        ccs = [
            ConformanceClass(
                uri="http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core"
            ),
            ConformanceClass(
                uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core"
            ),
        ]
        primary = get_primary_api_type(ccs)
        assert primary == OGCAPIType.FEATURES

    def test_tiles_over_common(self):
        """Test that Tiles takes priority over Common."""
        ccs = [
            ConformanceClass(
                uri="http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core"
            ),
            ConformanceClass(
                uri="http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/core"
            ),
        ]
        primary = get_primary_api_type(ccs)
        assert primary == OGCAPIType.TILES

    def test_fallback_to_common(self):
        """Test fallback to Common when nothing else matches."""
        ccs = [
            ConformanceClass(uri="http://example.com/unknown"),
        ]
        primary = get_primary_api_type(ccs)
        assert primary == OGCAPIType.COMMON

    def test_empty_returns_common(self):
        """Test that empty list returns Common."""
        primary = get_primary_api_type([])
        assert primary == OGCAPIType.COMMON
