"""Compare a declared conformance list against the published standards.

The catalogue this reads lives in `known_classes`, generated from the
standards themselves. What the comparison deliberately does not say is
whether a missing class *ought* to be there: almost every class is
optional, and the few that are not follow from each standard's
dependency graph rather than from anything in the URI. Reporting an
absence as a fault is how a validator comes to call a compliant server
non-compliant.

So the report answers three questions a caller can act on without any
such judgement: which declarations the standards recognise, which they
do not, and which sibling classes exist in a standard the API already
claims — useful to notice a capability you implement and forgot to
declare, which is a real and common mistake.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .known_classes import KNOWN_CONFORMANCE_CLASSES, KnownConformanceClass
from .ogc_types import ConformanceClass


@dataclass(frozen=True, slots=True)
class ConformanceReport:
    """What the published standards say about a declared conformance list."""

    recognised: tuple[KnownConformanceClass, ...]
    unrecognised: tuple[str, ...]
    undeclared_siblings: tuple[KnownConformanceClass, ...]

    @property
    def specifications(self) -> tuple[str, ...]:
        """The standards the declaration draws on, in order."""
        seen: dict[str, None] = {}
        for known in self.recognised:
            seen.setdefault(known.spec, None)
        return tuple(seen)


def _uris(declared: Iterable[ConformanceClass | str]) -> list[str]:
    return [item if isinstance(item, str) else item.uri for item in declared]


def validate_conformance(
    declared: Iterable[ConformanceClass | str],
) -> ConformanceReport:
    """Compare a declaration against the catalogue of published classes.

    `unrecognised` holds what no catalogued standard defines. That is
    worth looking at — a typo, a draft, or a standard this catalogue does
    not cover yet — but it is not by itself an error.

    `undeclared_siblings` holds classes belonging to a standard the
    declaration already draws on, which it does not mention. Most are
    optional and their absence means nothing; the list is there to be
    read, not to be failed on.
    """
    uris = _uris(declared)
    seen = set(uris)

    recognised = tuple(
        KNOWN_CONFORMANCE_CLASSES[uri]
        for uri in uris
        if uri in KNOWN_CONFORMANCE_CLASSES
    )
    unrecognised = tuple(uri for uri in uris if uri not in KNOWN_CONFORMANCE_CLASSES)

    specifications = {known.spec for known in recognised}
    undeclared_siblings = tuple(
        known
        for uri, known in sorted(KNOWN_CONFORMANCE_CLASSES.items())
        if known.spec in specifications and uri not in seen
    )

    return ConformanceReport(
        recognised=recognised,
        unrecognised=unrecognised,
        undeclared_siblings=undeclared_siblings,
    )
