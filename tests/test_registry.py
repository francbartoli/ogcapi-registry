"""Tests for the registry module."""

import json

import pytest

from openapi_registry_validator.exceptions import (
    SpecificationAlreadyExistsError,
    SpecificationNotFoundError,
)
from openapi_registry_validator.models import (
    SpecificationKey,
    SpecificationMetadata,
    SpecificationType,
)
from openapi_registry_validator.registry import (
    AsyncSpecificationRegistry,
    SpecificationRegistry,
)


class TestSpecificationRegistry:
    """Tests for SpecificationRegistry."""

    @pytest.fixture
    def registry(self):
        """Create a fresh registry instance."""
        return SpecificationRegistry()

    @pytest.fixture
    def sample_content(self):
        """Return sample OpenAPI content."""
        return {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }

    def test_register(self, registry, sample_content):
        """Test registering a specification."""
        spec = registry.register(
            content=sample_content,
            spec_type=SpecificationType.OPENAPI_3_0,
            version="3.0.3",
        )
        assert spec.key.spec_type == SpecificationType.OPENAPI_3_0
        assert spec.key.version == "3.0.3"
        assert spec.raw_content == sample_content

    def test_register_with_metadata(self, registry, sample_content):
        """Test registering with custom metadata."""
        metadata = SpecificationMetadata(
            source_url="https://example.com/openapi.json"
        )
        spec = registry.register(
            content=sample_content,
            spec_type=SpecificationType.OPENAPI_3_0,
            version="3.0.3",
            metadata=metadata,
        )
        assert spec.metadata.source_url == "https://example.com/openapi.json"

    def test_register_duplicate_raises_error(self, registry, sample_content):
        """Test that registering a duplicate raises an error."""
        registry.register(
            content=sample_content,
            spec_type=SpecificationType.OPENAPI_3_0,
            version="3.0.3",
        )

        with pytest.raises(SpecificationAlreadyExistsError):
            registry.register(
                content=sample_content,
                spec_type=SpecificationType.OPENAPI_3_0,
                version="3.0.3",
            )

    def test_register_overwrite(self, registry, sample_content):
        """Test overwriting an existing specification."""
        registry.register(
            content=sample_content,
            spec_type=SpecificationType.OPENAPI_3_0,
            version="3.0.3",
        )

        updated_content = {**sample_content, "info": {"title": "Updated", "version": "2.0"}}
        spec = registry.register(
            content=updated_content,
            spec_type=SpecificationType.OPENAPI_3_0,
            version="3.0.3",
            overwrite=True,
        )
        assert spec.raw_content["info"]["title"] == "Updated"

    def test_get(self, registry, sample_content):
        """Test getting a specification."""
        registry.register(
            content=sample_content,
            spec_type=SpecificationType.OPENAPI_3_0,
            version="3.0.3",
        )

        spec = registry.get(SpecificationType.OPENAPI_3_0, "3.0.3")
        assert spec.raw_content == sample_content

    def test_get_not_found(self, registry):
        """Test that getting a non-existent spec raises an error."""
        with pytest.raises(SpecificationNotFoundError):
            registry.get(SpecificationType.OPENAPI_3_0, "3.0.3")

    def test_get_by_key(self, registry, sample_content):
        """Test getting a specification by key."""
        registry.register(
            content=sample_content,
            spec_type=SpecificationType.OPENAPI_3_0,
            version="3.0.3",
        )

        key = SpecificationKey(
            spec_type=SpecificationType.OPENAPI_3_0, version="3.0.3"
        )
        spec = registry.get_by_key(key)
        assert spec.raw_content == sample_content

    def test_exists(self, registry, sample_content):
        """Test checking if a specification exists."""
        assert registry.exists(SpecificationType.OPENAPI_3_0, "3.0.3") is False

        registry.register(
            content=sample_content,
            spec_type=SpecificationType.OPENAPI_3_0,
            version="3.0.3",
        )

        assert registry.exists(SpecificationType.OPENAPI_3_0, "3.0.3") is True

    def test_remove(self, registry, sample_content):
        """Test removing a specification."""
        registry.register(
            content=sample_content,
            spec_type=SpecificationType.OPENAPI_3_0,
            version="3.0.3",
        )

        result = registry.remove(SpecificationType.OPENAPI_3_0, "3.0.3")
        assert result is True
        assert registry.exists(SpecificationType.OPENAPI_3_0, "3.0.3") is False

    def test_remove_non_existent(self, registry):
        """Test removing a non-existent specification."""
        result = registry.remove(SpecificationType.OPENAPI_3_0, "3.0.3")
        assert result is False

    def test_clear(self, registry, sample_content):
        """Test clearing all specifications."""
        registry.register(
            content=sample_content,
            spec_type=SpecificationType.OPENAPI_3_0,
            version="3.0.3",
        )
        registry.register(
            content={**sample_content, "openapi": "3.1.0"},
            spec_type=SpecificationType.OPENAPI_3_1,
            version="3.1.0",
        )

        registry.clear()
        assert len(registry) == 0

    def test_list_keys(self, registry, sample_content):
        """Test listing all keys."""
        registry.register(
            content=sample_content,
            spec_type=SpecificationType.OPENAPI_3_0,
            version="3.0.3",
        )

        keys = registry.list_keys()
        assert len(keys) == 1
        assert keys[0].spec_type == SpecificationType.OPENAPI_3_0

    def test_list_specifications(self, registry, sample_content):
        """Test listing all specifications."""
        registry.register(
            content=sample_content,
            spec_type=SpecificationType.OPENAPI_3_0,
            version="3.0.3",
        )

        specs = registry.list_specifications()
        assert len(specs) == 1
        assert specs[0].raw_content == sample_content

    def test_len(self, registry, sample_content):
        """Test getting registry length."""
        assert len(registry) == 0

        registry.register(
            content=sample_content,
            spec_type=SpecificationType.OPENAPI_3_0,
            version="3.0.3",
        )
        assert len(registry) == 1

    def test_iter(self, registry, sample_content):
        """Test iterating over specifications."""
        registry.register(
            content=sample_content,
            spec_type=SpecificationType.OPENAPI_3_0,
            version="3.0.3",
        )

        specs = list(registry)
        assert len(specs) == 1
        assert specs[0].raw_content == sample_content

    def test_contains(self, registry, sample_content):
        """Test checking if key is in registry."""
        key = SpecificationKey(
            spec_type=SpecificationType.OPENAPI_3_0, version="3.0.3"
        )

        assert key not in registry

        registry.register(
            content=sample_content,
            spec_type=SpecificationType.OPENAPI_3_0,
            version="3.0.3",
        )

        assert key in registry

    def test_register_from_url(self, httpx_mock, registry):
        """Test registering from a URL."""
        content = json.dumps({
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        })
        httpx_mock.add_response(
            url="https://example.com/openapi.json",
            content=content.encode(),
            headers={"content-type": "application/json"},
        )

        spec = registry.register_from_url("https://example.com/openapi.json")
        assert spec.key.spec_type == SpecificationType.OPENAPI_3_0
        assert spec.key.version == "3.0.3"
        assert spec.metadata.source_url == "https://example.com/openapi.json"

    def test_register_from_url_infer_version(self, httpx_mock, registry):
        """Test that version is inferred from content."""
        content = json.dumps({
            "openapi": "3.1.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        })
        httpx_mock.add_response(
            url="https://example.com/openapi.json",
            content=content.encode(),
            headers={"content-type": "application/json"},
        )

        spec = registry.register_from_url("https://example.com/openapi.json")
        assert spec.key.spec_type == SpecificationType.OPENAPI_3_1
        assert spec.key.version == "3.1.0"


class TestAsyncSpecificationRegistry:
    """Tests for AsyncSpecificationRegistry."""

    @pytest.fixture
    def registry(self):
        """Create a fresh async registry instance."""
        return AsyncSpecificationRegistry()

    @pytest.fixture
    def sample_content(self):
        """Return sample OpenAPI content."""
        return {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }

    def test_register_sync(self, registry, sample_content):
        """Test that register works synchronously."""
        spec = registry.register(
            content=sample_content,
            spec_type=SpecificationType.OPENAPI_3_0,
            version="3.0.3",
        )
        assert spec.key.spec_type == SpecificationType.OPENAPI_3_0

    @pytest.mark.asyncio
    async def test_register_from_url(self, httpx_mock, registry):
        """Test registering from a URL asynchronously."""
        content = json.dumps({
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        })
        httpx_mock.add_response(
            url="https://example.com/openapi.json",
            content=content.encode(),
            headers={"content-type": "application/json"},
        )

        spec = await registry.register_from_url("https://example.com/openapi.json")
        assert spec.key.spec_type == SpecificationType.OPENAPI_3_0
        assert spec.metadata.source_url == "https://example.com/openapi.json"

    def test_get(self, registry, sample_content):
        """Test getting a specification."""
        registry.register(
            content=sample_content,
            spec_type=SpecificationType.OPENAPI_3_0,
            version="3.0.3",
        )

        spec = registry.get(SpecificationType.OPENAPI_3_0, "3.0.3")
        assert spec.raw_content == sample_content

    def test_delegation(self, registry, sample_content):
        """Test that methods delegate to sync registry."""
        registry.register(
            content=sample_content,
            spec_type=SpecificationType.OPENAPI_3_0,
            version="3.0.3",
        )

        assert registry.exists(SpecificationType.OPENAPI_3_0, "3.0.3")
        assert len(registry) == 1
        assert len(registry.list_keys()) == 1
        assert len(registry.list_specifications()) == 1

        registry.remove(SpecificationType.OPENAPI_3_0, "3.0.3")
        assert not registry.exists(SpecificationType.OPENAPI_3_0, "3.0.3")
