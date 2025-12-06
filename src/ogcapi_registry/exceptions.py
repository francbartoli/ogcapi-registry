"""Custom exceptions for the OpenAPI Registry Validator library."""

from typing import Any


class OpenAPIRegistryError(Exception):
    """Base exception for all library errors."""

    pass


class FetchError(OpenAPIRegistryError):
    """Raised when fetching a remote OpenAPI specification fails."""

    def __init__(self, url: str, reason: str) -> None:
        self.url = url
        self.reason = reason
        super().__init__(f"Failed to fetch OpenAPI spec from '{url}': {reason}")


class ParseError(OpenAPIRegistryError):
    """Raised when parsing an OpenAPI specification fails."""

    def __init__(self, reason: str, source: str | None = None) -> None:
        self.reason = reason
        self.source = source
        msg = f"Failed to parse OpenAPI spec: {reason}"
        if source:
            msg += f" (source: {source})"
        super().__init__(msg)


class RegistryError(OpenAPIRegistryError):
    """Raised when a registry operation fails."""

    pass


class SpecificationNotFoundError(RegistryError):
    """Raised when a specification is not found in the registry."""

    def __init__(self, spec_type: str, version: str) -> None:
        self.spec_type = spec_type
        self.version = version
        super().__init__(
            f"Specification not found: type='{spec_type}', version='{version}'"
        )


class SpecificationAlreadyExistsError(RegistryError):
    """Raised when trying to register a specification that already exists."""

    def __init__(self, spec_type: str, version: str) -> None:
        self.spec_type = spec_type
        self.version = version
        super().__init__(
            f"Specification already exists: type='{spec_type}', version='{version}'"
        )


class ValidationError(OpenAPIRegistryError):
    """Raised when validation of an OpenAPI document fails."""

    def __init__(self, errors: list[dict[str, Any]]) -> None:
        self.errors = errors
        error_count = len(errors)
        super().__init__(f"Validation failed with {error_count} error(s)")

    def __str__(self) -> str:
        lines = [f"Validation failed with {len(self.errors)} error(s):"]
        for i, error in enumerate(self.errors, 1):
            path = error.get("path", "")
            message = error.get("message", "Unknown error")
            lines.append(f"  {i}. [{path}] {message}")
        return "\n".join(lines)
