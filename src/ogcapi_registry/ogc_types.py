"""OGC API types and conformance class definitions."""

import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class OGCAPIType(str, Enum):
    """Enumeration of OGC API specification types."""

    COMMON = "ogcapi-common"
    FEATURES = "ogcapi-features"
    TILES = "ogcapi-tiles"
    MAPS = "ogcapi-maps"
    PROCESSES = "ogcapi-processes"
    RECORDS = "ogcapi-records"
    COVERAGES = "ogcapi-coverages"
    EDR = "ogcapi-edr"  # Environmental Data Retrieval
    STYLES = "ogcapi-styles"
    ROUTES = "ogcapi-routes"

    @property
    def display_name(self) -> str:
        """Get human-readable name for the API type."""
        names = {
            OGCAPIType.COMMON: "OGC API - Common",
            OGCAPIType.FEATURES: "OGC API - Features",
            OGCAPIType.TILES: "OGC API - Tiles",
            OGCAPIType.MAPS: "OGC API - Maps",
            OGCAPIType.PROCESSES: "OGC API - Processes",
            OGCAPIType.RECORDS: "OGC API - Records",
            OGCAPIType.COVERAGES: "OGC API - Coverages",
            OGCAPIType.EDR: "OGC API - Environmental Data Retrieval",
            OGCAPIType.STYLES: "OGC API - Styles",
            OGCAPIType.ROUTES: "OGC API - Routes",
        }
        return names.get(self, self.value)


class OGCSpecificationKey(BaseModel):
    """Unique key for identifying an OGC API specification by type and version.

    This is an immutable model that serves as a composite key for storing
    and retrieving OGC API specifications. The key consists of:
    - api_type: The OGC API type (Features, Tiles, EDR, etc.)
    - spec_version: The specification version (e.g., "1.0", "1.1")
    - part: Optional part number for multi-part specifications (e.g., Features Part 1, 2, 3)

    Examples:
        - OGC API - Features Part 1 v1.0: (FEATURES, "1.0", 1)
        - OGC API - EDR v1.1: (EDR, "1.1", None)
        - OGC API - Common Part 2 v1.0: (COMMON, "1.0", 2)
    """

    model_config = {"frozen": True}

    api_type: OGCAPIType = Field(
        ..., description="The OGC API type (Features, Tiles, EDR, etc.)"
    )
    spec_version: str = Field(
        ..., description="The specification version (e.g., '1.0', '1.1')"
    )
    part: int | None = Field(
        None, description="Part number for multi-part specifications (e.g., 1, 2, 3)"
    )

    def __hash__(self) -> int:
        return hash((self.api_type, self.spec_version, self.part))

    def __str__(self) -> str:
        if self.part:
            return f"{self.api_type.display_name} Part {self.part} v{self.spec_version}"
        return f"{self.api_type.display_name} v{self.spec_version}"

    def matches(self, other: "OGCSpecificationKey", strict: bool = False) -> bool:
        """Check if this key matches another key.

        Args:
            other: The other key to compare
            strict: If True, require exact match including part number

        Returns:
            True if keys match
        """
        if self.api_type != other.api_type:
            return False

        if strict:
            return self.spec_version == other.spec_version and self.part == other.part

        # Non-strict: just check major.minor version compatibility
        self_major_minor = ".".join(self.spec_version.split(".")[:2])
        other_major_minor = ".".join(other.spec_version.split(".")[:2])
        return self_major_minor == other_major_minor

    @classmethod
    def from_conformance_class(
        cls, cc: "ConformanceClass"
    ) -> "OGCSpecificationKey | None":
        """Create a specification key from a conformance class.

        Args:
            cc: The conformance class

        Returns:
            OGCSpecificationKey or None if cannot be determined
        """
        if cc.api_type is None or cc.spec_version is None:
            return None

        return cls(
            api_type=cc.api_type,
            spec_version=cc.spec_version,
            part=cc.part,
        )


