"""Tests for the client module."""

import json

import pytest
import yaml

from ogcapi_registry.client import AsyncOpenAPIClient, OpenAPIClient
from ogcapi_registry.exceptions import FetchError, ParseError


class TestOpenAPIClient:
    """Tests for OpenAPIClient."""

    @pytest.fixture
    def client(self):
        """Create a client instance."""
        return OpenAPIClient()

    @pytest.fixture
    def valid_openapi_json(self):
        """Return valid OpenAPI JSON content."""
        return json.dumps(
            {
                "openapi": "3.0.3",
                "info": {"title": "Test API", "version": "1.0.0"},
                "paths": {},
            }
        )

    @pytest.fixture
    def valid_openapi_yaml(self):
        """Return valid OpenAPI YAML content."""
        return yaml.dump(
            {
                "openapi": "3.0.3",
                "info": {"title": "Test API", "version": "1.0.0"},
                "paths": {},
            }
        )

    def test_parse_json_content(self, client):
        """Test parsing JSON content."""
        content = b'{"openapi": "3.0.3", "info": {"title": "Test", "version": "1.0"}}'
        result = client._parse_content(content, "application/json", "test.json")
        assert result["openapi"] == "3.0.3"

    def test_parse_yaml_content(self, client):
        """Test parsing YAML content."""
        content = b"openapi: '3.0.3'\ninfo:\n  title: Test\n  version: '1.0'"
        result = client._parse_content(content, "application/yaml", "test.yaml")
        assert result["openapi"] == "3.0.3"

    def test_parse_content_from_url_extension(self, client):
        """Test inferring format from URL extension."""
        content = b"openapi: '3.0.3'\ninfo:\n  title: Test\n  version: '1.0'"
        result = client._parse_content(content, None, "https://example.com/api.yaml")
        assert result["openapi"] == "3.0.3"

    def test_parse_invalid_content(self, client):
        """Test parsing invalid content raises ParseError."""
        with pytest.raises(ParseError, match="must be a JSON/YAML object"):
            client._parse_content(b"[1, 2, 3]", "application/json", "test.json")

    def test_fetch_json(self, httpx_mock, client, valid_openapi_json):
        """Test fetching JSON content."""
        httpx_mock.add_response(
            url="https://example.com/openapi.json",
            content=valid_openapi_json.encode(),
            headers={"content-type": "application/json"},
        )

        content, metadata = client.fetch("https://example.com/openapi.json")
        assert content["openapi"] == "3.0.3"
        assert metadata.source_url == "https://example.com/openapi.json"
        assert metadata.content_type == "application/json"

    def test_fetch_yaml(self, httpx_mock, client, valid_openapi_yaml):
        """Test fetching YAML content."""
        httpx_mock.add_response(
            url="https://example.com/openapi.yaml",
            content=valid_openapi_yaml.encode(),
            headers={"content-type": "application/yaml"},
        )

        content, metadata = client.fetch("https://example.com/openapi.yaml")
        assert content["openapi"] == "3.0.3"
        assert metadata.content_type == "application/yaml"

    def test_fetch_with_etag(self, httpx_mock, client, valid_openapi_json):
        """Test that ETag is captured in metadata."""
        httpx_mock.add_response(
            url="https://example.com/openapi.json",
            content=valid_openapi_json.encode(),
            headers={
                "content-type": "application/json",
                "etag": '"abc123"',
            },
        )

        _, metadata = client.fetch("https://example.com/openapi.json")
        assert metadata.etag == '"abc123"'

    def test_fetch_http_error(self, httpx_mock, client):
        """Test that HTTP errors raise FetchError."""
        httpx_mock.add_response(
            url="https://example.com/openapi.json",
            status_code=404,
        )

        with pytest.raises(FetchError, match="HTTP 404"):
            client.fetch("https://example.com/openapi.json")

    def test_fetch_and_validate_structure_valid(
        self, httpx_mock, client, valid_openapi_json
    ):
        """Test structural validation of valid spec."""
        httpx_mock.add_response(
            url="https://example.com/openapi.json",
            content=valid_openapi_json.encode(),
            headers={"content-type": "application/json"},
        )

        content, _ = client.fetch_and_validate_structure(
            "https://example.com/openapi.json"
        )
        assert content["openapi"] == "3.0.3"

    def test_fetch_and_validate_structure_missing_openapi(self, httpx_mock, client):
        """Test that missing openapi field raises ParseError."""
        invalid = json.dumps({"info": {"title": "Test", "version": "1.0"}})
        httpx_mock.add_response(
            url="https://example.com/openapi.json",
            content=invalid.encode(),
            headers={"content-type": "application/json"},
        )

        with pytest.raises(ParseError, match="Missing required 'openapi' field"):
            client.fetch_and_validate_structure("https://example.com/openapi.json")

    def test_fetch_and_validate_structure_unsupported_version(self, httpx_mock, client):
        """Test that unsupported version raises ParseError."""
        invalid = json.dumps(
            {
                "openapi": "2.0",
                "info": {"title": "Test", "version": "1.0"},
            }
        )
        httpx_mock.add_response(
            url="https://example.com/openapi.json",
            content=invalid.encode(),
            headers={"content-type": "application/json"},
        )

        with pytest.raises(ParseError, match="Unsupported OpenAPI version"):
            client.fetch_and_validate_structure("https://example.com/openapi.json")


class TestAsyncOpenAPIClient:
    """Tests for AsyncOpenAPIClient."""

    @pytest.fixture
    def client(self):
        """Create an async client instance."""
        return AsyncOpenAPIClient()

    @pytest.fixture
    def valid_openapi_json(self):
        """Return valid OpenAPI JSON content."""
        return json.dumps(
            {
                "openapi": "3.0.3",
                "info": {"title": "Test API", "version": "1.0.0"},
                "paths": {},
            }
        )

    @pytest.mark.asyncio
    async def test_fetch_json(self, httpx_mock, client, valid_openapi_json):
        """Test fetching JSON content asynchronously."""
        httpx_mock.add_response(
            url="https://example.com/openapi.json",
            content=valid_openapi_json.encode(),
            headers={"content-type": "application/json"},
        )

        content, metadata = await client.fetch("https://example.com/openapi.json")
        assert content["openapi"] == "3.0.3"
        assert metadata.source_url == "https://example.com/openapi.json"

    @pytest.mark.asyncio
    async def test_fetch_http_error(self, httpx_mock, client):
        """Test that HTTP errors raise FetchError."""
        httpx_mock.add_response(
            url="https://example.com/openapi.json",
            status_code=500,
        )

        with pytest.raises(FetchError, match="HTTP 500"):
            await client.fetch("https://example.com/openapi.json")

    @pytest.mark.asyncio
    async def test_fetch_and_validate_structure(
        self, httpx_mock, client, valid_openapi_json
    ):
        """Test structural validation of valid spec."""
        httpx_mock.add_response(
            url="https://example.com/openapi.json",
            content=valid_openapi_json.encode(),
            headers={"content-type": "application/json"},
        )

        content, _ = await client.fetch_and_validate_structure(
            "https://example.com/openapi.json"
        )
        assert content["openapi"] == "3.0.3"
