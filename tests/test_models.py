"""Tests for the models module."""

import pytest
from pydantic import ValidationError

from openapi_registry_validator.models import (
    RegisteredSpecification,
    SpecificationKey,
    SpecificationMetadata,
    SpecificationType,
    ValidationResult,
)


class TestSpecificationType:
    """Tests for SpecificationType enum."""

    def test_from_version_3_0(self):
        """Test parsing OpenAPI 3.0.x versions."""
        assert SpecificationType.from_version("3.0.0") == SpecificationType.OPENAPI_3_0
        assert SpecificationType.from_version("3.0.3") == SpecificationType.OPENAPI_3_0

    def test_from_version_3_1(self):
        """Test parsing OpenAPI 3.1.x versions."""
        assert SpecificationType.from_version("3.1.0") == SpecificationType.OPENAPI_3_1
        assert SpecificationType.from_version("3.1.1") == SpecificationType.OPENAPI_3_1

    def test_from_version_unsupported(self):
        """Test that unsupported versions raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported OpenAPI version"):
            SpecificationType.from_version("2.0")
        with pytest.raises(ValueError, match="Unsupported OpenAPI version"):
            SpecificationType.from_version("4.0.0")


class TestSpecificationKey:
    """Tests for SpecificationKey model."""

    def test_creation(self):
        """Test creating a specification key."""
        key = SpecificationKey(
            spec_type=SpecificationType.OPENAPI_3_0, version="3.0.3"
        )
        assert key.spec_type == SpecificationType.OPENAPI_3_0
        assert key.version == "3.0.3"

    def test_immutability(self):
        """Test that specification key is immutable."""
        key = SpecificationKey(
            spec_type=SpecificationType.OPENAPI_3_0, version="3.0.3"
        )
        with pytest.raises(ValidationError):
            key.version = "3.0.4"

    def test_hashable(self):
        """Test that specification key is hashable."""
        key1 = SpecificationKey(
            spec_type=SpecificationType.OPENAPI_3_0, version="3.0.3"
        )
        key2 = SpecificationKey(
            spec_type=SpecificationType.OPENAPI_3_0, version="3.0.3"
        )
        key3 = SpecificationKey(
            spec_type=SpecificationType.OPENAPI_3_1, version="3.1.0"
        )

        # Same keys should be equal and have same hash
        assert key1 == key2
        assert hash(key1) == hash(key2)

        # Different keys should not be equal
        assert key1 != key3

        # Should be usable as dict keys
        d = {key1: "value1", key3: "value3"}
        assert d[key2] == "value1"


class TestSpecificationMetadata:
    """Tests for SpecificationMetadata model."""

    def test_defaults(self):
        """Test default values."""
        metadata = SpecificationMetadata()
        assert metadata.source_url is None
        assert metadata.content_type is None
        assert metadata.etag is None
        assert metadata.fetched_at is not None

    def test_with_values(self):
        """Test creating with values."""
        metadata = SpecificationMetadata(
            source_url="https://example.com/openapi.json",
            content_type="application/json",
            etag='"abc123"',
        )
        assert metadata.source_url == "https://example.com/openapi.json"
        assert metadata.content_type == "application/json"
        assert metadata.etag == '"abc123"'

    def test_immutability(self):
        """Test that metadata is immutable."""
        metadata = SpecificationMetadata(source_url="https://example.com")
        with pytest.raises(ValidationError):
            metadata.source_url = "https://other.com"


class TestRegisteredSpecification:
    """Tests for RegisteredSpecification model."""

    @pytest.fixture
    def sample_spec(self):
        """Create a sample specification."""
        return RegisteredSpecification(
            key=SpecificationKey(
                spec_type=SpecificationType.OPENAPI_3_0, version="3.0.3"
            ),
            metadata=SpecificationMetadata(
                source_url="https://example.com/openapi.yaml"
            ),
            raw_content={
                "openapi": "3.0.3",
                "info": {"title": "Test API", "version": "1.0.0"},
                "paths": {},
            },
        )

    def test_openapi_version(self, sample_spec):
        """Test getting OpenAPI version."""
        assert sample_spec.openapi_version == "3.0.3"

    def test_info_title(self, sample_spec):
        """Test getting info title."""
        assert sample_spec.info_title == "Test API"

    def test_info_version(self, sample_spec):
        """Test getting info version."""
        assert sample_spec.info_version == "1.0.0"

    def test_to_openapi_raises_for_3_0(self, sample_spec):
        """Test that converting 3.0 spec raises ValueError."""
        with pytest.raises(ValueError, match="does not support OpenAPI 3.0"):
            sample_spec.to_openapi()

    def test_to_openapi_works_for_3_1(self):
        """Test converting 3.1 spec to OpenAPI model."""
        spec = RegisteredSpecification(
            key=SpecificationKey(
                spec_type=SpecificationType.OPENAPI_3_1, version="3.1.0"
            ),
            metadata=SpecificationMetadata(),
            raw_content={
                "openapi": "3.1.0",
                "info": {"title": "Test API 3.1", "version": "1.0.0"},
            },
        )
        openapi = spec.to_openapi()
        assert openapi.info.title == "Test API 3.1"
        assert openapi.info.version == "1.0.0"

    def test_immutability(self, sample_spec):
        """Test that specification is immutable."""
        with pytest.raises(ValidationError):
            sample_spec.raw_content = {}


class TestValidationResult:
    """Tests for ValidationResult model."""

    def test_success(self):
        """Test creating a success result."""
        result = ValidationResult.success()
        assert result.is_valid is True
        assert result.errors == ()
        assert result.warnings == ()

    def test_success_with_warnings(self):
        """Test creating a success result with warnings."""
        warnings = ({"path": "/", "message": "Warning"},)
        result = ValidationResult.success(warnings=warnings)
        assert result.is_valid is True
        assert result.warnings == warnings

    def test_failure(self):
        """Test creating a failure result."""
        errors = [{"path": "/info", "message": "Missing field"}]
        result = ValidationResult.failure(errors)
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0]["message"] == "Missing field"

    def test_failure_with_key(self):
        """Test creating a failure result with validation key."""
        key = SpecificationKey(
            spec_type=SpecificationType.OPENAPI_3_0, version="3.0.3"
        )
        result = ValidationResult.failure([], validated_against=key)
        assert result.validated_against == key

    def test_immutability(self):
        """Test that result is immutable."""
        result = ValidationResult.success()
        with pytest.raises(ValidationError):
            result.is_valid = False