class ConformanceClass(BaseModel):
    """Represents an OGC API conformance class.

    Conformance classes are URIs that identify specific capabilities
    that an API implementation supports.

    URI format: http://www.opengis.net/spec/ogcapi-{type}-{part}/{version}/conf/{class}
    Examples:
        - http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core
        - http://www.opengis.net/spec/ogcapi-edr-1/1.1/conf/queries
        - http://www.opengis.net/spec/ogcapi-common-2/1.0/conf/collections
    """

    model_config = {"frozen": True}

    uri: str = Field(..., description="The conformance class URI")

    # Regex pattern to parse OGC API conformance URIs
    # Matches: ogcapi-{type}-{part}/{version}/conf/{class}
    _URI_PATTERN = re.compile(
        r"ogcapi-(\w+)-(\d+)/(\d+\.\d+(?:\.\d+)?)/conf/(\w+[-\w]*)",
        re.IGNORECASE,
    )

    @property
    def api_type(self) -> OGCAPIType | None:
        """Determine the OGC API type from the conformance class URI."""
        uri_lower = self.uri.lower()

        # Check for specific API types in order of specificity
        if "ogcapi-features" in uri_lower or "/features-" in uri_lower:
            return OGCAPIType.FEATURES
        elif "ogcapi-tiles" in uri_lower or "/tiles-" in uri_lower:
            return OGCAPIType.TILES
        elif "ogcapi-maps" in uri_lower or "/maps-" in uri_lower:
            return OGCAPIType.MAPS
        elif "ogcapi-processes" in uri_lower or "/processes-" in uri_lower:
            return OGCAPIType.PROCESSES
        elif "ogcapi-records" in uri_lower or "/records-" in uri_lower:
            return OGCAPIType.RECORDS
        elif "ogcapi-coverages" in uri_lower or "/coverages-" in uri_lower:
            return OGCAPIType.COVERAGES
        elif "ogcapi-edr" in uri_lower or "/edr-" in uri_lower:
            return OGCAPIType.EDR
        elif "ogcapi-styles" in uri_lower or "/styles-" in uri_lower:
            return OGCAPIType.STYLES
        elif "ogcapi-routes" in uri_lower or "/routes-" in uri_lower:
            return OGCAPIType.ROUTES
        elif "ogcapi-common" in uri_lower or "/common-" in uri_lower:
            return OGCAPIType.COMMON

        return None

    @property
    def part(self) -> int | None:
        """Extract part number from conformance class URI.

        Returns:
            Part number (e.g., 1 for ogcapi-features-1) or None
        """
        match = self._URI_PATTERN.search(self.uri)
        if match:
            return int(match.group(2))

        # Fallback: try simpler pattern
        simple_match = re.search(r"ogcapi-\w+-(\d+)/", self.uri, re.IGNORECASE)
        if simple_match:
            return int(simple_match.group(1))

        return None

    @property
    def spec_version(self) -> str | None:
        """Extract specification version from conformance class URI.

        Returns:
            Version string (e.g., "1.0", "1.1") or None
        """
        match = self._URI_PATTERN.search(self.uri)
        if match:
            return match.group(3)

        # Fallback: try simpler pattern
        simple_match = re.search(r"/(\d+\.\d+(?:\.\d+)?)/", self.uri)
        if simple_match:
            return simple_match.group(1)

        return None

    @property
    def version(self) -> str | None:
        """Extract version from conformance class URI if present.

        Deprecated: Use spec_version instead for clarity.
        """
        return self.spec_version

    @property
    def conformance_class_name(self) -> str | None:
        """Extract the conformance class name (e.g., 'core', 'geojson').

        Returns:
            Conformance class name or None
        """
        match = self._URI_PATTERN.search(self.uri)
        if match:
            return match.group(4)

        # Fallback: try to get from /conf/{name}
        simple_match = re.search(r"/conf/([^/]+)/?$", self.uri, re.IGNORECASE)
        if simple_match:
            return simple_match.group(1)

        return None

    @property
    def is_core(self) -> bool:
        """Check if this is a core conformance class."""
        return "/conf/core" in self.uri.lower()

    @property
    def specification_key(self) -> "OGCSpecificationKey | None":
        """Get the OGC specification key for this conformance class.

        Returns:
            OGCSpecificationKey or None if cannot be determined
        """
        return OGCSpecificationKey.from_conformance_class(self)

    def __hash__(self) -> int:
        return hash(self.uri)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ConformanceClass):
            return self.uri == other.uri
        if isinstance(other, str):
            return self.uri == other
        return False

    def __repr__(self) -> str:
        return f"ConformanceClass(uri='{self.uri}')"


