"""The verdict taxonomy emitted by the comparator.

A ``Verdict`` does not merely say *whether* a number is right — it says *how* it is
wrong, which is the diagnostic the rest of the library is built around.
"""

from __future__ import annotations

from enum import Enum


class Verdict(str, Enum):
    """How a parsed number relates to the ground-truth value.

    Subclasses ``str`` so members serialize directly to their name in JSON and
    compare equal to the plain string (``Verdict.EXACT == "EXACT"``).
    """

    EXACT = "EXACT"  # equal at the full precision available in the answer text
    WITHIN_TOLERANCE = "WITHIN_TOLERANCE"  # not exact, but inside the tolerance band
    ROUNDING = "ROUNDING"  # differs only because the answer reported fewer digits
    SCALE_ERROR = "SCALE_ERROR"  # right digits, wrong magnitude (millions vs billions)
    SIGN_ERROR = "SIGN_ERROR"  # magnitude matches, sign is flipped (incl. accounting parentheses)
    UNIT_CONFUSION = "UNIT_CONFUSION"  # related-unit mix-up (bps vs % vs ratio, $ vs ratio)
    MISSING = "MISSING"  # no parseable number found in the answer
    MISMATCH = "MISMATCH"  # a number is present but genuinely wrong (see Result.looks_fabricated)

    @property
    def is_pass(self) -> bool:
        """True when the answer's number is acceptably correct."""
        return self in _PASSING


_PASSING = frozenset({Verdict.EXACT, Verdict.WITHIN_TOLERANCE, Verdict.ROUNDING})

# ``FABRICATED`` is a framing alias, not a separate verdict: a fabricated number is a
# MISMATCH that is far outside tolerance and unexplained by scale/sign/unit/rounding.
# Splitting it into its own enum member would invite a distinction we cannot draw
# deterministically; instead, ``Result.looks_fabricated`` flags the egregious case.
FABRICATED = Verdict.MISMATCH
