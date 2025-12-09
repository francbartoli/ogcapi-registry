"""HTTP client for fetching remote OpenAPI specifications."""

from typing import Any

import httpx
import yaml

from .exceptions import FetchError, ParseError
from .models import SpecificationMetadata


class OpenAPIClient:
    """Client for fetching OpenAPI specifications from remote URLs.

    This client supports both JSON and YAML formats and handles
    content negotiation automatically.
    """

    SUPPORTED_CONTENT_TYPES = {
        "application/json",
        "application/yaml",
        "application/x-yaml",
        "text/yaml",
        "text/x-yaml",
        "text/plain",
        "application/vnd.oai.openapi",
        "application/vnd.oai.openapi+json",
        "application/vnd.oai.openapi+yaml",
    }

    DEFAULT_TIMEOUT = 30.0

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
        headers: dict[str, str] | None = None,
        follow_redirects: bool = True,
    ) -> None:
        """Initialize the OpenAPI client.

        Args:
            timeout: Request timeout in seconds
            headers: Additional headers to send with requests
            follow_redirects: Whether to follow HTTP redirects
        """
        self._timeout = timeout
        self._headers = headers or {}
        self._follow_redirects = follow_redirects

    def _create_client(self) -> httpx.Client:
        """Create a configured httpx client."""
        default_headers = {
            "Accept": "application/json, application/yaml, application/vnd.oai.openapi+json, application/vnd.oai.openapi+yaml, */*",
            "User-Agent": "openapi-registry-validator/0.1.0",
        }
        default_headers.update(self._headers)

        return httpx.Client(
            timeout=self._timeout,
            headers=default_headers,
            follow_redirects=self._follow_redirects,
        )

    def _parse_content(
        self, content: bytes, content_type: str | None, url: str
    ) -> dict[str, Any]:
        """Parse response content as JSON or YAML.

        Args:
            content: Raw response content
            content_type: Content-Type header value
            url: Original URL (used for error messages and format detection)

        Returns:
            Parsed content as a dictionary

        Raises:
            ParseError: If parsing fails
        """
        content_str = content.decode("utf-8")

        # Determine format from content type or URL
        is_yaml = False
        if content_type:
            content_type_lower = content_type.lower()
            if "yaml" in content_type_lower:
                is_yaml = True
            elif "json" in content_type_lower:
                is_yaml = False
        else:
            # Fall back to URL extension
            url_lower = url.lower()
            if url_lower.endswith((".yaml", ".yml")):
                is_yaml = True

        # Try parsing
        try:
            if is_yaml:
                result = yaml.safe_load(content_str)
            else:
                # Try JSON first, fall back to YAML
                import json

                try:
                    result = json.loads(content_str)
                except json.JSONDecodeError:
                    # YAML is a superset of JSON, so try YAML
                    result = yaml.safe_load(content_str)

            if not isinstance(result, dict):
                raise ParseError(
                    "OpenAPI specification must be a JSON/YAML object",
                    source=url,
                )

            return result

        except yaml.YAMLError as e:
            raise ParseError(f"Invalid YAML: {e}", source=url)
        except Exception as e:
            raise ParseError(str(e), source=url)

    def fetch(self, url: str) -> tuple[dict[str, Any], SpecificationMetadata]:
        """Fetch an OpenAPI specification from a URL.

        Args:
            url: The URL to fetch the specification from

        Returns:
            A tuple of (parsed_content, metadata)

        Raises:
            FetchError: If the HTTP request fails
            ParseError: If parsing the response fails
        """
        with self._create_client() as client:
            try:
                response = client.get(url)
                response.raise_for_status()
            except httpx.TimeoutException:
                raise FetchError(url, "Request timed out")
            except httpx.HTTPStatusError as e:
                raise FetchError(url, f"HTTP {e.response.status_code}")
            except httpx.RequestError as e:
                raise FetchError(url, str(e))

            content_type = (
                response.headers.get("content-type", "").split(";")[0].strip()
            )
            etag = response.headers.get("etag")

            content = self._parse_content(response.content, content_type, url)

            metadata = SpecificationMetadata(
                source_url=url,
                content_type=content_type or None,
                etag=etag,
            )

            return content, metadata

    def fetch_and_validate_structure(
        self, url: str
    ) -> tuple[dict[str, Any], SpecificationMetadata]:
        """Fetch and perform basic structural validation of an OpenAPI spec.

        This method fetches the specification and verifies it has the required
        'openapi' and 'info' fields.

        Args:
            url: The URL to fetch the specification from

        Returns:
            A tuple of (parsed_content, metadata)

        Raises:
            FetchError: If the HTTP request fails
            ParseError: If parsing or basic validation fails
        """
        content, metadata = self.fetch(url)

        # Basic structural validation
        if "openapi" not in content:
            raise ParseError("Missing required 'openapi' field", source=url)

        openapi_version = content["openapi"]
        if not isinstance(openapi_version, str):
            raise ParseError("'openapi' field must be a string", source=url)

        if not openapi_version.startswith("3."):
            raise ParseError(
                f"Unsupported OpenAPI version: {openapi_version}. Only 3.x is supported.",
                source=url,
            )

        if "info" not in content:
            raise ParseError("Missing required 'info' field", source=url)

        return content, metadata


