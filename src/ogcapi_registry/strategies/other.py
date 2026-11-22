"""Validation strategies for other OGC API types."""

import re
from typing import Any, ClassVar

from ..expectations import Expectation, Verb
from ..models import ErrorSeverity, ValidationResult
from ..ogc_types import ConformanceClass, OGCAPIType
from .base import ValidationStrategy


#: The last segment of each EDR query path.
EDR_QUERY_TYPES = (
    "position",
    "radius",
    "area",
    "cube",
    "trajectory",
    "corridor",
    "locations",
    "items",
)

_EDR_QUERY_PATH = re.compile(
    r"^/collections/[^/]+(?:/instances/[^/]+)?/(" + "|".join(EDR_QUERY_TYPES) + r")$"
)
_EDR_QUERIES_CLASS = re.compile(r"/ogcapi-edr-1/(\d+\.\d+)/conf/queries$")

#: The query parameters a GET operation of each query type has to include, by
#: version: the parameter, the verb and the clause that states it. EDR 1.0.1
#: writes MUST where 1.1 writes SHALL.
_EDR_QUERY_PARAMETERS: dict[str, dict[str, list[tuple[str, Verb, str]]]] = {
    "1.0": {
        "position": [
            ("coords", Verb.SHALL, "/req/queries/position C"),
            ("parameter-name", Verb.SHOULD, "/req/queries/position F"),
            ("crs", Verb.SHOULD, "/req/queries/position H"),
            ("f", Verb.SHOULD, "/req/queries/position I"),
        ],
        "area": [
            ("coords", Verb.SHALL, "/req/edr/rc-area C"),
            ("parameter-name", Verb.SHOULD, "/req/edr/rc-area F"),
            ("crs", Verb.SHOULD, "/req/edr/rc-area H"),
            ("f", Verb.SHOULD, "/req/edr/rc-area I"),
        ],
        "cube": [
            ("bbox", Verb.SHALL, "/req/edr/rc-cube C"),
            ("z", Verb.SHALL, "/req/edr/rc-cube F"),
            ("parameter-name", Verb.SHOULD, "/req/edr/rc-cube H"),
            ("crs", Verb.SHOULD, "/req/edr/rc-cube J"),
            ("f", Verb.SHOULD, "/req/edr/rc-cube K"),
        ],
    },
    "1.1": {
        "position": [
            ("coords", Verb.SHALL, "/req/queries/position D"),
            ("parameter-name", Verb.SHOULD, "/req/queries/position G"),
            ("crs", Verb.SHOULD, "/req/queries/position I"),
            ("f", Verb.SHOULD, "/req/queries/position J"),
        ],
        "area": [
            ("coords", Verb.SHALL, "/req/edr/rc-area D"),
            ("parameter-name", Verb.SHOULD, "/req/edr/rc-area G"),
            ("crs", Verb.SHOULD, "/req/edr/rc-area I"),
            ("f", Verb.SHOULD, "/req/edr/rc-area J"),
        ],
        "cube": [
            ("bbox", Verb.SHALL, "/req/edr/rc-cube D"),
            ("z", Verb.SHALL, "/req/edr/rc-cube G"),
            ("parameter-name", Verb.SHOULD, "/req/edr/rc-cube I"),
            ("crs", Verb.SHOULD, "/req/edr/rc-cube K"),
            ("f", Verb.SHOULD, "/req/edr/rc-cube L"),
        ],
    },
}


