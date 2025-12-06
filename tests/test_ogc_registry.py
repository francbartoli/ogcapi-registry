"""Tests for the OGC Specification Registry."""

import pytest
from pytest_httpx import HTTPXMock

from ogcapi_registry import (
    OGCAPIType,
    OGCRegisteredSpecification,
    OGCSpecificationKey,
    OGCSpecificationRegistry,
    create_default_ogc_registry,
)
from ogcapi_registry.exceptions import (
    SpecificationAlreadyExistsError,
    SpecificationNotFoundError,
)


class TestOGCSpecificationKey:
    """Tests for OGCSpecificationKey."""

    def test_creation(self) -> None:
        """Test creating a specification key."""
        key = OGCSpecificationKey(
            api_type=OGCAPIType.FEATURES,
            spec_version="1.0",
            part=1,
        )
        assert key.api_type == OGCAPIType.FEATURES
        assert key.spec_version == "1.0"
        assert key.part == 1

    def test_creation_without_part(self) -> None:
        """Test creating a specification key without part number."""
        key = OGCSpecificationKey(
            api_type=OGCAPIType.EDR,
            spec_version="1.1",
        )
        assert key.api_type == OGCAPIType.EDR
        assert key.spec_version == "1.1"
        assert key.part is None

    def test_hashable(self) -> None:
        """Test that specification keys are hashable."""
        key1 = OGCSpecificationKey(
            api_type=OGCAPIType.FEATURES,
            spec_version="1.0",
            part=1,
        )
        key2 = OGCSpecificationKey(
            api_type=OGCAPIType.FEATURES,
            spec_version="1.0",
            part=1,
        )
        assert hash(key1) == hash(key2)

        # Can be used in sets
        keys = {key1, key2}
        assert len(keys) == 1

    def test_str_representation(self) -> None:
        """Test string representation of specification key."""
        key = OGCSpecificationKey(
            api_type=OGCAPIType.FEATURES,
            spec_version="1.0",
            part=1,
        )
        assert str(key) == "OGC API - Features Part 1 v1.0"

    def test_str_without_part(self) -> None:
        """Test string representation without part number."""
        key = OGCSpecificationKey(
            api_type=OGCAPIType.EDR,
            spec_version="1.1",
        )
        assert str(key) == "OGC API - Environmental Data Retrieval v1.1"

    def test_matches_strict(self) -> None:
        """Test strict matching of specification keys."""
        key1 = OGCSpecificationKey(
            api_type=OGCAPIType.FEATURES,
            spec_version="1.0",
            part=1,
        )
        key2 = OGCSpecificationKey(
            api_type=OGCAPIType.FEATURES,
            spec_version="1.0",
            part=1,
        )
        key3 = OGCSpecificationKey(
            api_type=OGCAPIType.FEATURES,
            spec_version="1.0.1",
            part=1,
        )

        assert key1.matches(key2, strict=True)
        assert not key1.matches(key3, strict=True)

    def test_matches_non_strict(self) -> None:
        """Test non-strict (major.minor) matching of specification keys."""
        key1 = OGCSpecificationKey(
            api_type=OGCAPIType.FEATURES,
            spec_version="1.0",
            part=1,
        )
        key2 = OGCSpecificationKey(
            api_type=OGCAPIType.FEATURES,
            spec_version="1.0.1",
            part=1,
        )
        key3 = OGCSpecificationKey(
            api_type=OGCAPIType.FEATURES,
            spec_version="1.1",
            part=1,
        )

        assert key1.matches(key2, strict=False)  # 1.0 matches 1.0.1
        assert not key1.matches(key3, strict=False)  # 1.0 doesn't match 1.1

    def test_immutability(self) -> None:
        """Test that specification keys are immutable."""
        key = OGCSpecificationKey(
            api_type=OGCAPIType.FEATURES,
            spec_version="1.0",
            part=1,
        )
        with pytest.raises(Exception):  # Pydantic ValidationError
            key.spec_version = "2.0"  # type: ignore


