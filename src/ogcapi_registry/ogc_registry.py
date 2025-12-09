"""OGC Specification Registry for storing OGC API reference specifications.

This module provides a registry for storing and retrieving OGC API
specifications indexed by API type, version, and part number.
"""

import threading
from datetime import datetime, timezone
from typing import Any

from .exceptions import SpecificationAlreadyExistsError, SpecificationNotFoundError
from .models import SpecificationMetadata
from .ogc_types import OGCAPIType, OGCSpecificationKey


class OGCRegisteredSpecification:
    """A registered OGC API specification with metadata.

    This class represents a complete OGC API specification stored in the registry,
    including the raw OpenAPI document and metadata about when/where it was fetched.
    """

    def __init__(
        self,
        key: OGCSpecificationKey,
        raw_content: dict[str, Any],
        metadata: SpecificationMetadata | None = None,
    ):
        """Initialize a registered specification.

        Args:
            key: The OGC specification key (type, version, part)
            raw_content: The raw OpenAPI document as a dictionary
            metadata: Optional metadata about the specification source
        """
        self._key = key
        self._raw_content = raw_content
        self._metadata = metadata or SpecificationMetadata(
            fetched_at=datetime.now(timezone.utc)
        )

    @property
    def key(self) -> OGCSpecificationKey:
        """Get the specification key."""
        return self._key

    @property
    def raw_content(self) -> dict[str, Any]:
        """Get the raw OpenAPI document."""
        return self._raw_content

    @property
    def metadata(self) -> SpecificationMetadata:
        """Get the specification metadata."""
        return self._metadata

    @property
    def openapi_version(self) -> str:
        """Get the OpenAPI version from the document."""
        return self._raw_content.get("openapi", "")

    @property
    def info_title(self) -> str:
        """Get the title from the document info."""
        info = self._raw_content.get("info", {})
        return info.get("title", "")

    @property
    def info_version(self) -> str:
        """Get the version from the document info."""
        info = self._raw_content.get("info", {})
        return info.get("version", "")

    @property
    def paths(self) -> dict[str, Any]:
        """Get the paths from the OpenAPI document."""
        return self._raw_content.get("paths", {})

    def __repr__(self) -> str:
        return f"OGCRegisteredSpecification(key={self._key})"