class EDRStrategy(ValidationStrategy):
    """Validation strategy for OGC API - Environmental Data Retrieval.

    EDR has no conformance class per query type: a server offers a query by
    publishing its path, and conformance class ``queries`` holds the
    requirements of every type (19-086r5 and 19-086r6, Annex A). So the query
    paths are read from the document, and their parameters are checked
    against each EDR version whose ``queries`` class is declared.
    """

    api_type: ClassVar[OGCAPIType] = OGCAPIType.EDR
    required_conformance_patterns: ClassVar[list[str]] = [
        "ogcapi-edr",
        "/edr-",
    ]
    optional_conformance_patterns: ClassVar[list[str]] = [
        "/conf/collections",
        "/conf/queries",
    ]

    def validate(
        self,
        document: dict[str, Any],
        conformance_classes: list[ConformanceClass],
    ) -> ValidationResult:
        errors: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []

        errors.extend(
            self.validate_paths_exist(
                document, self.get_required_paths(conformance_classes)
            )
        )
        errors.extend(
            self.validate_operations_exist(
                document, self.get_required_operations(conformance_classes)
            )
        )

        for found in self._check_query_parameters(document, conformance_classes):
            if found["severity"] == ErrorSeverity.CRITICAL.value:
                errors.append(found)
            else:
                warnings.append(found)

        if errors:
            return ValidationResult.failure(errors, warnings=tuple(warnings))
        return ValidationResult.success(warnings=tuple(warnings))

    def get_required_paths(
        self, conformance_classes: list[ConformanceClass]
    ) -> list[str]:
        return ["/", "/conformance", "/collections"]

    def get_required_operations(
        self, conformance_classes: list[ConformanceClass]
    ) -> dict[str, list[str]]:
        return {"/": ["get"], "/conformance": ["get"], "/collections": ["get"]}

    @staticmethod
    def list_query_paths(document: dict[str, Any]) -> dict[str, list[str]]:
        """List the query paths a document publishes, by query type.

        A query path ends with the name of its type, under
        ``/collections/{collectionId}`` or under one of its instances. The
        collection id may be written literally, as pygeoapi does.

        Parameters
        ----------
        document
            The OpenAPI document.

        Returns
        -------
        dict of str to list of str
            The paths of each query type that has any, in document order.
        """
        found: dict[str, list[str]] = {}
        for path in document.get("paths", {}):
            match = _EDR_QUERY_PATH.match(path)
            if match:
                found.setdefault(match.group(1), []).append(path)
        return found

    def _list_get_parameters(
        self, path_item: dict[str, Any], document: dict[str, Any]
    ) -> set[str]:
        """List the parameter names of a GET operation, inherited ones included.

        The EDR schemas name the coordinates file of each query type after
        it, such as ``positionCoords.yaml``; the parameter it defines is
        ``coords``.
        """
        operation = path_item.get("get", {})
        names = self._parameter_names(
            [*path_item.get("parameters", []), *operation.get("parameters", [])],
            document,
        )
        return {
            "coords" if name.removesuffix("Coords") in EDR_QUERY_TYPES else name
            for name in names
        }

    def get_query_expectations(
        self, document: dict[str, Any], version: str
    ) -> list[Expectation]:
        """List the query parameters an EDR version expects of the query paths.

        Only position, area and cube are listed; the clauses of the other
        query types are not read yet. A path offered by POST alone, as EDR
        1.1 allows, has no GET operation to check.

        Parameters
        ----------
        document
            The OpenAPI document.
        version
            The EDR version, ``1.0`` or ``1.1``.

        Returns
        -------
        list of Expectation
            One per parameter of each query path, with the verb and the clause.
        """
        rules = _EDR_QUERY_PARAMETERS.get(version, {})
        return [
            Expectation(
                target=f"GET {path} ?{parameter}",
                verb=verb,
                source=f"OGC API - EDR {version}, {clause}",
            )
            for query_type, paths in self.list_query_paths(document).items()
            for path in paths
            if "get" in document["paths"][path]
            for parameter, verb, clause in rules.get(query_type, [])
        ]

    def _check_query_parameters(
        self,
        document: dict[str, Any],
        conformance_classes: list[ConformanceClass],
    ) -> list[dict[str, Any]]:
        """Report each expected query parameter a query path lacks."""
        found: list[dict[str, Any]] = []
        query_paths = self.list_query_paths(document)
        paths = document.get("paths", {})
        for cc in conformance_classes:
            declared = _EDR_QUERIES_CLASS.search(cc.uri)
            if declared is None:
                continue
            version = declared.group(1)
            if not query_paths:
                found.append(
                    self.create_error(
                        path="paths",
                        message=(
                            f"OGC API - EDR {version}, /req/edr/rc-data-queries A: "
                            "a collection SHALL offer at least one query type, "
                            "and the document publishes no query path"
                        ),
                        error_type="missing_query_path",
                        conformance_class=cc.uri,
                    )
                )
                continue
            for expectation in self.get_query_expectations(document, version):
                path, parameter = expectation.target[len("GET ") :].split(" ?")
                if parameter in self._list_get_parameters(paths[path], document):
                    continue
                found.append(
                    self.create_error(
                        path=f"paths/{path}.get.parameters",
                        message=(
                            f"{expectation.source}: GET {path} "
                            f"{expectation.verb.value.upper()} include the "
                            f"'{parameter}' query parameter"
                        ),
                        error_type="missing_query_parameter",
                        severity=expectation.severity,
                        conformance_class=cc.uri,
                    )
                )
        return found