class TestOGCRegisteredSpecification:
    """Tests for OGCRegisteredSpecification."""

    def test_creation(self) -> None:
        """Test creating a registered specification."""
        key = OGCSpecificationKey(
            api_type=OGCAPIType.FEATURES,
            spec_version="1.0",
            part=1,
        )
        raw_content = {
            "openapi": "3.0.3",
            "info": {"title": "OGC API - Features", "version": "1.0.0"},
            "paths": {"/": {}},
        }

        spec = OGCRegisteredSpecification(key=key, raw_content=raw_content)

        assert spec.key == key
        assert spec.raw_content == raw_content
        assert spec.openapi_version == "3.0.3"
        assert spec.info_title == "OGC API - Features"
        assert spec.info_version == "1.0.0"

    def test_paths_property(self) -> None:
        """Test accessing paths from the specification."""
        key = OGCSpecificationKey(
            api_type=OGCAPIType.FEATURES,
            spec_version="1.0",
            part=1,
        )
        raw_content = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/": {"get": {}},
                "/collections": {"get": {}},
            },
        }

        spec = OGCRegisteredSpecification(key=key, raw_content=raw_content)
        assert "/" in spec.paths
        assert "/collections" in spec.paths


class TestOGCSpecificationRegistry:
    """Tests for OGCSpecificationRegistry."""

    def test_register(self) -> None:
        """Test registering a specification."""
        registry = OGCSpecificationRegistry()
        raw_content = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {},
        }

        spec = registry.register(
            api_type=OGCAPIType.FEATURES,
            spec_version="1.0",
            raw_content=raw_content,
            part=1,
        )

        assert spec.key.api_type == OGCAPIType.FEATURES
        assert spec.key.spec_version == "1.0"
        assert spec.key.part == 1

    def test_register_duplicate_raises_error(self) -> None:
        """Test that registering a duplicate raises an error."""
        registry = OGCSpecificationRegistry()
        raw_content = {"openapi": "3.0.3", "info": {"title": "Test", "version": "1.0.0"}}

        registry.register(
            api_type=OGCAPIType.FEATURES,
            spec_version="1.0",
            raw_content=raw_content,
        )

        with pytest.raises(SpecificationAlreadyExistsError):
            registry.register(
                api_type=OGCAPIType.FEATURES,
                spec_version="1.0",
                raw_content=raw_content,
            )

    def test_register_overwrite(self) -> None:
        """Test overwriting an existing specification."""
        registry = OGCSpecificationRegistry()
        raw_content1 = {"openapi": "3.0.3", "info": {"title": "Test 1", "version": "1.0.0"}}
        raw_content2 = {"openapi": "3.0.3", "info": {"title": "Test 2", "version": "1.0.0"}}

        registry.register(
            api_type=OGCAPIType.FEATURES,
            spec_version="1.0",
            raw_content=raw_content1,
        )

        spec = registry.register(
            api_type=OGCAPIType.FEATURES,
            spec_version="1.0",
            raw_content=raw_content2,
            overwrite=True,
        )

        assert spec.info_title == "Test 2"

    def test_get(self) -> None:
        """Test getting a specification by key components."""
        registry = OGCSpecificationRegistry()
        raw_content = {"openapi": "3.0.3", "info": {"title": "Test", "version": "1.0.0"}}

        registry.register(
            api_type=OGCAPIType.EDR,
            spec_version="1.1",
            raw_content=raw_content,
        )

        spec = registry.get(api_type=OGCAPIType.EDR, spec_version="1.1")
        assert spec.key.api_type == OGCAPIType.EDR
        assert spec.key.spec_version == "1.1"

    def test_get_not_found(self) -> None:
        """Test getting a non-existent specification."""
        registry = OGCSpecificationRegistry()

        with pytest.raises(SpecificationNotFoundError):
            registry.get(api_type=OGCAPIType.FEATURES, spec_version="1.0")

    def test_get_latest(self) -> None:
        """Test getting the latest version of a specification."""
        registry = OGCSpecificationRegistry()
        raw_content = {"openapi": "3.0.3", "info": {"title": "Test", "version": "1.0.0"}}

        registry.register(
            api_type=OGCAPIType.EDR,
            spec_version="1.0",
            raw_content=raw_content,
        )
        registry.register(
            api_type=OGCAPIType.EDR,
            spec_version="1.1",
            raw_content=raw_content,
        )
        registry.register(
            api_type=OGCAPIType.EDR,
            spec_version="1.0.1",
            raw_content=raw_content,
        )

        latest = registry.get_latest(api_type=OGCAPIType.EDR)
        assert latest.key.spec_version == "1.1"

    def test_get_latest_not_found(self) -> None:
        """Test getting latest when no specifications exist."""
        registry = OGCSpecificationRegistry()

        with pytest.raises(SpecificationNotFoundError):
            registry.get_latest(api_type=OGCAPIType.FEATURES)

    def test_exists(self) -> None:
        """Test checking if a specification exists."""
        registry = OGCSpecificationRegistry()
        raw_content = {"openapi": "3.0.3", "info": {"title": "Test", "version": "1.0.0"}}

        assert not registry.exists(api_type=OGCAPIType.FEATURES, spec_version="1.0")

        registry.register(
            api_type=OGCAPIType.FEATURES,
            spec_version="1.0",
            raw_content=raw_content,
        )

        assert registry.exists(api_type=OGCAPIType.FEATURES, spec_version="1.0")

    def test_remove(self) -> None:
        """Test removing a specification."""
        registry = OGCSpecificationRegistry()
        raw_content = {"openapi": "3.0.3", "info": {"title": "Test", "version": "1.0.0"}}

        registry.register(
            api_type=OGCAPIType.FEATURES,
            spec_version="1.0",
            raw_content=raw_content,
        )

        assert registry.remove(api_type=OGCAPIType.FEATURES, spec_version="1.0")
        assert not registry.exists(api_type=OGCAPIType.FEATURES, spec_version="1.0")

    def test_remove_non_existent(self) -> None:
        """Test removing a non-existent specification."""
        registry = OGCSpecificationRegistry()
        assert not registry.remove(api_type=OGCAPIType.FEATURES, spec_version="1.0")

    def test_list_versions(self) -> None:
        """Test listing all versions of an API type."""
        registry = OGCSpecificationRegistry()
        raw_content = {"openapi": "3.0.3", "info": {"title": "Test", "version": "1.0.0"}}

        registry.register(api_type=OGCAPIType.EDR, spec_version="1.0", raw_content=raw_content)
        registry.register(api_type=OGCAPIType.EDR, spec_version="1.1", raw_content=raw_content)
        registry.register(api_type=OGCAPIType.EDR, spec_version="1.0.1", raw_content=raw_content)

        versions = registry.list_versions(api_type=OGCAPIType.EDR)
        assert versions == ["1.1", "1.0.1", "1.0"]

    def test_list_by_type(self) -> None:
        """Test listing specifications by API type."""
        registry = OGCSpecificationRegistry()
        raw_content = {"openapi": "3.0.3", "info": {"title": "Test", "version": "1.0.0"}}

        registry.register(api_type=OGCAPIType.FEATURES, spec_version="1.0", raw_content=raw_content)
        registry.register(api_type=OGCAPIType.EDR, spec_version="1.1", raw_content=raw_content)
        registry.register(api_type=OGCAPIType.FEATURES, spec_version="1.1", raw_content=raw_content)

        features_specs = registry.list_by_type(api_type=OGCAPIType.FEATURES)
        assert len(features_specs) == 2
        assert features_specs[0].key.spec_version == "1.1"  # Latest first
        assert features_specs[1].key.spec_version == "1.0"

    def test_list_keys(self) -> None:
        """Test listing all specification keys."""
        registry = OGCSpecificationRegistry()
        raw_content = {"openapi": "3.0.3", "info": {"title": "Test", "version": "1.0.0"}}

        registry.register(api_type=OGCAPIType.FEATURES, spec_version="1.0", raw_content=raw_content)
        registry.register(api_type=OGCAPIType.EDR, spec_version="1.1", raw_content=raw_content)

        keys = registry.list_keys()
        assert len(keys) == 2

    def test_len(self) -> None:
        """Test getting the number of specifications."""
        registry = OGCSpecificationRegistry()
        raw_content = {"openapi": "3.0.3", "info": {"title": "Test", "version": "1.0.0"}}

        assert len(registry) == 0

        registry.register(api_type=OGCAPIType.FEATURES, spec_version="1.0", raw_content=raw_content)
        assert len(registry) == 1

    def test_contains(self) -> None:
        """Test checking if a key exists using 'in' operator."""
        registry = OGCSpecificationRegistry()
        raw_content = {"openapi": "3.0.3", "info": {"title": "Test", "version": "1.0.0"}}

        key = OGCSpecificationKey(api_type=OGCAPIType.FEATURES, spec_version="1.0")

        assert key not in registry

        registry.register(api_type=OGCAPIType.FEATURES, spec_version="1.0", raw_content=raw_content)

        assert key in registry

    def test_iter(self) -> None:
        """Test iterating over specification keys."""
        registry = OGCSpecificationRegistry()
        raw_content = {"openapi": "3.0.3", "info": {"title": "Test", "version": "1.0.0"}}

        registry.register(api_type=OGCAPIType.FEATURES, spec_version="1.0", raw_content=raw_content)
        registry.register(api_type=OGCAPIType.EDR, spec_version="1.1", raw_content=raw_content)

        keys = list(registry)
        assert len(keys) == 2

    def test_clear(self) -> None:
        """Test clearing all specifications."""
        registry = OGCSpecificationRegistry()
        raw_content = {"openapi": "3.0.3", "info": {"title": "Test", "version": "1.0.0"}}

        registry.register(api_type=OGCAPIType.FEATURES, spec_version="1.0", raw_content=raw_content)
        registry.register(api_type=OGCAPIType.EDR, spec_version="1.1", raw_content=raw_content)

        assert len(registry) == 2
        registry.clear()
        assert len(registry) == 0

    def test_register_from_url(self, httpx_mock: HTTPXMock) -> None:
        """Test registering a specification from a URL."""
        spec_content = {
            "openapi": "3.0.3",
            "info": {"title": "OGC API - Features", "version": "1.0.0"},
            "paths": {},
        }

        httpx_mock.add_response(
            url="https://example.com/openapi.json",
            json=spec_content,
            headers={"content-type": "application/json"},
        )

        registry = OGCSpecificationRegistry()
        spec = registry.register_from_url(
            api_type=OGCAPIType.FEATURES,
            spec_version="1.0",
            url="https://example.com/openapi.json",
            part=1,
        )

        assert spec.key.api_type == OGCAPIType.FEATURES
        assert spec.key.spec_version == "1.0"
        assert spec.info_title == "OGC API - Features"


