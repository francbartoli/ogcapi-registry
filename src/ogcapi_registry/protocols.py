"""Protocol definitions for structural subtyping (duck typing).

This module defines Protocol classes that enable duck typing throughout
the library. Classes don't need to explicitly inherit from these protocols
to be compatible - they just need to implement the required methods.

Usage:
    from ogcapi_registry.protocols import ValidationStrategyProtocol

    def validate_with_strategy(
        strategy: ValidationStrategyProtocol,
        document: dict,
    ) -> ValidationResult:
        return strategy.validate(document, [])
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, TypeVar, runtime_checkable

if TYPE_CHECKING:
    from .models import SpecificationMetadata, ValidationResult
    from .ogc_types import ConformanceClass, OGCAPIType, OGCSpecificationKey

# Type variables for generic protocols
K = TypeVar("K")  # Key type (invariant - used in input and output)
V_co = TypeVar(
    "V_co", covariant=True
)  # Value type (covariant - only in return positions)
T = TypeVar("T", covariant=True)  # Covariant type for returns


@runtime_checkable
class ValidationStrategyProtocol(Protocol):
    """Protocol for validation strategies.

    Any class implementing these methods can be used as a validation strategy,
    without needing to inherit from ValidationStrategy.

    Example:
        class CustomStrategy:
            api_type = OGCAPIType.FEATURES

            def validate(self, document, conformance_classes):
                # Custom validation logic
                return ValidationResult.success()

            def get_required_paths(self, conformance_classes):
                return ["/collections"]

            def get_required_operations(self, conformance_classes):
                return {"/collections": ["get"]}

            def matches_conformance(self, conformance_classes):
                return True

            def get_conformance_score(self, conformance_classes):
                return 1

            def supports_version(self, spec_version):
                return True

        # CustomStrategy can be used anywhere ValidationStrategyProtocol is expected
    """

    @property
    def api_type(self) -> "OGCAPIType":
        """The OGC API type this strategy handles."""
        ...

    def validate(
        self,
        document: dict[str, Any],
        conformance_classes: list["ConformanceClass"],
    ) -> "ValidationResult":
        """Validate an OpenAPI document."""
        ...

    def get_required_paths(
        self,
        conformance_classes: list["ConformanceClass"],
    ) -> list[str]:
        """Get required API paths for validation."""
        ...

    def get_required_operations(
        self,
        conformance_classes: list["ConformanceClass"],
    ) -> dict[str, list[str]]:
        """Get required HTTP operations for each path."""
        ...

    def matches_conformance(
        self,
        conformance_classes: list["ConformanceClass"],
    ) -> bool:
        """Check if this strategy matches the given conformance classes."""
        ...

    def get_conformance_score(
        self,
        conformance_classes: list["ConformanceClass"],
    ) -> int:
        """Calculate a score indicating how well this strategy matches."""
        ...

    def supports_version(self, spec_version: str) -> bool:
        """Check if this strategy supports a specific specification version."""
        ...


@runtime_checkable
class VersionAwareStrategyProtocol(ValidationStrategyProtocol, Protocol):
    """Extended protocol for version-aware validation strategies.

    Adds methods for checking version support and extracting
    specification information from conformance classes.
    """

    def supports_version(self, spec_version: str) -> bool:
        """Check if this strategy supports a specific specification version."""
        ...

    def get_spec_version_from_conformance(
        self,
        conformance_classes: list["ConformanceClass"],
    ) -> str | None:
        """Extract the specification version from conformance classes."""
        ...

    def get_specification_key(
        self,
        conformance_classes: list["ConformanceClass"],
    ) -> "OGCSpecificationKey | None":
        """Get the OGC specification key for validation."""
        ...


class RegistryProtocol(Protocol[K, V_co]):
    """Generic protocol for specification registries.

    Note: This protocol is not @runtime_checkable because generic protocols
    with type variables cannot be reliably checked at runtime with isinstance().

    This protocol defines the common interface for all registry types,
    enabling duck typing for registry implementations.

    Type Parameters:
        K: The key type (e.g., SpecificationKey, OGCSpecificationKey)
        V: The value type (e.g., RegisteredSpecification, OGCRegisteredSpecification)

    Example:
        class InMemoryRegistry:
            def __init__(self):
                self._data = {}

            def get_by_key(self, key):
                return self._data[key]

            def exists_by_key(self, key):
                return key in self._data

            # ... implement other methods

        # InMemoryRegistry can be used anywhere RegistryProtocol is expected
    """

    def get_by_key(self, key: K) -> V_co:
        """Get a specification by its key."""
        ...

    def exists_by_key(self, key: K) -> bool:
        """Check if a specification exists."""
        ...

    def remove_by_key(self, key: K) -> bool:
        """Remove a specification by its key."""
        ...

    def list_keys(self) -> list[K]:
        """List all keys in the registry."""
        ...

    def clear(self) -> None:
        """Remove all specifications from the registry."""
        ...

    def __len__(self) -> int:
        """Get the number of specifications in the registry."""
        ...

    def __contains__(self, key: K) -> bool:
        """Check if a key exists in the registry."""
        ...


@runtime_checkable
class OpenAPIClientProtocol(Protocol):
    """Protocol for OpenAPI fetching clients.

    Any class implementing these methods can be used to fetch
    OpenAPI specifications, without inheriting from OpenAPIClient.

    Example:
        class CachedClient:
            def __init__(self, cache_dir: str):
                self._cache = {}

            def fetch(self, url: str):
                if url in self._cache:
                    return self._cache[url]
                # Fetch from network...

            def fetch_and_validate_structure(self, url: str):
                content, metadata = self.fetch(url)
                # Validate...
                return content, metadata

        # CachedClient can be used anywhere OpenAPIClientProtocol is expected
    """

    def fetch(
        self,
        url: str,
    ) -> tuple[dict[str, Any], "SpecificationMetadata"]:
        """Fetch an OpenAPI specification from a URL.

        Args:
            url: The URL to fetch from

        Returns:
            Tuple of (parsed content dict, metadata)
        """
        ...

    def fetch_and_validate_structure(
        self,
        url: str,
    ) -> tuple[dict[str, Any], "SpecificationMetadata"]:
        """Fetch and validate the basic structure of an OpenAPI specification.

        Args:
            url: The URL to fetch from

        Returns:
            Tuple of (parsed content dict, metadata)

        Raises:
            ParseError: If the document structure is invalid
        """
        ...


@runtime_checkable
class AsyncOpenAPIClientProtocol(Protocol):
    """Protocol for async OpenAPI fetching clients.

    Async version of OpenAPIClientProtocol for use with asyncio.
    """

    async def fetch(
        self,
        url: str,
    ) -> tuple[dict[str, Any], "SpecificationMetadata"]:
        """Fetch an OpenAPI specification from a URL asynchronously."""
        ...

    async def fetch_and_validate_structure(
        self,
        url: str,
    ) -> tuple[dict[str, Any], "SpecificationMetadata"]:
        """Fetch and validate an OpenAPI specification asynchronously."""
        ...


@runtime_checkable
class ConformanceClassProtocol(Protocol):
    """Protocol for conformance class objects.

    Enables duck typing for any object that represents an OGC conformance class.
    """

    @property
    def uri(self) -> str:
        """The conformance class URI."""
        ...

    @property
    def api_type(self) -> "OGCAPIType":
        """The detected OGC API type."""
        ...

    @property
    def is_core(self) -> bool:
        """Whether this is a core conformance class."""
        ...


@runtime_checkable
class SpecificationKeyProtocol(Protocol):
    """Protocol for specification key objects.

    Enables duck typing for any object that can serve as a specification key.
    """

    def __hash__(self) -> int:
        """Keys must be hashable for use in dicts/sets."""
        ...

    def __eq__(self, other: object) -> bool:
        """Keys must support equality comparison."""
        ...


# Type aliases for common protocol combinations
AnyStrategy = ValidationStrategyProtocol | VersionAwareStrategyProtocol
AnyClient = OpenAPIClientProtocol | AsyncOpenAPIClientProtocol
