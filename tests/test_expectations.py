"""Expectations carry the standard's verb, its clause and its condition."""

from __future__ import annotations

import pytest

from ogcapi_registry.expectations import Expectation, Verb
from ogcapi_registry.models import ErrorSeverity
from ogcapi_registry.ogc_types import ConformanceClass
from ogcapi_registry.strategies.tiles import TilesStrategy

TILESETS_LIST = "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/tilesets-list"
GEODATA_TILESETS = (
    "http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/geodata-tilesets"
)


class TestVerb:
    """The verb decides the severity, so nobody has to decide it twice."""

    def test_shall_is_an_error(self):
        assert Verb.SHALL.severity is ErrorSeverity.CRITICAL

    def test_should_is_a_warning(self):
        assert Verb.SHOULD.severity is ErrorSeverity.WARNING

    def test_may_is_information(self):
        assert Verb.MAY.severity is ErrorSeverity.INFO


class TestExpectation:
    def test_an_unconditional_expectation_can_be_evaluated(self):
        expectation = Expectation(
            target="/tiles",
            verb=Verb.SHALL,
            source="OGC API - Tiles Part 1, /req/tilesets-list/tileset-path",
        )

        assert expectation.is_evaluable
        assert expectation.severity is ErrorSeverity.CRITICAL

    def test_a_condition_makes_it_unevaluable(self):
        expectation = Expectation(
            target="/tileMatrixSets",
            verb=Verb.SHOULD,
            source="OGC API - Tiles Part 1, tiling schemes clauses B-D",
            condition="the API uses a tile matrix set not available in a register",
        )

        assert not expectation.is_evaluable


class TestStrategyExpectations:
    """What the tiles strategy expects, and on whose authority."""

    @pytest.fixture
    def strategy(self):
        return TilesStrategy()

    @pytest.fixture
    def classes(self):
        return [
            ConformanceClass(uri=TILESETS_LIST),
            ConformanceClass(uri=GEODATA_TILESETS),
        ]

    def test_every_expectation_cites_a_clause(self, strategy, classes):
        """An expectation nobody can check is an assumption with a verb."""
        expectations = strategy.get_expectations(classes)

        assert expectations
        for expectation in expectations:
            assert expectation.source

    def test_the_tilesets_list_is_required_on_the_standard_s_authority(
        self, strategy, classes
    ):
        expectations = {e.target: e for e in strategy.get_expectations(classes)}

        tiles = expectations["/collections/{collectionId}/tiles"]
        assert tiles.verb is Verb.SHALL
        assert "geodata-tilesets" in tiles.source

    def test_the_tiling_schemes_endpoint_is_recorded_and_not_demanded(
        self, strategy, classes
    ):
        """It was deleted outright in #10; recording it is better.

        The clause exists, it is a SHOULD, and it applies only when the
        API uses a tile matrix set that is not in a register. Keeping it
        with its condition means the knowledge survives and nobody
        re-adds it as a requirement.
        """
        expectations = {e.target: e for e in strategy.get_expectations(classes)}

        schemes = expectations["/tileMatrixSets"]
        assert schemes.verb is Verb.SHOULD
        assert not schemes.is_evaluable

    def test_required_paths_only_lists_what_can_be_demanded(self, strategy, classes):
        """The old contract still holds, and says nothing conditional."""
        paths = strategy.get_required_paths(classes)

        assert "/collections/{collectionId}/tiles" in paths
        assert "/tileMatrixSets" not in paths
