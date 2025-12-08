"""In-memory registry for OpenAPI specifications."""

import threading
from typing import Iterator

from .client import AsyncOpenAPIClient, OpenAPIClient
from .exceptions import (
    SpecificationAlreadyExistsError,
    SpecificationNotFoundError,
)
from .models import (
    RegisteredSpecification,
    SpecificationKey,
    SpecificationMetadata,
    SpecificationType,
)


class SpecificationRegistry:
    """Thread-safe in-memory registry for OpenAPI specifications.

    This registry stores immutable OpenAPI specifications indexed by their
    type and version. It supports both direct registration and fetching
    from remote URLs.
    """

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._specifications: dict[SpecificationKey, RegisteredSpecification] = {}
        self._lock = threading.RLock()
        self._client = OpenAPIClient()

    def register(
        self,
        content: dict,
        spec_type: SpecificationType,
        version: str,
        metadata: SpecificationMetadata | None = None,
        overwrite: bool = False,
    ) -> RegisteredSpecification:
        """Register an OpenAPI specification in the registry.

        Args:
            content: Parsed OpenAPI specification content
            spec_type: Type of the specification (e.g., OPENAPI_3_0)
            version: Version string (e.g., "3.0.3")
            metadata: Optional metadata about the specification
            overwrite: If True, overwrite existing specification

        Returns:
            The registered specification

        Raises:
            SpecificationAlreadyExistsError: If specification exists and overwrite=False
        """
        key = SpecificationKey(spec_type=spec_type, version=version)

        if metadata is None:
            metadata = SpecificationMetadata()

        spec = RegisteredSpecification(
            key=key,
            metadata=metadata,
            raw_content=content,
        )

        with self._lock:
            if key in self._specifications and not overwrite:
                raise SpecificationAlreadyExistsError(spec_type.value, version)
            self._specifications[key] = spec

        return spec

    def register_from_url(
        self,
        url: str,
        spec_type: SpecificationType | None = None,
        version: str | None = None,
        overwrite: bool = False,
    ) -> RegisteredSpecification:
        """Fetch and register an OpenAPI specification from a URL.

        If spec_type or version are not provided, they will be inferred
        from the fetched specification content.

        Args:
            url: URL to fetch the specification from
            spec_type: Optional specification type (inferred if not provided)
            version: Optional version string (inferred if not provided)
            overwrite: If True, overwrite existing specification

        Returns:
            The registered specification

        Raises:
            FetchError: If fetching fails
            ParseError: If parsing fails
            SpecificationAlreadyExistsError: If specification exists and overwrite=False
        """
        content, metadata = self._client.fetch_and_validate_structure(url)

        # Infer type and version from content if not provided
        openapi_version = content["openapi"]
        if spec_type is None:
            spec_type = SpecificationType.from_version(openapi_version)
        if version is None:
            version = openapi_version

        return self.register(
            content=content,
            spec_type=spec_type,
            version=version,
            metadata=metadata,
            overwrite=overwrite,
        )

    def get(
        self, spec_type: SpecificationType, version: str
    ) -> RegisteredSpecification:
        """Get a specification from the registry.

        Args:
            spec_type: Type of the specification
            version: Version string

        Returns:
            The registered specification

        Raises:
            SpecificationNotFoundError: If the specification is not found
        """
        key = SpecificationKey(spec_type=spec_type, version=version)
        with self._lock:
            if key not in self._specifications:
                raise SpecificationNotFoundError(spec_type.value, version)
            return self._specifications[key]

    def get_by_key(self, key: SpecificationKey) -> RegisteredSpecification:
        """Get a specification from the registry by key.

        Args:
            key: The specification key

        Returns:
            The registered specification

        Raises:
            SpecificationNotFoundError: If the specification is not found
        """
        with self._lock:
            if key not in self._specifications:
                raise SpecificationNotFoundError(key.spec_type.value, key.version)
            return self._specifications[key]

    def exists(self, spec_type: SpecificationType, version: str) -> bool:
        """Check if a specification exists in the registry.

        Args:
            spec_type: Type of the specification
            version: Version string

        Returns:
            True if the specification exists, False otherwise
        """
        key = SpecificationKey(spec_type=spec_type, version=version)
        with self._lock:
            return key in self._specifications

    def remove(self, spec_type: SpecificationType, version: str) -> bool:
        """Remove a specification from the registry.

        Args:
            spec_type: Type of the specification
            version: Version string

        Returns:
            True if the specification was removed, False if it didn't exist
        """
        key = SpecificationKey(spec_type=spec_type, version=version)
        with self._lock:
            if key in self._specifications:
                del self._specifications[key]
                return True
            return False

    def clear(self) -> None:
        """Remove all specifications from the registry."""
        with self._lock:
            self._specifications.clear()

    def list_keys(self) -> list[SpecificationKey]:
        """List all specification keys in the registry.

        Returns:
            List of all specification keys
        """
        with self._lock:
            return list(self._specifications.keys())

    def list_specifications(self) -> list[RegisteredSpecification]:
        """List all specifications in the registry.

        Returns:
            List of all registered specifications
        """
        with self._lock:
            return list(self._specifications.values())

    def __len__(self) -> int:
        """Return the number of specifications in the registry."""
        with self._lock:
            return len(self._specifications)

    def __iter__(self) -> Iterator[RegisteredSpecification]:
        """Iterate over all specifications in the registry."""
        with self._lock:
            # Return a copy to avoid modification during iteration
            return iter(list(self._specifications.values()))

    def __contains__(self, key: SpecificationKey) -> bool:
        """Check if a key exists in the registry."""
        with self._lock:
            return key in self._specifications


