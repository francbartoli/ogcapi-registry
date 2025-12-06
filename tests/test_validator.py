"""Tests for the validator module."""

import json

import pytest

from ogcapi_registry.exceptions import SpecificationNotFoundError
from ogcapi_registry.models import (
    RegisteredSpecification,
    SpecificationKey,
    SpecificationMetadata,
    SpecificationType,
)
from ogcapi_registry.registry import SpecificationRegistry
from ogcapi_registry.validator import (
    OpenAPIValidator,
    create_validator_with_specs,
    parse_openapi_content,
    validate_against_reference,
    validate_document,
    validate_openapi_structure,
    validate_openapi_with_pydantic,
)


class TestParseOpenAPIContent:
    """Tests for parse_openapi_content function."""

    def test_parse_json(self):
        """Test parsing JSON content."""
        content = (
            '{"openapi": "3.0.3", "info": {"title": "Test", "version": "1.0"}}'
        )
        result = parse_openapi_content(content)
        assert result["openapi"] == "3.0.3"

    def test_parse_yaml(self):
        """Test parsing YAML content."""
        content = "openapi: '3.0.3'\ninfo:\n  title: Test\n  version: '1.0'"
        result = parse_openapi_content(content)
        assert result["openapi"] == "3.0.3"

    def test_parse_bytes(self):
        """Test parsing bytes content."""
        content = b'{"openapi": "3.0.3"}'
        result = parse_openapi_content(content)
        assert result["openapi"] == "3.0.3"

    def test_parse_with_format_hint_json(self):
        """Test parsing with JSON format hint."""
        content = '{"openapi": "3.0.3"}'
        result = parse_openapi_content(content, format_hint="json")
        assert result["openapi"] == "3.0.3"

    def test_parse_with_format_hint_yaml(self):
        """Test parsing with YAML format hint."""
        content = "openapi: '3.0.3'"
        result = parse_openapi_content(content, format_hint="yaml")
        assert result["openapi"] == "3.0.3"


class TestValidateOpenAPIStructure:
    """Tests for validate_openapi_structure function."""

    def test_valid_3_0_spec(self):
        """Test validating a valid OpenAPI 3.0 spec."""
        doc = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }
        result = validate_openapi_structure(doc)
        assert result.is_valid
        assert (
            result.validated_against.spec_type == SpecificationType.OPENAPI_3_0
        )

    def test_valid_3_1_spec(self):
        """Test validating a valid OpenAPI 3.1 spec."""
        doc = {
            "openapi": "3.1.0",
            "info": {"title": "Test API", "version": "1.0.0"},
        }
        result = validate_openapi_structure(doc)
        assert result.is_valid
        assert (
            result.validated_against.spec_type == SpecificationType.OPENAPI_3_1
        )

    def test_missing_openapi_field(self):
        """Test that missing openapi field fails validation."""
        doc = {"info": {"title": "Test", "version": "1.0"}}
        result = validate_openapi_structure(doc)
        assert not result.is_valid
        assert any(e["path"] == "openapi" for e in result.errors)

    def test_missing_info_field(self):
        """Test that missing info field fails validation."""
        doc = {"openapi": "3.0.3", "paths": {}}
        result = validate_openapi_structure(doc)
        assert not result.is_valid

    def test_unsupported_version(self):
        """Test that unsupported version fails validation."""
        doc = {"openapi": "2.0", "info": {"title": "Test", "version": "1.0"}}
        result = validate_openapi_structure(doc)
        assert not result.is_valid
        assert any("unsupported" in e["type"].lower() for e in result.errors)

    def test_version_mismatch_warning(self):
        """Test that version mismatch produces a warning."""
        doc = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0"},
            "paths": {},
        }
        result = validate_openapi_structure(
            doc, target_version=SpecificationType.OPENAPI_3_1
        )
        # Should be valid but with a warning
        assert len(result.warnings) > 0


