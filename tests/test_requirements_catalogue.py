"""The catalogue of the requirements each conformance class carries."""

from __future__ import annotations

from collections import Counter

from ogcapi_registry import KNOWN_REQUIREMENTS, list_requirements
from ogcapi_registry.known_classes import KNOWN_CONFORMANCE_CLASSES

MAPS = "http://www.opengis.net/spec/ogcapi-maps-1/1.0"

#: Distinct identifiers under a numbered requirement header in each document,
#: counted on 2026-11-09 with a pattern that accepts any identifier. A header
#: the parser misses shows up as a difference here.
HEADERS = {
    "17-069r4": 51,
    "18-058r1": 16,
    "19-079r2": 18,
    "20-057": 33,
    "18-062r2": 82,
    "19-086r6": 90,
    "20-058": 63,
    "21-065r2": 41,
    "19-072": 27,
    "23-058r2": 37,
}

#: Requirements stated in a requirements class that has no conformance class:
#: Requirements class A.4 of EDR 1.1.
LEFT_OUT = {"19-086r6": 37}


def test_every_requirement_belongs_to_a_known_class():
    orphans = [
        uri
        for uri, requirement in KNOWN_REQUIREMENTS.items()
        if requirement.conformance_class not in KNOWN_CONFORMANCE_CLASSES
    ]

    assert KNOWN_REQUIREMENTS
    assert orphans == []


def test_every_document_yields_its_requirements():
    counts = Counter(
        requirement.document for requirement in KNOWN_REQUIREMENTS.values()
    )

    expected = {
        document: headers - LEFT_OUT.get(document, 0)
        for document, headers in HEADERS.items()
    }

    assert {document: counts[document] for document in HEADERS} == expected


def test_maps_requirements_meet_their_class_under_http():
    uris = {r.uri for r in list_requirements(f"{MAPS}/conf/collection-map")}

    assert uris == {
        f"{MAPS}/req/collection-map/desc-links",
        f"{MAPS}/req/collection-map/desc-crs",
        f"{MAPS}/req/collection-map/map-operation",
    }


def test_cql2_and_common_are_catalogued():
    basic_cql2 = "http://www.opengis.net/spec/cql2/1.0/conf/basic-cql2"
    landing_page = "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/landing-page"

    assert basic_cql2 in KNOWN_CONFORMANCE_CLASSES
    assert landing_page in KNOWN_CONFORMANCE_CLASSES
    assert list_requirements(basic_cql2)
    assert list_requirements(landing_page)


def test_edr_requirements_carry_the_version_of_their_document():
    edr = [r.uri for r in KNOWN_REQUIREMENTS.values() if r.document == "19-086r6"]

    assert edr
    assert all("/ogcapi-edr-1/1.1/req/" in uri for uri in edr)


def test_an_unknown_class_has_no_requirements():
    assert list_requirements(f"{MAPS}/conf/no-such-class") == ()


def test_common_part_3_is_catalogued():
    schemas = "http://www.opengis.net/spec/ogcapi-common-3/1.0/conf/schemas"
    roles = (
        "http://www.opengis.net/spec/ogcapi-common-3/1.0/conf/advanced-property-roles"
    )

    assert KNOWN_CONFORMANCE_CLASSES[schemas].document == "23-058r2"
    assert len(list_requirements(schemas)) == 9
    assert len(list_requirements(roles)) == 7