class AsyncSpecificationRegistry:
    """Async-compatible in-memory registry for OpenAPI specifications.

    This registry provides async methods for fetching specifications
    while maintaining a synchronous internal store.
    """

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._sync_registry = SpecificationRegistry()
        self._async_client = AsyncOpenAPIClient()

    def register(
        self,
        content: dict,
        spec_type: SpecificationType,
        version: str,
        metadata: SpecificationMetadata | None = None,
        overwrite: bool = False,
    ) -> RegisteredSpecification:
        """Register an OpenAPI specification in the registry.

        This method is synchronous as it doesn't involve I/O.

        Args:
            content: Parsed OpenAPI specification content
            spec_type: Type of the specification
            version: Version string
            metadata: Optional metadata about the specification
            overwrite: If True, overwrite existing specification

        Returns:
            The registered specification
        """
        return self._sync_registry.register(
            content=content,
            spec_type=spec_type,
            version=version,
            metadata=metadata,
            overwrite=overwrite,
        )

    async def register_from_url(
        self,
        url: str,
        spec_type: SpecificationType | None = None,
        version: str | None = None,
        overwrite: bool = False,
    ) -> RegisteredSpecification:
        """Fetch and register an OpenAPI specification from a URL asynchronously.

        Args:
            url: URL to fetch the specification from
            spec_type: Optional specification type (inferred if not provided)
            version: Optional version string (inferred if not provided)
            overwrite: If True, overwrite existing specification

        Returns:
            The registered specification
        """
        (
            content,
            metadata,
        ) = await self._async_client.fetch_and_validate_structure(url)

        # Infer type and version from content if not provided
        openapi_version = content["openapi"]
        if spec_type is None:
            spec_type = SpecificationType.from_version(openapi_version)
        if version is None:
            version = openapi_version

        return self.register(
            content=content,
            spec_type=spec_type,
            version=version,
            metadata=metadata,
            overwrite=overwrite,
        )

    def get(
        self, spec_type: SpecificationType, version: str
    ) -> RegisteredSpecification:
        """Get a specification from the registry."""
        return self._sync_registry.get(spec_type, version)

    def get_by_key(self, key: SpecificationKey) -> RegisteredSpecification:
        """Get a specification from the registry by key."""
        return self._sync_registry.get_by_key(key)

    def exists(self, spec_type: SpecificationType, version: str) -> bool:
        """Check if a specification exists in the registry."""
        return self._sync_registry.exists(spec_type, version)

    def remove(self, spec_type: SpecificationType, version: str) -> bool:
        """Remove a specification from the registry."""
        return self._sync_registry.remove(spec_type, version)

    def clear(self) -> None:
        """Remove all specifications from the registry."""
        self._sync_registry.clear()

    def list_keys(self) -> list[SpecificationKey]:
        """List all specification keys in the registry."""
        return self._sync_registry.list_keys()

    def list_specifications(self) -> list[RegisteredSpecification]:
        """List all specifications in the registry."""
        return self._sync_registry.list_specifications()

    def __len__(self) -> int:
        """Return the number of specifications in the registry."""
        return len(self._sync_registry)

    def __iter__(self) -> Iterator[RegisteredSpecification]:
        """Iterate over all specifications in the registry."""
        return iter(self._sync_registry)

    def __contains__(self, key: SpecificationKey) -> bool:
        """Check if a key exists in the registry."""
        return key in self._sync_registry
