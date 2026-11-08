"""Requirements read from the text of a published OGC API standard.

A standard states each requirement once, under a header such as
``Requirement 2 /req/core/root-success`` or
``Requirement A.1 Identifier /req/core/root-op``, followed by its parts
(``A``, ``B``, or ``Statement A:``) or by a single statement. The same
identifier comes back elsewhere: in the list of a requirements class,
which has no text, and in the abstract tests, written
``Requirement Requirement 1:`` or ``Requirements:``. Only a header followed
by the requirement's own statement counts: one that starts with its part
``A``, or says *shall*.

Recommendations (``/rec/``) and permissions (``/per/``) are not
requirements and are left out.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_HEADER = re.compile(
    r"(?<!Requirement )Requirement (?:[A-Z]\.)?\d+:? (?:Identifier )?"
    r"/req/([a-z0-9-]+)/([a-z0-9-]+)(?![a-z0-9/-])"
)
_END = re.compile(
    r"(?:Requirement|Recommendation|Permission) (?:[A-Z]\.)?\d+"
    r"|Abstract test|Conformance Test|(?<!Included in )Requirements class \d"
    r"|\b\d+(?:\.\d+)+\. [A-Z]"
)
_INCLUDED = re.compile(r"^Included in Requirements class [^:]*: \S+ ")
_CONDITION = re.compile(r"^Condition .*?(?= (?:Statement )?A:? )")


@dataclass(frozen=True, slots=True)
class KnownRequirement:
    """A requirement a published standard states.

    Attributes
    ----------
    uri
        The requirement's identifier as a full URI with ``http://``, such as
        ``http://www.opengis.net/spec/ogcapi-maps-1/1.0/req/collection-map/desc-crs``.
    conformance_class
        The URI of the conformance class whose requirements class states it.
    document
        The OGC document number the requirement was read from.
    parts
        The statements of the requirement, in order: one per lettered part,
        or a single one when the standard gives no letters.
    """

    uri: str
    conformance_class: str
    document: str
    parts: tuple[str, ...]


def parse_requirements(
    text: str, spec: str, version: str, document: str
) -> list[KnownRequirement]:
    """Read the requirements a standard states, in the order it states them.

    Parameters
    ----------
    text
        The standard, stripped to text with its whitespace collapsed.
    spec
        The name of the standard in its URIs, such as ``ogcapi-maps-1``.
    version
        The version in its URIs, such as ``1.0``.
    document
        The OGC document number, recorded on each requirement.

    Returns
    -------
    list of KnownRequirement
        One per requirement, from its first header followed by a statement.
    """
    base = f"http://www.opengis.net/spec/{spec}/{version}"
    found: dict[str, KnownRequirement] = {}
    for header in _HEADER.finditer(text):
        name, item = header.groups()
        uri = f"{base}/req/{name}/{item}"
        if uri in found:
            continue
        end = _END.search(text, header.end())
        body = text[header.end() : end.start() if end else len(text)].strip()
        if not _is_statement(body):
            continue
        found[uri] = KnownRequirement(
            uri=uri,
            conformance_class=f"{base}/conf/{name}",
            document=document,
            parts=_split_parts(body),
        )
    return list(found.values())


def _is_statement(body: str) -> bool:
    """Tell whether the text after a header states a requirement.

    The list of a requirements class repeats the headers with no statement
    after them. A statement starts with its part ``A``, or says *shall*,
    in whatever case the standard writes it.

    Parameters
    ----------
    body
        The text after the header, up to the next header.

    Returns
    -------
    bool
        True when the text is the requirement's own statement.
    """
    bare = _CONDITION.sub("", _INCLUDED.sub("", body))
    return bool(re.match(r"(?:Statement )?A:? ", bare)) or "shall" in bare.lower()


def _split_parts(body: str) -> tuple[str, ...]:
    """Split a requirement's text into its lettered parts.

    Parameters
    ----------
    body
        The text after the header, up to the next header.

    Returns
    -------
    tuple of str
        One statement per letter ``A``, ``B``, …, or the whole text when it
        does not start with ``A``.
    """
    body = _INCLUDED.sub("", body)
    body = _CONDITION.sub("", body)
    first = re.match(r"(?:Statement )?A:? ", body)
    if first is None:
        return (body,)
    starts = [(first.start(), first.end())]
    letter = "B"
    while True:
        marker = re.compile(rf"(?<= )(?:Statement )?{letter}:? (?=\S)").search(
            body, starts[-1][1]
        )
        if marker is None:
            break
        starts.append((marker.start(), marker.end()))
        letter = chr(ord(letter) + 1)
    ends = [start for start, _ in starts[1:]] + [len(body)]
    return tuple(
        body[end_of_marker:stop].strip()
        for (_, end_of_marker), stop in zip(starts, ends)
    )