class OGCSpecificationRegistry:
    """Thread-safe registry for OGC API reference specifications.

    This registry stores OGC API specifications indexed by their type, version,
    and part number. It provides methods to:
    - Register specifications manually or from remote URLs
    - Retrieve specifications by exact key or latest version
    - List available specifications by API type
    """

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._specs: dict[OGCSpecificationKey, OGCRegisteredSpecification] = {}
        self._lock = threading.RLock()

    def register(
        self,
        api_type: OGCAPIType,
        spec_version: str,
        raw_content: dict[str, Any],
        part: int | None = None,
        metadata: SpecificationMetadata | None = None,
        overwrite: bool = False,
    ) -> OGCRegisteredSpecification:
        """Register an OGC API specification.

        Args:
            api_type: The OGC API type (Features, Tiles, EDR, etc.)
            spec_version: The specification version (e.g., "1.0", "1.1")
            raw_content: The raw OpenAPI document as a dictionary
            part: Optional part number for multi-part specifications
            metadata: Optional metadata about the specification source
            overwrite: If True, overwrite existing specification

        Returns:
            The registered specification

        Raises:
            SpecificationAlreadyExistsError: If specification exists and overwrite=False
        """
        key = OGCSpecificationKey(
            api_type=api_type,
            spec_version=spec_version,
            part=part,
        )

        with self._lock:
            if key in self._specs and not overwrite:
                raise SpecificationAlreadyExistsError(
                    spec_type=str(key.api_type.value),
                    version=key.spec_version,
                )

            spec = OGCRegisteredSpecification(
                key=key,
                raw_content=raw_content,
                metadata=metadata,
            )
            self._specs[key] = spec
            return spec

    def register_from_url(
        self,
        api_type: OGCAPIType,
        spec_version: str,
        url: str,
        part: int | None = None,
        overwrite: bool = False,
    ) -> OGCRegisteredSpecification:
        """Register an OGC API specification from a remote URL.

        Args:
            api_type: The OGC API type (Features, Tiles, EDR, etc.)
            spec_version: The specification version (e.g., "1.0", "1.1")
            url: The URL to fetch the specification from
            part: Optional part number for multi-part specifications
            overwrite: If True, overwrite existing specification

        Returns:
            The registered specification
        """
        from .client import OpenAPIClient

        client = OpenAPIClient()
        raw_content, metadata = client.fetch(url)

        return self.register(
            api_type=api_type,
            spec_version=spec_version,
            raw_content=raw_content,
            part=part,
            metadata=metadata,
            overwrite=overwrite,
        )

    def get(
        self,
        api_type: OGCAPIType,
        spec_version: str,
        part: int | None = None,
    ) -> OGCRegisteredSpecification:
        """Get a specification by its key components.

        Args:
            api_type: The OGC API type
            spec_version: The specification version
            part: Optional part number

        Returns:
            The registered specification

        Raises:
            SpecificationNotFoundError: If specification not found
        """
        key = OGCSpecificationKey(
            api_type=api_type,
            spec_version=spec_version,
            part=part,
        )
        return self.get_by_key(key)

    def get_by_key(self, key: OGCSpecificationKey) -> OGCRegisteredSpecification:
        """Get a specification by its key.

        Args:
            key: The specification key

        Returns:
            The registered specification

        Raises:
            SpecificationNotFoundError: If specification not found
        """
        with self._lock:
            if key not in self._specs:
                raise SpecificationNotFoundError(
                    spec_type=str(key.api_type.value),
                    version=key.spec_version,
                )
            return self._specs[key]

    def get_latest(
        self,
        api_type: OGCAPIType,
        part: int | None = None,
    ) -> OGCRegisteredSpecification:
        """Get the latest version of a specification.

        Args:
            api_type: The OGC API type
            part: Optional part number to filter by

        Returns:
            The latest registered specification

        Raises:
            SpecificationNotFoundError: If no specifications found
        """
        with self._lock:
            matching = [
                spec
                for spec in self._specs.values()
                if spec.key.api_type == api_type
                and (part is None or spec.key.part == part)
            ]

            if not matching:
                raise SpecificationNotFoundError(
                    spec_type=str(api_type.value),
                    version="*",  # Any version
                )

            # Sort by version (semantic versioning comparison)
            def version_key(spec: OGCRegisteredSpecification) -> tuple[int, ...]:
                parts = spec.key.spec_version.split(".")
                return tuple(int(p) for p in parts)

            matching.sort(key=version_key, reverse=True)
            return matching[0]

    def exists(
        self,
        api_type: OGCAPIType,
        spec_version: str,
        part: int | None = None,
    ) -> bool:
        """Check if a specification exists in the registry.

        Args:
            api_type: The OGC API type
            spec_version: The specification version
            part: Optional part number

        Returns:
            True if specification exists
        """
        key = OGCSpecificationKey(
            api_type=api_type,
            spec_version=spec_version,
            part=part,
        )
        with self._lock:
            return key in self._specs

    def remove(
        self,
        api_type: OGCAPIType,
        spec_version: str,
        part: int | None = None,
    ) -> bool:
        """Remove a specification from the registry.

        Args:
            api_type: The OGC API type
            spec_version: The specification version
            part: Optional part number

        Returns:
            True if specification was removed, False if not found
        """
        key = OGCSpecificationKey(
            api_type=api_type,
            spec_version=spec_version,
            part=part,
        )
        with self._lock:
            if key in self._specs:
                del self._specs[key]
                return True
            return False

    def list_versions(self, api_type: OGCAPIType) -> list[str]:
        """List all versions of a specific API type.

        Args:
            api_type: The OGC API type

        Returns:
            List of version strings, sorted in descending order
        """
        with self._lock:
            versions = set(
                spec.key.spec_version
                for spec in self._specs.values()
                if spec.key.api_type == api_type
            )

            def version_key(v: str) -> tuple[int, ...]:
                parts = v.split(".")
                return tuple(int(p) for p in parts)

            return sorted(versions, key=version_key, reverse=True)

    def list_by_type(
        self,
        api_type: OGCAPIType,
    ) -> list[OGCRegisteredSpecification]:
        """List all specifications of a specific API type.

        Args:
            api_type: The OGC API type

        Returns:
            List of specifications, sorted by version descending
        """
        with self._lock:
            matching = [
                spec for spec in self._specs.values() if spec.key.api_type == api_type
            ]

            def version_key(spec: OGCRegisteredSpecification) -> tuple[int, ...]:
                parts = spec.key.spec_version.split(".")
                return tuple(int(p) for p in parts)

            return sorted(matching, key=version_key, reverse=True)

    def list_keys(self) -> list[OGCSpecificationKey]:
        """List all specification keys in the registry.

        Returns:
            List of specification keys
        """
        with self._lock:
            return list(self._specs.keys())

    def list_specifications(self) -> list[OGCRegisteredSpecification]:
        """List all specifications in the registry.

        Returns:
            List of all registered specifications
        """
        with self._lock:
            return list(self._specs.values())

    def clear(self) -> None:
        """Remove all specifications from the registry."""
        with self._lock:
            self._specs.clear()

    def __len__(self) -> int:
        """Get the number of specifications in the registry."""
        with self._lock:
            return len(self._specs)

    def __contains__(self, key: OGCSpecificationKey) -> bool:
        """Check if a specification key exists in the registry."""
        with self._lock:
            return key in self._specs

    def __iter__(self):
        """Iterate over specification keys in the registry."""
        with self._lock:
            return iter(list(self._specs.keys()))


