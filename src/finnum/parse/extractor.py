"""Extract every number from a piece of free text.

Ranges are matched first (longest-match-wins) so a span like ``$1.2-1.4B`` is read as one
range rather than two stray numbers; single numbers that fall inside a matched range are
then skipped. A range match whose two sides are different quantities ("grew 2% to $391B")
or a change ("from $383B to $391B") is rejected, and its numbers are parsed individually.
"""

from __future__ import annotations

import re

from ..result import ParsedNumber
from .normalize import detect_scale_header, normalize_range, normalize_single
from .tokens import RANGE_RE, SINGLE_RE

# "from X to Y" states two values (a change), unless it is "ranges/ranging from X to Y".
_FROM_BEFORE_RE = re.compile(r"\bfrom\s*$", re.IGNORECASE)
_RANGES_FROM_BEFORE_RE = re.compile(r"\brang(?:e|es|ed|ing)\s+from\s*$", re.IGNORECASE)


def _overlaps(span: tuple[int, int], taken: list[tuple[int, int]]) -> bool:
    start, end = span
    return any(start < t_end and t_start < end for t_start, t_end in taken)


def _rate_kind(token: str | None) -> str | None:
    if not token:
        return None
    return "percent" if token.lower() in {"%", "percent", "pct"} else "bps"


def _is_coherent_range(m: re.Match[str], text: str) -> bool:
    """True if a ``RANGE_RE`` match is one quantity's range, not two quantities or a change.

    A rate unit is a suffix, so in a real range it sits on the second value (or both);
    a currency symbol is a prefix, so it sits on the first value (or both).
    """
    g = m.groupdict()
    lo_rate, hi_rate = _rate_kind(g["unit_lo"]), _rate_kind(g["unit"])
    if lo_rate and lo_rate != hi_rate:  # "2% to $391B", "250 bps to 12.5%", "3% to 1,234"
        return False
    if hi_rate and (g["cur1"] or g["cur2"] or g["lomag"] or g["himag"]):  # "$5M to 10%"
        return False
    if g["cur2"] and g["cur2"] != g["cur1"]:  # "7 points to $8.2B", "$5 to €6"
        return False
    if g["sep"].lower() == "to":
        before = text[max(0, m.start() - 40) : m.start()]
        if _FROM_BEFORE_RE.search(before) and not _RANGES_FROM_BEFORE_RE.search(before):
            return False  # "rose from $383.3B to $391.0B"
    return True


def _is_identifier(text: str, m: re.Match[str], *marker_groups: str) -> bool:
    """True if a bare number is part of an identifier, not a quantity: FY2024, Q3, 1Q24,
    Form 10-K, COVID-19, 3-for-1, Item 7A. Numbers carrying a currency, magnitude, unit
    or parentheses are never treated as identifiers ("US$3.4 million", "$3.4B", "12.5%")."""
    if any(m.group(name) for name in marker_groups):
        return False
    raw = m.group(0)
    start, end = m.start() + len(raw) - len(raw.lstrip()), m.end()
    before = text[start - 1] if start > 0 else ""
    after, after2 = text[end : end + 1], text[end + 1 : end + 2]
    if text[start] in "-+−" and before.isalnum():  # a hyphen, not a minus: "COVID-19"
        return True
    if before.isalpha():  # "FY2024", "Q3"
        return True
    if after.isalpha() and not (after in "xX" and not after2.isalnum()):  # "1Q24"; keep "1.2x"
        return True
    return after in "-–" and after2.isalpha()  # "10-K", "3-for-1", "5-year"


_SINGLE_MARKERS = ("cur1", "cur2", "openparen", "mag_in", "mag_out", "unit")
_RANGE_MARKERS = ("cur1", "cur2", "lomag", "himag", "unit_lo", "unit")


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

    pos = 0
    while (m := RANGE_RE.search(text, pos)) is not None:
        if _is_coherent_range(m, text) and not _is_identifier(text, m, *_RANGE_MARKERS):
            found.append(normalize_range(m, default_scale))
            taken.append(m.span())
            pos = m.end()
        else:
            # Re-scan from just after the first value, so a genuine range that starts at
            # the second value ("grew 2% to $1.2-1.4B") is still found.
            pos = m.end("lo")

    for m in SINGLE_RE.finditer(text):
        if _overlaps(m.span(), taken) or _is_identifier(text, m, *_SINGLE_MARKERS):
            continue
        found.append(normalize_single(m, default_scale))

    found.sort(key=lambda p: p.span[0])
    return found
