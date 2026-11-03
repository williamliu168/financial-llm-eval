"""Turn a regex match into a canonical :class:`ParsedNumber`.

Canonicalization means: resolve the sign (including accounting parentheses), fold in any
magnitude word or table-scale header, and tag the unit (currency / percent / bps) with a
canonical ``as_ratio`` for rate-like numbers. The output value is directly comparable to
a ground-truth number; nothing here interprets the number as a financial *concept*.
"""

from __future__ import annotations

import re

from ..result import ParsedNumber, Unit
from .tokens import CURRENCY_SYMBOL, MAGNITUDE, SCALE_HEADER_RE

_MINUS = {"-", "−"}  # ASCII hyphen-minus and the Unicode minus sign


def magnitude_multiplier(token: str | None) -> int:
    """Multiplier for a magnitude token ("M", "bn", "millions", ...); 1 if ``None``."""
    if not token:
        return 1
    key = token.lower()
    return MAGNITUDE.get(key) or MAGNITUDE.get(key.rstrip("s")) or 1


def detect_scale_header(text: str) -> int | None:
    """Default scale implied by a "(in millions)"-style header, if present."""
    m = SCALE_HEADER_RE.search(text)
    if not m:
        return None
    return MAGNITUDE[m.group(1).lower()]


def _classify_unit(
    unit_token: str | None, currency: str | None, value: float
) -> tuple[Unit, float | None]:
    """Map a matched unit token to a canonical ``Unit`` and ``as_ratio``."""
    if unit_token:
        token = unit_token.lower().replace(" ", "")
        if token in {"%", "percent", "pct"}:
            return "percent", value / 100.0
        if token.startswith("bp") or "basispoint" in token:
            return "bps", value / 10_000.0
    if currency:
        return "currency", None
    return "unknown", None


def normalize_single(match: re.Match[str], default_scale: int | None) -> ParsedNumber:
    """Build a :class:`ParsedNumber` from a ``SINGLE_RE`` match."""
    g = match.groupdict()
    base = float(g["num"].replace(",", ""))

    mag_token = g.get("mag_in") or g.get("mag_out")
    has_explicit_magnitude = mag_token is not None
    multiplier = magnitude_multiplier(mag_token)

    scale = multiplier
    value = base * multiplier
    # A "(in millions)" header (or an explicit scale_hint) applies only when the number
    # carries no magnitude of its own — an explicit "B" always wins.
    if not has_explicit_magnitude and default_scale:
        value *= default_scale
        scale = default_scale

    is_paren = bool(g.get("openparen"))
    negative = is_paren or g.get("sign") in {"-", "−"} or g.get("sign1") in {"-", "−"}
    if negative:
        value = -value

    cur_symbol = g.get("cur1") or g.get("cur2")
    currency = CURRENCY_SYMBOL.get(cur_symbol) if cur_symbol else None

    unit, as_ratio = _classify_unit(g.get("unit"), currency, value)

    return ParsedNumber(
        raw_text=match.group(0).strip(),
        span=match.span(),
        value=value,
        unit=unit,
        scale=scale,
        is_negative_paren=is_paren,
        is_approximate=bool(g.get("approx")),
        currency=currency,
        as_ratio=as_ratio,
    )


def normalize_range(match: re.Match[str], default_scale: int | None) -> ParsedNumber:
    """Build a range :class:`ParsedNumber` (value = midpoint) from a ``RANGE_RE`` match."""
    g = match.groupdict()
    lo = float(g["lo"].replace(",", ""))
    hi = float(g["hi"].replace(",", ""))

    lomag, himag = g.get("lomag"), g.get("himag")
    has_explicit_magnitude = bool(lomag or himag)
    # A magnitude on one side is shared with the other (e.g. "$1.2-1.4B").
    lo *= magnitude_multiplier(lomag or himag)
    hi *= magnitude_multiplier(himag or lomag)
    if not has_explicit_magnitude and default_scale:
        lo *= default_scale
        hi *= default_scale
    # Signs are per endpoint and never shared: "-1% to 2%" is a legitimate range.
    if g.get("sign_lo") in _MINUS or g.get("sign_lo_in") in _MINUS:
        lo = -lo
    if g.get("sign_hi") in _MINUS or g.get("sign_hi_in") in _MINUS:
        hi = -hi

    midpoint = (lo + hi) / 2.0
    cur_symbol = g.get("cur1") or g.get("cur2")
    currency = CURRENCY_SYMBOL.get(cur_symbol) if cur_symbol else None
    unit, as_ratio = _classify_unit(g.get("unit") or g.get("unit_lo"), currency, midpoint)

    return ParsedNumber(
        raw_text=match.group(0).strip(),
        span=match.span(),
        value=midpoint,
        unit=unit,
        scale=magnitude_multiplier(lomag or himag),
        is_approximate=bool(g.get("approx")),
        is_range=True,
        range_value=(lo, hi),
        currency=currency,
        as_ratio=as_ratio,
    )