class TestCreateDefaultOGCRegistry:
    """Tests for create_default_ogc_registry."""

    def test_creates_empty_registry(self) -> None:
        """Test that create_default_ogc_registry creates an empty registry."""
        registry = create_default_ogc_registry()
        assert isinstance(registry, OGCSpecificationRegistry)
        assert len(registry) == 0


class TestConformanceClassSpecificationKey:
    """Tests for ConformanceClass.specification_key property."""

    def test_conformance_class_spec_key(self) -> None:
        """Test extracting specification key from conformance class."""
        from ogcapi_registry import ConformanceClass

        cc = ConformanceClass(
            uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core"
        )

        key = cc.specification_key
        assert key is not None
        assert key.api_type == OGCAPIType.FEATURES
        assert key.spec_version == "1.0"
        assert key.part == 1

    def test_conformance_class_spec_version(self) -> None:
        """Test extracting specification version from conformance class."""
        from ogcapi_registry import ConformanceClass

        cc = ConformanceClass(
            uri="http://www.opengis.net/spec/ogcapi-edr-1/1.1/conf/core"
        )

        assert cc.spec_version == "1.1"
        assert cc.part == 1
        assert cc.conformance_class_name == "core"

    def test_conformance_class_name_extraction(self) -> None:
        """Test extracting conformance class name."""
        from ogcapi_registry import ConformanceClass

        cc = ConformanceClass(
            uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson"
        )

        assert cc.conformance_class_name == "geojson"