# Common conformance class URI patterns
CONFORMANCE_PATTERNS: dict[OGCAPIType, list[str]] = {
    OGCAPIType.COMMON: [
        "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core",
        "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/landing-page",
        "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/oas30",
        "http://www.opengis.net/spec/ogcapi-common-2/1.0/conf/collections",
    ],
    OGCAPIType.FEATURES: [
        "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
        "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/oas30",
        "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson",
        "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/html",
        "http://www.opengis.net/spec/ogcapi-features-2/1.0/conf/crs",
        "http://www.opengis.net/spec/ogcapi-features-3/1.0/conf/filter",
    ],
    OGCAPIType.TILES: [
        "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/core",
        "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/tileset",
        "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/tilesets-list",
        "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/geodata-tilesets",
        "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/dataset-tilesets",
    ],
    OGCAPIType.MAPS: [
        "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/core",
        "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/display-resolution",
        "http://www.opengis.net/spec/ogcapi-maps-1/1.0/conf/spatial-subsetting",
    ],
    OGCAPIType.PROCESSES: [
        "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/core",
        "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/ogc-process-description",
        "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/json",
        "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/job-list",
        "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/dismiss",
    ],
    OGCAPIType.RECORDS: [
        "http://www.opengis.net/spec/ogcapi-records-1/1.0/conf/core",
        "http://www.opengis.net/spec/ogcapi-records-1/1.0/conf/sorting",
        "http://www.opengis.net/spec/ogcapi-records-1/1.0/conf/cql-filter",
    ],
    OGCAPIType.COVERAGES: [
        "http://www.opengis.net/spec/ogcapi-coverages-1/1.0/conf/core",
        "http://www.opengis.net/spec/ogcapi-coverages-1/1.0/conf/geodata-coverage",
    ],
    OGCAPIType.EDR: [
        "http://www.opengis.net/spec/ogcapi-edr-1/1.0/conf/core",
        "http://www.opengis.net/spec/ogcapi-edr-1/1.0/conf/collections",
        "http://www.opengis.net/spec/ogcapi-edr-1/1.0/conf/queries",
    ],
    OGCAPIType.STYLES: [
        "http://www.opengis.net/spec/ogcapi-styles-1/1.0/conf/core",
        "http://www.opengis.net/spec/ogcapi-styles-1/1.0/conf/manage-styles",
    ],
    OGCAPIType.ROUTES: [
        "http://www.opengis.net/spec/ogcapi-routes-1/1.0/conf/core",
    ],
}


def parse_conformance_classes(
    conformance_data: list[str] | dict[str, Any],
) -> list[ConformanceClass]:
    """Parse conformance classes from various formats.

    Args:
        conformance_data: Either a list of URIs or a dict with 'conformsTo' key

    Returns:
        List of ConformanceClass objects
    """
    if isinstance(conformance_data, dict):
        # Handle {"conformsTo": [...]} format
        uris = conformance_data.get("conformsTo", [])
    else:
        uris = conformance_data

    return [ConformanceClass(uri=uri) for uri in uris if isinstance(uri, str)]


def detect_api_types(
    conformance_classes: list[ConformanceClass],
) -> set[OGCAPIType]:
    """Detect all OGC API types from a list of conformance classes.

    Args:
        conformance_classes: List of conformance classes

    Returns:
        Set of detected OGC API types
    """
    types: set[OGCAPIType] = set()

    for cc in conformance_classes:
        api_type = cc.api_type
        if api_type:
            types.add(api_type)

    return types


def get_primary_api_type(
    conformance_classes: list[ConformanceClass],
) -> OGCAPIType:
    """Determine the primary OGC API type from conformance classes.

    The primary type is determined by priority (most specific first).
    If no specific type is found, returns COMMON.

    Args:
        conformance_classes: List of conformance classes

    Returns:
        The primary OGC API type
    """
    types = detect_api_types(conformance_classes)

    # Priority order (most specific first)
    priority = [
        OGCAPIType.FEATURES,
        OGCAPIType.TILES,
        OGCAPIType.MAPS,
        OGCAPIType.PROCESSES,
        OGCAPIType.RECORDS,
        OGCAPIType.COVERAGES,
        OGCAPIType.EDR,
        OGCAPIType.STYLES,
        OGCAPIType.ROUTES,
        OGCAPIType.COMMON,
    ]

    for api_type in priority:
        if api_type in types:
            return api_type

    return OGCAPIType.COMMON


def get_specification_keys(
    conformance_classes: list[ConformanceClass],
) -> set[OGCSpecificationKey]:
    """Extract all unique OGC specification keys from conformance classes.

    Args:
        conformance_classes: List of conformance classes

    Returns:
        Set of OGCSpecificationKey objects
    """
    keys: set[OGCSpecificationKey] = set()

    for cc in conformance_classes:
        key = cc.specification_key
        if key:
            keys.add(key)

    return keys


def get_specification_versions(
    conformance_classes: list[ConformanceClass],
    api_type: OGCAPIType,
) -> set[str]:
    """Get all versions of a specific OGC API type from conformance classes.

    Args:
        conformance_classes: List of conformance classes
        api_type: The OGC API type to filter by

    Returns:
        Set of version strings (e.g., {"1.0", "1.1"})
    """
    versions: set[str] = set()

    for cc in conformance_classes:
        if cc.api_type == api_type and cc.spec_version:
            versions.add(cc.spec_version)

    return versions


def group_conformance_by_spec(
    conformance_classes: list[ConformanceClass],
) -> dict[OGCSpecificationKey, list[ConformanceClass]]:
    """Group conformance classes by their specification key.

    Args:
        conformance_classes: List of conformance classes

    Returns:
        Dictionary mapping specification keys to their conformance classes
    """
    groups: dict[OGCSpecificationKey, list[ConformanceClass]] = {}

    for cc in conformance_classes:
        key = cc.specification_key
        if key:
            if key not in groups:
                groups[key] = []
            groups[key].append(cc)

    return groups
