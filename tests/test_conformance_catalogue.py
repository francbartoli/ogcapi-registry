"""The catalogue of published conformance classes, and what it answers."""

from __future__ import annotations

from ogcapi_registry.conformance import validate_conformance
from ogcapi_registry.known_classes import (
    KNOWN_CONFORMANCE_CLASSES,
    SOURCE_DOCUMENTS,
)

TILES_CORE = "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/core"
TILES_MVT = "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/mvt"
FEATURES_CORE = "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core"


class TestCatalogue:
    """What was harvested from the standards."""

    def test_every_entry_cites_the_document_it_came_from(self):
        """An entry nobody can check is an assumption wearing a URI."""
        assert KNOWN_CONFORMANCE_CLASSES
        for known in KNOWN_CONFORMANCE_CLASSES.values():
            assert known.document in SOURCE_DOCUMENTS

    def test_the_key_is_the_uri_the_entry_describes(self):
        for uri, known in KNOWN_CONFORMANCE_CLASSES.items():
            assert known.uri == uri
            assert uri.endswith(f"/conf/{known.name}")

    def test_a_requirement_identifier_is_not_a_conformance_class(self):
        """`…/conf/collections/rc-md-success` names a requirement.

        It appears in the same documents and matches a careless pattern;
        a class name carries no slash.
        """
        assert not [
            uri for uri in KNOWN_CONFORMANCE_CLASSES if uri.count("/conf/") != 1
        ]
        assert not [
            uri for uri in KNOWN_CONFORMANCE_CLASSES if "/" in uri.split("/conf/")[1]
        ]

    def test_maps_is_in_there(self):
        """Maps writes its URIs with `https`, and was missed at first."""
        specs = {known.spec for known in KNOWN_CONFORMANCE_CLASSES.values()}
        assert "ogcapi-maps-1" in specs

    def test_classes_are_attributed_to_the_standard_that_defines_them(self):
        """Tiles cites Common; those classes belong to Common."""
        for uri, known in KNOWN_CONFORMANCE_CLASSES.items():
            assert f"/spec/{known.spec}/" in uri


class TestValidateConformance:
    """The comparison, which judges nothing about what ought to be there."""

    def test_a_published_class_is_recognised(self):
        report = validate_conformance([TILES_CORE])

        assert [known.uri for known in report.recognised] == [TILES_CORE]
        assert report.unrecognised == ()

    def test_something_no_standard_defines_is_reported_as_such(self):
        report = validate_conformance(
            ["http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/tilematrixsets"]
        )

        assert report.recognised == ()
        assert len(report.unrecognised) == 1

    def test_siblings_are_listed_only_for_standards_already_claimed(self):
        report = validate_conformance([TILES_CORE])
        specs = {known.spec for known in report.undeclared_siblings}

        assert specs == {"ogcapi-tiles-1"}
        assert TILES_MVT in [known.uri for known in report.undeclared_siblings]

    def test_a_declared_class_is_not_reported_as_a_missing_sibling(self):
        report = validate_conformance([TILES_CORE, TILES_MVT])

        assert TILES_MVT not in [known.uri for known in report.undeclared_siblings]

    def test_the_specifications_a_declaration_draws_on(self):
        report = validate_conformance([TILES_CORE, FEATURES_CORE])

        assert set(report.specifications) == {"ogcapi-tiles-1", "ogcapi-features-1"}

    def test_an_empty_declaration_says_nothing_about_anything(self):
        report = validate_conformance([])

        assert report.recognised == ()
        assert report.unrecognised == ()
        assert report.undeclared_siblings == ()