class TestOGCTypesHelperFunctions:
    """Tests for helper functions in ogc_types module."""

    def test_get_specification_keys(self) -> None:
        """Test extracting specification keys from conformance classes."""
        from ogcapi_registry import ConformanceClass, get_specification_keys

        ccs = [
            ConformanceClass(uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core"),
            ConformanceClass(uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson"),
            ConformanceClass(uri="http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core"),
        ]

        keys = get_specification_keys(ccs)
        assert len(keys) == 2  # Features 1.0 and Common 1.0

    def test_get_specification_versions(self) -> None:
        """Test getting versions of a specific API type."""
        from ogcapi_registry import ConformanceClass, get_specification_versions

        ccs = [
            ConformanceClass(uri="http://www.opengis.net/spec/ogcapi-edr-1/1.0/conf/core"),
            ConformanceClass(uri="http://www.opengis.net/spec/ogcapi-edr-1/1.1/conf/core"),
            ConformanceClass(uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core"),
        ]

        versions = get_specification_versions(ccs, OGCAPIType.EDR)
        assert versions == {"1.0", "1.1"}

    def test_group_conformance_by_spec(self) -> None:
        """Test grouping conformance classes by specification."""
        from ogcapi_registry import ConformanceClass, group_conformance_by_spec

        ccs = [
            ConformanceClass(uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core"),
            ConformanceClass(uri="http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson"),
            ConformanceClass(uri="http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core"),
        ]

        groups = group_conformance_by_spec(ccs)
        assert len(groups) == 2

        # Check Features 1.0 Part 1 group
        features_key = OGCSpecificationKey(
            api_type=OGCAPIType.FEATURES,
            spec_version="1.0",
            part=1,
        )
        assert features_key in groups
        assert len(groups[features_key]) == 2
