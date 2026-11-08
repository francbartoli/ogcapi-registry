"""Requirements read from the text of a published standard."""

from __future__ import annotations

from ogcapi_registry.requirements_text import KnownRequirement, parse_requirements

FEATURES = (
    "7.2.2. Response Requirement 2 /req/core/root-success A A successful execution of "
    "the operation SHALL be reported as a response with a HTTP status code 200 . "
    "B The content of that response SHALL be based upon the OpenAPI 3.0 schema "
    "landingPage.yaml . Recommendation 1 /rec/core/root-links A The landing page "
    "SHOULD include links . 7.3. API definition"
)
TILES = (
    "Requirement 1 Identifier /req/core/tc-op A The tiles making up a tileset SHALL "
    "be available via an HTTP GET request . Abstract test A.2 Identifier "
    "/conf/core/tc-op Requirement Requirement 1: /req/core/tc-op Test purpose Validate "
    "that tiles are available ."
)
MAPS = (
    "Normative statements Requirement 46: /req/collection-map/desc-links "
    "Requirement 47: /req/collection-map/desc-crs The Collection Map requirements "
    "class specifies how to get maps . Requirement 47 Identifier "
    "/req/collection-map/desc-crs Included in Requirements class 13: "
    "https://www.opengis.net/spec/ogcapi-maps-1/1.0/req/collection-map A The crs "
    "property SHALL contain URI or safe CURIEs . B A storageCrs property SHALL be the "
    "URI of that CRS . Requirement 48 Identifier /req/collection-map/map-operation "
    "A Every collection SHALL support an HTTP GET operation ."
)
EDR = (
    "Requirement A.1 Identifier /req/core/root-op Included in Requirements class A.1: "
    "http://www.opengis.net/spec/ogcapi-edr-1/1.1/req/core Statement A: The server "
    "SHALL support the HTTP GET operation at the path / . Permission 1 /per/core/crs "
    "A The server MAY support other CRSs ."
)
PROCESSES = (
    "Requirement 59 /req/oas30/oas-definition-2 The JSON representation SHALL conform "
    "to the OpenAPI Specification, version 3.0 . Requirement 60 /req/oas30/oas-impl "
    "The server SHALL implement all capabilities ."
)
QUOTING = (
    "C The responses to all HTTP GET requests issued in A and B SHALL satisfy "
    "requirement /req/landing-page/conformance-success . Requirements: "
    "/req/features-filter/queryables-link Test purpose: Check that a link exists ."
)


def _uris(requirements: list[KnownRequirement]) -> list[str]:
    return [requirement.uri for requirement in requirements]


def test_a_requirement_is_read_in_each_layout():
    assert _uris(
        parse_requirements(FEATURES, "ogcapi-features-1", "1.0", "17-069r4")
    ) == ["http://www.opengis.net/spec/ogcapi-features-1/1.0/req/core/root-success"]
    assert _uris(parse_requirements(TILES, "ogcapi-tiles-1", "1.0", "20-057")) == [
        "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/req/core/tc-op"
    ]
    assert _uris(parse_requirements(EDR, "ogcapi-edr-1", "1.1", "19-086r6")) == [
        "http://www.opengis.net/spec/ogcapi-edr-1/1.1/req/core/root-op"
    ]


def test_the_parts_follow_the_header():
    (root,) = parse_requirements(FEATURES, "ogcapi-features-1", "1.0", "17-069r4")

    assert len(root.parts) == 2
    assert root.parts[0].startswith("A successful execution")
    assert root.parts[1].startswith("The content of that response")
    assert "landingPage.yaml" in root.parts[1]
    assert "SHOULD" not in " ".join(root.parts)


def test_a_statement_without_letters_is_one_part():
    first, second = parse_requirements(
        PROCESSES, "ogcapi-processes-1", "1.0", "18-062r2"
    )

    assert first.parts == (
        "The JSON representation SHALL conform to the OpenAPI Specification, version 3.0 .",
    )
    assert second.uri.endswith("/req/oas30/oas-impl")


def test_the_definition_wins_over_lists_and_abstract_tests():
    requirements = parse_requirements(MAPS, "ogcapi-maps-1", "1.0", "20-058")
    desc_crs = next(r for r in requirements if r.uri.endswith("/desc-crs"))

    assert _uris(requirements) == [
        "http://www.opengis.net/spec/ogcapi-maps-1/1.0/req/collection-map/desc-crs",
        "http://www.opengis.net/spec/ogcapi-maps-1/1.0/req/collection-map/map-operation",
    ]
    assert len(desc_crs.parts) == 2
    assert desc_crs.parts[0].startswith("The crs property SHALL")


def test_recommendations_and_permissions_are_left_out():
    uris = _uris(parse_requirements(FEATURES, "ogcapi-features-1", "1.0", "17-069r4"))
    uris += _uris(parse_requirements(EDR, "ogcapi-edr-1", "1.1", "19-086r6"))

    assert not [uri for uri in uris if "/rec/" in uri or "/per/" in uri]


def test_a_quoted_requirement_belongs_to_its_own_document():
    assert parse_requirements(QUOTING, "ogcapi-common-1", "1.0", "19-072") == []


def test_the_class_is_the_segment_after_req():
    (requirement,) = parse_requirements(EDR, "ogcapi-edr-1", "1.1", "19-086r6")

    assert (
        requirement.conformance_class
        == "http://www.opengis.net/spec/ogcapi-edr-1/1.1/conf/core"
    )
    assert requirement.document == "19-086r6"


def test_a_lowercase_shall_is_a_requirement():
    text = (
        "Requirement 8 Identifier /req/core/query-param-value-boolean A Boolean values "
        "shall be represented by the lowercase strings true and false ."
    )

    (requirement,) = parse_requirements(text, "ogcapi-common-1", "1.0", "19-072")

    assert requirement.parts[0].startswith("Boolean values shall")


def test_a_requirement_that_reuses_another_is_read():
    text = (
        "Requirement 44 /req/gmlsf2/content A The requirement /req/gmlsf0/content "
        "applies, too, with the following changes . Requirement 45 /req/gmlsf2/headers "
        "A The server SHALL send headers ."
    )

    uris = [
        r.uri for r in parse_requirements(text, "ogcapi-features-1", "1.0", "17-069r4")
    ]

    assert uris == [
        "http://www.opengis.net/spec/ogcapi-features-1/1.0/req/gmlsf2/content",
        "http://www.opengis.net/spec/ogcapi-features-1/1.0/req/gmlsf2/headers",
    ]
