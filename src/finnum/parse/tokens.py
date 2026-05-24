"""Lexical tables and compiled patterns for the number parser.

Every rule here corresponds to a *public* convention for how numbers appear in
financial prose — magnitude abbreviations, currency symbols, accounting parentheses for
negatives, basis points, and "(in millions)"-style scale headers. See
``PARSING_REFERENCES.md`` for the sources. Nothing here encodes any domain-specific
synthesis, reconciliation, or normalization logic.
"""

from __future__ import annotations

import re

# Magnitude words/abbreviations → multiplier. Plurals ("millions") are folded by the
# parser. "MM"/"mn" (million) and "bn" (billion) are standard finance shorthand.
MAGNITUDE: dict[str, int] = {
    "k": 1_000,
    "thousand": 1_000,
    "m": 1_000_000,
    "mm": 1_000_000,
    "mn": 1_000_000,
    "million": 1_000_000,
    "b": 1_000_000_000,
    "bn": 1_000_000_000,
    "billion": 1_000_000_000,
    "t": 1_000_000_000_000,
    "trillion": 1_000_000_000_000,
}

# Unicode currency symbols → ISO 4217 code (tag only; no FX conversion is ever performed).
CURRENCY_SYMBOL: dict[str, str] = {"$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY"}

# --- regex fragments (combined below) ---
_NUM = r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?|\.\d+"
_MAG = r"thousands?|millions?|billions?|trillions?|mn|bn|mm|[kmbt]"
_CUR = r"[$€£¥]"
_SIGN = r"[-+−]"  # ASCII -, +, and the Unicode minus sign
_APPROX = r"~|≈|\b(?:about|approximately|approx\.?|roughly|around|circa)\b"
_PCT = r"%|percent|pct"
_BPS = r"bps|bp|basis\s+points?"
_SEP = r"-|–|—|to"  # hyphen, en dash, em dash, or the word "to"

# A single financial number, with optional approximation marker, currency, accounting
# parentheses, sign, magnitude (inside or outside the parentheses), and trailing unit.
SINGLE_RE = re.compile(
    rf"""
    (?P<approx>{_APPROX})?
    \s*
    (?P<sign1>{_SIGN})?        # sign before the currency symbol, e.g. -$88.5B
    \s*
    (?P<cur1>{_CUR})?          # currency before an opening paren, e.g. $(1.2)
    \s*
    (?P<openparen>\()?         # accounting-negative opening paren
    \s*
    (?P<cur2>{_CUR})?          # currency in the normal position, e.g. $1.2 or ($1.2)
    \s*
    (?P<sign>{_SIGN})?
    (?P<num>{_NUM})
    (?:\s*(?P<mag_in>{_MAG})(?![a-z]))?      # magnitude before a closing paren
    (?(openparen)\s*\))                       # require ")" iff we matched "("
    (?:\s*(?P<mag_out>{_MAG})(?![a-z]))?      # magnitude after a closing paren, e.g. (1.2)B
    (?:\s*(?P<unit>{_PCT}|{_BPS})(?![a-z]))?
    """,
    re.IGNORECASE | re.VERBOSE,
)

# A numeric range, e.g. "$1.2-1.4B", "1.2 to 1.4 billion", "12% to 14%". A magnitude or
# currency on one side is shared with the other when that side omits it.
RANGE_RE = re.compile(
    rf"""
    (?P<approx>{_APPROX})?
    \s*
    (?P<cur1>{_CUR})?
    \s*
    (?P<lo>{_NUM})
    (?:\s*(?P<lomag>{_MAG})(?![a-z]))?
    (?:\s*(?P<unit_lo>{_PCT}|{_BPS})(?![a-z]))?   # unit on the first element, e.g. "12% to 14%"
    \s*(?:{_SEP})\s*
    (?P<cur2>{_CUR})?
    \s*
    (?P<hi>{_NUM})
    (?:\s*(?P<himag>{_MAG})(?![a-z]))?
    (?:\s*(?P<unit>{_PCT}|{_BPS})(?![a-z]))?
    """,
    re.IGNORECASE | re.VERBOSE,
)

# "(in thousands)", "$ in millions", "amounts in billions" → a default scale multiplier
# applied to bare numbers that carry no explicit magnitude of their own.
SCALE_HEADER_RE = re.compile(r"in\s+(thousand|million|billion)s?\b", re.IGNORECASE)