class CoveragesStrategy(ValidationStrategy):
    """Validation strategy for OGC API - Coverages."""

    api_type: ClassVar[OGCAPIType] = OGCAPIType.COVERAGES
    required_conformance_patterns: ClassVar[list[str]] = [
        "ogcapi-coverages",
        "/coverages-",
    ]
    optional_conformance_patterns: ClassVar[list[str]] = [
        "/conf/geodata-coverage",
        "/conf/coverage-subset",
        "/conf/coverage-rangesubset",
        "/conf/coverage-scaling",
    ]

    def validate(
        self,
        document: dict[str, Any],
        conformance_classes: list[ConformanceClass],
    ) -> ValidationResult:
        errors: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []

        required_paths = self.get_required_paths(conformance_classes)
        errors.extend(self.validate_paths_exist(document, required_paths))

        required_ops = self.get_required_operations(conformance_classes)
        errors.extend(self.validate_operations_exist(document, required_ops))

        if errors:
            return ValidationResult.failure(errors, warnings=tuple(warnings))
        return ValidationResult.success(warnings=tuple(warnings))

    def get_required_paths(
        self, conformance_classes: list[ConformanceClass]
    ) -> list[str]:
        paths = [
            "/",
            "/conformance",
            "/collections",
            "/collections/{collectionId}",
            "/collections/{collectionId}/coverage",
        ]
        return paths

    def get_required_operations(
        self, conformance_classes: list[ConformanceClass]
    ) -> dict[str, list[str]]:
        return {
            "/": ["get"],
            "/conformance": ["get"],
            "/collections": ["get"],
            "/collections/{collectionId}": ["get"],
            "/collections/{collectionId}/coverage": ["get"],
        }


class MapsStrategy(ValidationStrategy):
    """Validation strategy for OGC API - Maps."""

    api_type: ClassVar[OGCAPIType] = OGCAPIType.MAPS
    required_conformance_patterns: ClassVar[list[str]] = [
        "ogcapi-maps",
        "/maps-",
    ]
    optional_conformance_patterns: ClassVar[list[str]] = [
        "/conf/display-resolution",
        "/conf/spatial-subsetting",
        "/conf/scaling",
        "/conf/background",
    ]

    def validate(
        self,
        document: dict[str, Any],
        conformance_classes: list[ConformanceClass],
    ) -> ValidationResult:
        errors: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []

        required_paths = self.get_required_paths(conformance_classes)
        errors.extend(self.validate_paths_exist(document, required_paths))

        required_ops = self.get_required_operations(conformance_classes)
        errors.extend(self.validate_operations_exist(document, required_ops))

        if errors:
            return ValidationResult.failure(errors, warnings=tuple(warnings))
        return ValidationResult.success(warnings=tuple(warnings))

    def get_required_paths(
        self, conformance_classes: list[ConformanceClass]
    ) -> list[str]:
        paths = [
            "/",
            "/conformance",
            "/collections",
            "/collections/{collectionId}",
            "/collections/{collectionId}/map",
        ]
        return paths

    def get_required_operations(
        self, conformance_classes: list[ConformanceClass]
    ) -> dict[str, list[str]]:
        return {
            "/": ["get"],
            "/conformance": ["get"],
            "/collections": ["get"],
            "/collections/{collectionId}": ["get"],
            "/collections/{collectionId}/map": ["get"],
        }