class TestValidateOpenAPIWithPydantic:
    """Tests for validate_openapi_with_pydantic function."""

    def test_valid_3_1_spec(self):
        """Test validating a valid OpenAPI 3.1 spec with Pydantic."""
        doc = {
            "openapi": "3.1.0",
            "info": {"title": "Test API", "version": "1.0.0"},
        }
        result = validate_openapi_with_pydantic(doc)
        assert result.is_valid

    def test_3_0_spec_skips_pydantic(self):
        """Test that OpenAPI 3.0 specs skip Pydantic validation."""
        doc = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }
        result = validate_openapi_with_pydantic(doc)
        # Should succeed because Pydantic validation is skipped for 3.0
        assert result.is_valid
        assert (
            result.validated_against.spec_type == SpecificationType.OPENAPI_3_0
        )

    def test_invalid_info_3_1(self):
        """Test that invalid info fails Pydantic validation for 3.1."""
        doc = {
            "openapi": "3.1.0",
            "info": {},  # Missing required fields
        }
        result = validate_openapi_with_pydantic(doc)
        assert not result.is_valid
        assert len(result.errors) > 0


class TestValidateAgainstReference:
    """Tests for validate_against_reference function."""

    @pytest.fixture
    def reference_spec(self):
        """Create a reference specification."""
        return RegisteredSpecification(
            key=SpecificationKey(
                spec_type=SpecificationType.OPENAPI_3_0, version="3.0.3"
            ),
            metadata=SpecificationMetadata(),
            raw_content={
                "openapi": "3.0.3",
                "info": {"title": "Reference API", "version": "1.0.0"},
                "paths": {},
            },
        )

    def test_valid_document(self, reference_spec):
        """Test validating a valid document against reference."""
        doc = {
            "openapi": "3.0.3",
            "info": {"title": "My API", "version": "2.0.0"},
            "paths": {},
        }
        result = validate_against_reference(doc, reference_spec)
        assert result.is_valid
        assert result.validated_against == reference_spec.key

    def test_version_type_mismatch(self, reference_spec):
        """Test that different OpenAPI type fails validation."""
        doc = {
            "openapi": "3.1.0",
            "info": {"title": "My API", "version": "2.0.0"},
        }
        result = validate_against_reference(doc, reference_spec)
        assert not result.is_valid
        assert any("type_mismatch" in e["type"] for e in result.errors)

    def test_strict_version_mismatch(self, reference_spec):
        """Test strict mode requires exact version match."""
        doc = {
            "openapi": "3.0.2",  # Different minor version
            "info": {"title": "My API", "version": "2.0.0"},
            "paths": {},
        }
        result = validate_against_reference(doc, reference_spec, strict=True)
        assert not result.is_valid
        assert any("version_mismatch" in e["type"] for e in result.errors)

    def test_missing_openapi_field(self, reference_spec):
        """Test that missing openapi field fails validation."""
        doc = {"info": {"title": "My API", "version": "2.0.0"}}
        result = validate_against_reference(doc, reference_spec)
        assert not result.is_valid


class TestValidateDocument:
    """Tests for validate_document function."""

    def test_validate_dict(self):
        """Test validating a dict document."""
        doc = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }
        result = validate_document(doc)
        assert result.is_valid

    def test_validate_json_string(self):
        """Test validating a JSON string."""
        doc = json.dumps(
            {
                "openapi": "3.0.3",
                "info": {"title": "Test API", "version": "1.0.0"},
                "paths": {},
            }
        )
        result = validate_document(doc)
        assert result.is_valid

    def test_validate_yaml_string(self):
        """Test validating a YAML string."""
        doc = """
openapi: "3.0.3"
info:
  title: Test API
  version: "1.0.0"
paths: {}
"""
        result = validate_document(doc, format_hint="yaml")
        assert result.is_valid

    def test_validate_invalid_parse(self):
        """Test that invalid content fails parsing."""
        result = validate_document("not valid json or yaml: {{{{")
        assert not result.is_valid
        assert any("parse_error" in e["type"] for e in result.errors)

    def test_validate_invalid_structure(self):
        """Test that invalid structure fails validation."""
        doc = {"openapi": "3.0.3"}  # Missing info
        result = validate_document(doc)
        assert not result.is_valid


