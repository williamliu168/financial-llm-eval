"""Extract every number from a piece of free text.

Ranges are matched first (longest-match-wins) so a span like ``$1.2-1.4B`` is read as one
range rather than two stray numbers; single numbers that fall inside a matched range are
then skipped.
"""

from __future__ import annotations

from ..result import ParsedNumber
from .normalize import detect_scale_header, normalize_range, normalize_single
from .tokens import RANGE_RE, SINGLE_RE


def _overlaps(span: tuple[int, int], taken: list[tuple[int, int]]) -> bool:
    start, end = span
    return any(start < t_end and t_start < end for t_start, t_end in taken)


def find_numbers(text: str, scale_hint: int | None = None) -> list[ParsedNumber]:
    """Return all numbers found in ``text``, ordered by position.

    ``scale_hint`` (e.g. ``1_000_000`` for a table reported "in millions") overrides any
    scale header detected in the text and applies to numbers lacking their own magnitude.
    """
    if not text:
        return []

    default_scale = scale_hint if scale_hint is not None else detect_scale_header(text)

    found: list[ParsedNumber] = []
    taken: list[tuple[int, int]] = []

    for m in RANGE_RE.finditer(text):
        found.append(normalize_range(m, default_scale))
        taken.append(m.span())

    for m in SINGLE_RE.finditer(text):
        if _overlaps(m.span(), taken):
            continue
        found.append(normalize_single(m, default_scale))

    found.sort(key=lambda p: p.span[0])
    return found
