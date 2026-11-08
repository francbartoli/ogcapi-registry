"""The catalogue of the requirements each conformance class carries."""

from __future__ import annotations

from collections import Counter

from ogcapi_registry import KNOWN_REQUIREMENTS, list_requirements
from ogcapi_registry.known_classes import KNOWN_CONFORMANCE_CLASSES

MAPS = "http://www.opengis.net/spec/ogcapi-maps-1/1.0"

#: Requirements under a numbered header in each document, counted on 2026-11-08.
FLOORS = {
    "17-069r4": 50,
    "18-058r1": 15,
    "19-079r2": 18,
    "20-057": 33,
    "18-062r2": 78,
    # 79 under a header; the 26 of Requirements class A.4 have no conformance class.
    "19-086r6": 53,
    "20-058": 63,
    "21-065r2": 41,
    "19-072": 27,
}


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

    assert {document: counts[document] for document in FLOORS} == FLOORS


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
