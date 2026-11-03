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
# A sign must touch what it negates: "-$5B" is negative, "Revenue - $5B" uses a dash.
_GLUED_SIGN = rf"{_SIGN}(?=[$€£¥(\d.])"
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
    (?P<sign1>{_GLUED_SIGN})?  # sign before the currency symbol, e.g. -$88.5B
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

# A numeric range, e.g. "$1.2-1.4B", "1.2 to 1.4 billion", "12% to 14%", "-$1.2 to -$1.4B".
# A magnitude or currency on one side is shared with the other when that side omits it.
# The regex is deliberately permissive; ``extractor`` rejects matches whose two sides are
# different quantities ("grew 2% to $391B") or a change ("from $383B to $391B").
RANGE_RE = re.compile(
    rf"""
    (?P<approx>{_APPROX})?
    \s*
    (?P<sign_lo>{_GLUED_SIGN})?
    \s*
    (?P<cur1>{_CUR})?
    \s*
    (?P<sign_lo_in>{_SIGN})?
    (?P<lo>{_NUM})
    (?:\s*(?P<lomag>{_MAG})(?![a-z]))?
    (?:\s*(?P<unit_lo>{_PCT}|{_BPS})(?![a-z]))?   # unit on the first element, e.g. "12% to 14%"
    \s*(?P<sep>{_SEP})\s*
    (?P<sign_hi>{_GLUED_SIGN})?
    \s*
    (?P<cur2>{_CUR})?
    \s*
    (?P<sign_hi_in>{_SIGN})?
    (?P<hi>{_NUM})
    (?:\s*(?P<himag>{_MAG})(?![a-z]))?
    (?:\s*(?P<unit>{_PCT}|{_BPS})(?![a-z]))?
    """,
    re.IGNORECASE | re.VERBOSE,
)

# A loss or "negative" stated in words right before a figure carries its sign, the way
# accounting parentheses do in a table: "net loss of $1.2 billion", "diluted loss per share
# was $0.56", "net loss attributable to common stockholders: $31.3 million".
LOSS_CUE_RE = re.compile(
    r"""
    (?:\b(?:net|operating|pre-?tax|comprehensive)\s+)?\bloss(?:es)?
    (?:\s+from\s+operations|\s+per\s+(?:basic\s+|diluted\s+)?share
       |\s+attributable\s+to\s+[a-z][a-z\s&'.-]{0,40}?)?
    \s*(?:of|was|were|totaled|totalled|amounted\s+to|came\s+in\s+at|:)
    (?:\s+(?:about|approximately|roughly|around))?\s*$
    |\bnegative\s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

# "(in thousands)", "$ in millions", "amounts in billions" → a default scale multiplier
# applied to bare numbers that carry no explicit magnitude of their own.
SCALE_HEADER_RE = re.compile(r"\bin\s+(thousand|million|billion)s?\b", re.IGNORECASE)

# Calendar dates are not quantities; their digits are masked before extraction so that
# "fiscal year ended September 28, 2024" does not add 28 and 2024 as candidates.
_MONTH = (
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?"
    r"|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\.?"
)
DATE_RE = re.compile(
    rf"\b{_MONTH}\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+\d{{4}}\b"  # September 28, 2024
    rf"|\b\d{{1,2}}\s+{_MONTH}\s+\d{{4}}\b"  # 28 September 2024
    r"|\b\d{4}-\d{2}-\d{2}\b"  # 2024-09-28
    r"|\b\d{1,2}/\d{1,2}/\d{2,4}\b",  # 9/28/2024
    re.IGNORECASE,
)