class TestOpenAPIValidator:
    """Tests for OpenAPIValidator class."""

    @pytest.fixture
    def validator(self):
        """Create a validator with an empty registry."""
        return OpenAPIValidator()

    @pytest.fixture
    def validator_with_spec(self):
        """Create a validator with a pre-loaded specification."""
        registry = SpecificationRegistry()
        registry.register(
            content={
                "openapi": "3.0.3",
                "info": {"title": "Reference", "version": "1.0.0"},
                "paths": {},
            },
            spec_type=SpecificationType.OPENAPI_3_0,
            version="3.0.3",
        )
        return OpenAPIValidator(registry)

    def test_validate(self, validator):
        """Test basic validation."""
        doc = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {},
        }
        result = validator.validate(doc)
        assert result.is_valid

    def test_validate_against(self, validator_with_spec):
        """Test validation against a registered spec."""
        doc = {
            "openapi": "3.0.3",
            "info": {"title": "My API", "version": "2.0.0"},
            "paths": {},
        }
        result = validator_with_spec.validate_against(
            doc, SpecificationType.OPENAPI_3_0, "3.0.3"
        )
        assert result.is_valid

    def test_validate_against_not_found(self, validator):
        """Test that validation against non-existent spec raises error."""
        doc = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {},
        }
        with pytest.raises(SpecificationNotFoundError):
            validator.validate_against(
                doc, SpecificationType.OPENAPI_3_0, "3.0.3"
            )

    def test_validate_against_latest(self, validator_with_spec):
        """Test validation against the latest spec of a type."""
        doc = {
            "openapi": "3.0.3",
            "info": {"title": "My API", "version": "2.0.0"},
            "paths": {},
        }
        result = validator_with_spec.validate_against_latest(
            doc, SpecificationType.OPENAPI_3_0
        )
        assert result.is_valid

    def test_validate_against_latest_not_found(self, validator):
        """Test that validation against latest fails if no specs exist."""
        doc = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {},
        }
        with pytest.raises(SpecificationNotFoundError):
            validator.validate_against_latest(
                doc, SpecificationType.OPENAPI_3_0
            )

    def test_registry_property(self, validator):
        """Test accessing the registry property."""
        assert isinstance(validator.registry, SpecificationRegistry)


class TestCreateValidatorWithSpecs:
    """Tests for create_validator_with_specs function."""

    def test_create_with_url(self, httpx_mock):
        """Test creating a validator with a URL."""
        content = json.dumps(
            {
                "openapi": "3.0.3",
                "info": {"title": "Test API", "version": "1.0.0"},
                "paths": {},
            }
        )
        httpx_mock.add_response(
            url="https://example.com/openapi.json",
            content=content.encode(),
            headers={"content-type": "application/json"},
        )

        validator = create_validator_with_specs(
            "https://example.com/openapi.json"
        )
        assert len(validator.registry) == 1

    def test_create_with_multiple_urls(self, httpx_mock):
        """Test creating a validator with multiple URLs."""
        content_3_0 = json.dumps(
            {
                "openapi": "3.0.3",
                "info": {"title": "API 3.0", "version": "1.0.0"},
                "paths": {},
            }
        )
        content_3_1 = json.dumps(
            {
                "openapi": "3.1.0",
                "info": {"title": "API 3.1", "version": "1.0.0"},
            }
        )

        httpx_mock.add_response(
            url="https://example.com/api-3.0.json",
            content=content_3_0.encode(),
            headers={"content-type": "application/json"},
        )
        httpx_mock.add_response(
            url="https://example.com/api-3.1.json",
            content=content_3_1.encode(),
            headers={"content-type": "application/json"},
        )

        validator = create_validator_with_specs(
            "https://example.com/api-3.0.json",
            "https://example.com/api-3.1.json",
        )
        assert len(validator.registry) == 2
