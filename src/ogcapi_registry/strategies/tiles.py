"""Validation strategy for OGC API - Tiles."""

from typing import Any, ClassVar

from ..models import ValidationResult
from ..expectations import Expectation, Verb
from ..ogc_types import ConformanceClass, OGCAPIType
from .base import ValidationStrategy


class TilesStrategy(ValidationStrategy):
    """Validation strategy for OGC API - Tiles.

    Validates OpenAPI documents for compliance with the OGC API - Tiles
    specification.
    """

    api_type: ClassVar[OGCAPIType] = OGCAPIType.TILES
    required_conformance_patterns: ClassVar[list[str]] = [
        "ogcapi-tiles",
        "/tiles-",
    ]
    optional_conformance_patterns: ClassVar[list[str]] = [
        "/conf/tileset",
        "/conf/tilesets-list",
        "/conf/geodata-tilesets",
        "/conf/dataset-tilesets",
        "/conf/collections-selection",
    ]

    def validate(
        self,
        document: dict[str, Any],
        conformance_classes: list[ConformanceClass],
    ) -> ValidationResult:
        """Validate an OpenAPI document for OGC API - Tiles compliance.

        Args:
            document: The OpenAPI document to validate
            conformance_classes: Conformance classes declared by the implementation

        Returns:
            ValidationResult with validation outcome
        """
        errors: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []

        # Validate required paths
        required_paths = self.get_required_paths(conformance_classes)
        errors.extend(self.validate_paths_exist(document, required_paths))

        # Validate required operations
        required_ops = self.get_required_operations(conformance_classes)
        errors.extend(self.validate_operations_exist(document, required_ops))

        # Validate tileset endpoint
        tileset_errors = self._validate_tileset_endpoint(document, conformance_classes)
        errors.extend(tileset_errors)

        # Validate tile endpoint
        tile_errors = self._validate_tile_endpoint(document)
        errors.extend(tile_errors)

        if errors:
            return ValidationResult.failure(errors, warnings=tuple(warnings))

        return ValidationResult.success(warnings=tuple(warnings))

    def get_expectations(
        self,
        conformance_classes: list[ConformanceClass],
    ) -> list[Expectation]:
        """What the standard expects, in the standard's own words.

        Each entry carries the verb the clause used and the clause
        itself, so severity is derived rather than chosen, and a reader
        can check the claim against the text.
        """
        expectations = [
            Expectation(
                target="/",
                verb=Verb.SHALL,
                source="OGC API - Common Part 1, landing page",
            ),
            Expectation(
                target="/conformance",
                verb=Verb.SHALL,
                source="OGC API - Common Part 1, conformance declaration",
            ),
        ]

        if self._has_conformance_class(conformance_classes, "/conf/dataset-tilesets"):
            expectations += [
                Expectation(
                    target="/tiles",
                    verb=Verb.SHALL,
                    source="OGC API - Tiles Part 1, /req/tilesets-list/tileset-path: "
                    "the API SHALL support a GET operation on a .../tiles path",
                ),
                Expectation(
                    target="/tiles/{tileMatrixSetId}",
                    verb=Verb.SHALL,
                    source="OGC API - Tiles Part 1, /req/tileset/description",
                ),
                Expectation(
                    target="/tiles/{tileMatrixSetId}/{tileMatrix}/{tileRow}/{tileCol}",
                    verb=Verb.SHALL,
                    source="OGC API - Tiles Part 1, /req/core/tc-tilematrix-definition "
                    "and the tileRow/tileCol definitions beside it",
                ),
            ]

        if self._has_conformance_class(conformance_classes, "/conf/geodata-tilesets"):
            expectations += [
                Expectation(
                    target="/collections/{collectionId}/tiles",
                    verb=Verb.SHALL,
                    source="OGC API - Tiles Part 1, /req/geodata-tilesets/operation A: "
                    "the resource SHALL have a list of at least one tileset at .../tiles",
                ),
                Expectation(
                    target="/collections/{collectionId}/tiles/{tileMatrixSetId}",
                    verb=Verb.SHALL,
                    source="OGC API - Tiles Part 1, /req/tileset/description",
                ),
                Expectation(
                    target=(
                        "/collections/{collectionId}/tiles/{tileMatrixSetId}"
                        "/{tileMatrix}/{tileRow}/{tileCol}"
                    ),
                    verb=Verb.SHALL,
                    source="OGC API - Tiles Part 1, /req/core/tc-tilematrix-definition "
                    "and the tileRow/tileCol definitions beside it",
                ),
            ]

        # Recorded rather than demanded, and deliberately not tied to any
        # conformance class: the tiling schemes clauses are a SHOULD, and
        # they apply only where the API uses a tile matrix set that is not
        # in a register. Deleting the line would lose the knowledge; this
        # way it is here, cited, and it never fires.
        expectations.append(
            Expectation(
                target="/tileMatrixSets",
                verb=Verb.SHOULD,
                source="OGC API - Tiles Part 1, tiling schemes clauses B-D",
                condition="the API uses a tile matrix set not available in a register",
            )
        )

        return expectations

    def get_required_paths(
        self,
        conformance_classes: list[ConformanceClass],
    ) -> list[str]:
        """The paths the standard demands outright.

        Derived from `get_expectations`: only what a clause states with
        `shall`, and only where no condition stands in the way.
        """
        return [
            expectation.target
            for expectation in self.get_expectations(conformance_classes)
            if expectation.verb is Verb.SHALL and expectation.is_evaluable
        ]

    def get_required_operations(
        self,
        conformance_classes: list[ConformanceClass],
    ) -> dict[str, list[str]]:
        """The operations those paths owe, which for tiles is a GET each."""
        return {path: ["get"] for path in self.get_required_paths(conformance_classes)}

    def _validate_tileset_endpoint(
        self,
        document: dict[str, Any],
        conformance_classes: list[ConformanceClass],
    ) -> list[dict[str, Any]]:
        """Validate tileset endpoints.

        Args:
            document: The OpenAPI document
            conformance_classes: Conformance classes

        Returns:
            List of validation errors
        """
        errors: list[dict[str, Any]] = []
        paths = document.get("paths", {})

        # Check for tileset metadata endpoint
        tileset_paths = [p for p in paths if "/tiles" in p and "tileMatrix" not in p]

        for tileset_path in tileset_paths:
            if "{tileMatrixSetId}" in tileset_path:
                get_op = paths[tileset_path].get("get", {})
                if not get_op:
                    continue

                responses = get_op.get("responses", {})
                if "200" not in responses and "2XX" not in responses:
                    errors.append(
                        {
                            "path": f"paths/{tileset_path}.get.responses",
                            "message": "Tileset endpoint should have a 200 response",
                            "type": "missing_response",
                        }
                    )

        return errors

    def _validate_tile_endpoint(self, document: dict[str, Any]) -> list[dict[str, Any]]:
        """Validate tile retrieval endpoints.

        Args:
            document: The OpenAPI document

        Returns:
            List of validation errors
        """
        errors: list[dict[str, Any]] = []
        paths = document.get("paths", {})

        # Find tile endpoints (contain tileMatrix, tileRow, tileCol)
        tile_paths = [
            p for p in paths if "tileMatrix" in p and "tileRow" in p and "tileCol" in p
        ]

        for tile_path in tile_paths:
            get_op = paths[tile_path].get("get", {})
            if not get_op:
                continue

            responses = get_op.get("responses", {})

            # Should have 200 response
            if "200" not in responses and "2XX" not in responses:
                errors.append(
                    {
                        "path": f"paths/{tile_path}.get.responses",
                        "message": "Tile endpoint should have a 200 response",
                        "type": "missing_response",
                    }
                )

            # Should have 404 response for not found tiles
            if "404" not in responses and "4XX" not in responses:
                errors.append(
                    {
                        "path": f"paths/{tile_path}.get.responses",
                        "message": "Tile endpoint should have a 404 response for missing tiles",
                        "type": "missing_response",
                    }
                )

        return errors

    @staticmethod
    def _has_conformance_class(
        conformance_classes: list[ConformanceClass],
        pattern: str,
    ) -> bool:
        """Check if a conformance class matching the pattern exists."""
        pattern_lower = pattern.lower()
        return any(pattern_lower in cc.uri.lower() for cc in conformance_classes)