class AsyncOpenAPIClient:
    """Async client for fetching OpenAPI specifications from remote URLs.

    This client supports both JSON and YAML formats and handles
    content negotiation automatically.
    """

    SUPPORTED_CONTENT_TYPES = OpenAPIClient.SUPPORTED_CONTENT_TYPES
    DEFAULT_TIMEOUT = OpenAPIClient.DEFAULT_TIMEOUT

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
        headers: dict[str, str] | None = None,
        follow_redirects: bool = True,
    ) -> None:
        """Initialize the async OpenAPI client.

        Args:
            timeout: Request timeout in seconds
            headers: Additional headers to send with requests
            follow_redirects: Whether to follow HTTP redirects
        """
        self._timeout = timeout
        self._headers = headers or {}
        self._follow_redirects = follow_redirects

    def _create_client(self) -> httpx.AsyncClient:
        """Create a configured async httpx client."""
        default_headers = {
            "Accept": "application/json, application/yaml, application/vnd.oai.openapi+json, application/vnd.oai.openapi+yaml, */*",
            "User-Agent": "openapi-registry-validator/0.1.0",
        }
        default_headers.update(self._headers)

        return httpx.AsyncClient(
            timeout=self._timeout,
            headers=default_headers,
            follow_redirects=self._follow_redirects,
        )

    def _parse_content(
        self, content: bytes, content_type: str | None, url: str
    ) -> dict[str, Any]:
        """Parse response content as JSON or YAML."""
        # Reuse the sync client's parsing logic
        sync_client = OpenAPIClient()
        return sync_client._parse_content(content, content_type, url)

    async def fetch(self, url: str) -> tuple[dict[str, Any], SpecificationMetadata]:
        """Fetch an OpenAPI specification from a URL asynchronously.

        Args:
            url: The URL to fetch the specification from

        Returns:
            A tuple of (parsed_content, metadata)

        Raises:
            FetchError: If the HTTP request fails
            ParseError: If parsing the response fails
        """
        async with self._create_client() as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
            except httpx.TimeoutException:
                raise FetchError(url, "Request timed out")
            except httpx.HTTPStatusError as e:
                raise FetchError(url, f"HTTP {e.response.status_code}")
            except httpx.RequestError as e:
                raise FetchError(url, str(e))

            content_type = (
                response.headers.get("content-type", "").split(";")[0].strip()
            )
            etag = response.headers.get("etag")

            content = self._parse_content(response.content, content_type, url)

            metadata = SpecificationMetadata(
                source_url=url,
                content_type=content_type or None,
                etag=etag,
            )

            return content, metadata

    async def fetch_and_validate_structure(
        self, url: str
    ) -> tuple[dict[str, Any], SpecificationMetadata]:
        """Fetch and perform basic structural validation of an OpenAPI spec.

        Args:
            url: The URL to fetch the specification from

        Returns:
            A tuple of (parsed_content, metadata)

        Raises:
            FetchError: If the HTTP request fails
            ParseError: If parsing or basic validation fails
        """
        content, metadata = await self.fetch(url)

        # Basic structural validation
        if "openapi" not in content:
            raise ParseError("Missing required 'openapi' field", source=url)

        openapi_version = content["openapi"]
        if not isinstance(openapi_version, str):
            raise ParseError("'openapi' field must be a string", source=url)

        if not openapi_version.startswith("3."):
            raise ParseError(
                f"Unsupported OpenAPI version: {openapi_version}. Only 3.x is supported.",
                source=url,
            )

        if "info" not in content:
            raise ParseError("Missing required 'info' field", source=url)

        return content, metadata
