"""What a standard expects, in the standard's own words.

An expectation records one thing a document demands — a path, an
operation, a parameter — together with **the verb the standard used** and
the clause that used it. The verb is not decoration: OGC drafting
reserves `shall` for requirements and `should` for recommendations
(Terms and definitions in each standard, following OGC Policy Directive
49, which notes it is "shall", not "must"). Severity follows from it,
rather than each call site choosing one.

The condition matters as much as the verb. Both defects this library
carried were conditional clauses read as unconditional: the tiling
schemes endpoint is a SHOULD *when the API uses a tile matrix set not
available in a register*, and `bbox-crs` is owed *where `bbox` is
supported*. So an expectation may carry its condition, and the rule is
blunt:

    a condition the code cannot evaluate is never an error.

Recording the clause and declining to act on it is more useful than
deleting it: the knowledge stays, and nobody re-adds it as a requirement
a year from now.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .models import ErrorSeverity


class Verb(str, Enum):
    """The normative verb a standard used for an expectation."""

    SHALL = "shall"
    SHOULD = "should"
    MAY = "may"

    @property
    def severity(self) -> ErrorSeverity:
        """How failing this expectation should be reported."""
        return {
            Verb.SHALL: ErrorSeverity.CRITICAL,
            Verb.SHOULD: ErrorSeverity.WARNING,
            Verb.MAY: ErrorSeverity.INFO,
        }[self]


@dataclass(frozen=True, slots=True)
class Expectation:
    """One thing a standard expects, and where it says so."""

    target: str
    verb: Verb
    source: str
    condition: str | None = None

    @property
    def is_evaluable(self) -> bool:
        """Whether the expectation applies unconditionally.

        Nothing here can weigh a condition yet; one that carries any is
        reported as context, never as a fault.
        """
        return self.condition is None

    @property
    def severity(self) -> ErrorSeverity:
        return self.verb.severity