class StylesStrategy(ValidationStrategy):
    """Validation strategy for OGC API - Styles."""

    api_type: ClassVar[OGCAPIType] = OGCAPIType.STYLES
    required_conformance_patterns: ClassVar[list[str]] = [
        "ogcapi-styles",
        "/styles-",
    ]
    optional_conformance_patterns: ClassVar[list[str]] = [
        "/conf/manage-styles",
        "/conf/style-validation",
    ]

    def validate(
        self,
        document: dict[str, Any],
        conformance_classes: list[ConformanceClass],
    ) -> ValidationResult:
        errors: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []

        required_paths = self.get_required_paths(conformance_classes)
        errors.extend(self.validate_paths_exist(document, required_paths))

        required_ops = self.get_required_operations(conformance_classes)
        errors.extend(self.validate_operations_exist(document, required_ops))

        if errors:
            return ValidationResult.failure(errors, warnings=tuple(warnings))
        return ValidationResult.success(warnings=tuple(warnings))

    def get_required_paths(
        self, conformance_classes: list[ConformanceClass]
    ) -> list[str]:
        paths = ["/", "/conformance", "/styles", "/styles/{styleId}"]

        if self._has_conformance_class(conformance_classes, "/conf/manage-styles"):
            # Management requires POST/PUT/DELETE
            pass

        return paths

    def get_required_operations(
        self, conformance_classes: list[ConformanceClass]
    ) -> dict[str, list[str]]:
        operations: dict[str, list[str]] = {
            "/": ["get"],
            "/conformance": ["get"],
            "/styles": ["get"],
            "/styles/{styleId}": ["get"],
        }

        if self._has_conformance_class(conformance_classes, "/conf/manage-styles"):
            operations["/styles"] = ["get", "post"]
            operations["/styles/{styleId}"] = ["get", "put", "delete"]

        return operations

    @staticmethod
    def _has_conformance_class(
        conformance_classes: list[ConformanceClass], pattern: str
    ) -> bool:
        pattern_lower = pattern.lower()
        return any(pattern_lower in cc.uri.lower() for cc in conformance_classes)


class RoutesStrategy(ValidationStrategy):
    """Validation strategy for OGC API - Routes."""

    api_type: ClassVar[OGCAPIType] = OGCAPIType.ROUTES
    required_conformance_patterns: ClassVar[list[str]] = [
        "ogcapi-routes",
        "/routes-",
    ]
    optional_conformance_patterns: ClassVar[list[str]] = []

    def validate(
        self,
        document: dict[str, Any],
        conformance_classes: list[ConformanceClass],
    ) -> ValidationResult:
        errors: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []

        required_paths = self.get_required_paths(conformance_classes)
        errors.extend(self.validate_paths_exist(document, required_paths))

        required_ops = self.get_required_operations(conformance_classes)
        errors.extend(self.validate_operations_exist(document, required_ops))

        if errors:
            return ValidationResult.failure(errors, warnings=tuple(warnings))
        return ValidationResult.success(warnings=tuple(warnings))

    def get_required_paths(
        self, conformance_classes: list[ConformanceClass]
    ) -> list[str]:
        return ["/", "/conformance", "/routes"]

    def get_required_operations(
        self, conformance_classes: list[ConformanceClass]
    ) -> dict[str, list[str]]:
        return {
            "/": ["get"],
            "/conformance": ["get"],
            "/routes": ["post"],
        }