# Known OGC API specification URLs for auto-registration
OGC_SPEC_URLS: dict[OGCSpecificationKey, str] = {
    # OGC API - Features Part 1
    OGCSpecificationKey(
        api_type=OGCAPIType.FEATURES,
        spec_version="1.0",
        part=1,
    ): "https://schemas.opengis.net/ogcapi/features/part1/1.0/openapi/ogcapi-features-1.yaml",
    # OGC API - Common Part 1
    OGCSpecificationKey(
        api_type=OGCAPIType.COMMON,
        spec_version="1.0",
        part=1,
    ): "https://schemas.opengis.net/ogcapi/common/part1/1.0/openapi/ogcapi-common-1.yaml",
    # OGC API - Common Part 2
    OGCSpecificationKey(
        api_type=OGCAPIType.COMMON,
        spec_version="1.0",
        part=2,
    ): "https://schemas.opengis.net/ogcapi/common/part2/1.0/openapi/ogcapi-common-2.yaml",
    # OGC API - EDR
    OGCSpecificationKey(
        api_type=OGCAPIType.EDR,
        spec_version="1.1",
        part=1,
    ): "https://schemas.opengis.net/ogcapi/edr/1.1/openapi/ogcapi-edr-1.yaml",
    # OGC API - Processes Part 1
    OGCSpecificationKey(
        api_type=OGCAPIType.PROCESSES,
        spec_version="1.0",
        part=1,
    ): "https://schemas.opengis.net/ogcapi/processes/part1/1.0/openapi/ogcapi-processes-1.yaml",
}


def create_default_ogc_registry() -> OGCSpecificationRegistry:
    """Create an empty OGC specification registry.

    Returns:
        A new empty OGCSpecificationRegistry instance
    """
    return OGCSpecificationRegistry()


def populate_ogc_registry(
    registry: OGCSpecificationRegistry | None = None,
    specs: list[OGCSpecificationKey] | None = None,
) -> OGCSpecificationRegistry:
    """Populate an OGC registry with official specifications from remote URLs.

    Args:
        registry: Optional existing registry to populate (creates new if None)
        specs: Optional list of specification keys to fetch (fetches all known if None)

    Returns:
        The populated registry
    """
    if registry is None:
        registry = OGCSpecificationRegistry()

    keys_to_fetch = specs if specs is not None else list(OGC_SPEC_URLS.keys())

    for key in keys_to_fetch:
        if key in OGC_SPEC_URLS:
            url = OGC_SPEC_URLS[key]
            try:
                registry.register_from_url(
                    api_type=key.api_type,
                    spec_version=key.spec_version,
                    url=url,
                    part=key.part,
                    overwrite=True,
                )
            except Exception:
                # Skip specs that fail to fetch
                pass

    return registry
