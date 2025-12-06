"""OGC API types and conformance class definitions."""

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


class ConformanceClass(BaseModel):
    """Represents an OGC API conformance class.

    Conformance classes are URIs that identify specific capabilities
    that an API implementation supports.
    """

    model_config = {"frozen": True}

    uri: str = Field(..., description="The conformance class URI")

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
    def is_core(self) -> bool:
        """Check if this is a core conformance class."""
        return "/conf/core" in self.uri.lower()

    @property
    def version(self) -> str | None:
        """Extract version from conformance class URI if present."""
        import re

        # Pattern like /1.0/ or /1.0.0/
        match = re.search(r"/(\d+\.\d+(?:\.\d+)?)/", self.uri)
        return match.group(1) if match else None

    def __hash__(self) -> int:
        return hash(self.uri)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ConformanceClass):
            return self.uri == other.uri
        if isinstance(other, str):
            return self.uri == other
        return False


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
