"""The classification decision tree — the intellectual core of the library.

Given a parsed number and a ground-truth value, decide *how* (if at all) they differ. The
verdicts are assigned in a fixed precedence so the most specific, most actionable
diagnosis wins, and so a value that could be read several ways gets one deterministic
answer. The tree reasons only about the numbers themselves; it never reconstructs a
financial concept.
"""

from __future__ import annotations

import math

from .result import ParsedNumber, TolKind, Unit
from .verdict import Verdict

# How close ``expected / parsed`` must sit to a clean power of ten to call it a scale slip.
_SCALE_TOL = 0.01
# A scale slip beyond 10^4 is implausible; treat it as a plain mismatch instead.
_MAX_SCALE_K = 4
# Relative error above which a present-but-wrong number is flagged as "looks fabricated".
_FAB_THRESHOLD = 0.5


def _sign(x: float) -> int:
    if x == 0:
        return 0
    return 1 if x > 0 else -1


def within_tolerance(a: float, b: float, tol: float, tol_kind: TolKind) -> bool:
    """True if ``a`` is within tolerance of ``b`` (inclusive boundary).

    Relative tolerance is used by default; when the expected value is 0 (relative error
    is undefined) we fall back to treating ``tol`` as an absolute bound.
    """
    if tol_kind == "absolute" or b == 0:
        return abs(a - b) <= tol
    return abs(a - b) / abs(b) <= tol


def _clean_power_of_ten(parsed_value: float, expected: float) -> int | None:
    """Return ``k`` if ``expected/parsed`` is ~10**k for a non-zero, plausible ``k``.

    Returns ``None`` when the signs differ (a sign flip is reported separately, and a
    combined sign+scale error should fall through to MISMATCH rather than be excused).
    """
    if parsed_value == 0 or expected == 0:
        return None
    if _sign(parsed_value) != _sign(expected):
        return None
    ratio = abs(expected) / abs(parsed_value)
    k = round(math.log10(ratio))
    if k == 0 or abs(k) > _MAX_SCALE_K:
        return None
    if math.isclose(ratio, 10.0**k, rel_tol=_SCALE_TOL):
        return k
    return None


def _differs_only_by_rounding(parsed: ParsedNumber, expected: float) -> bool:
    """Placeholder until Milestone D fills in rounding detection."""
    return False


def _unit_reinterpretation(
    parsed: ParsedNumber, expected: float, tol: float, tol_kind: TolKind
) -> str | None:
    """Placeholder until Milestone D fills in unit-confusion detection."""
    return None


def classify(
    parsed: ParsedNumber | None,
    expected: float,
    *,
    tol: float,
    tol_kind: TolKind,
    expected_unit: Unit | None = None,
) -> tuple[Verdict, list[str], bool]:
    """Classify ``parsed`` against ``expected``.

    Returns ``(verdict, notes, looks_fabricated)``.
    """
    notes: list[str] = []

    # 0. No number was parsed from the answer.
    if parsed is None:
        return Verdict.MISSING, notes, False

    p = parsed.value
    e = expected

    # A range that brackets the truth is acceptable; otherwise judge the nearest endpoint.
    if parsed.is_range and parsed.range_value is not None:
        lo, hi = sorted(parsed.range_value)
        if lo <= e <= hi:
            notes.append(f"expected value falls within the stated range {lo:g}–{hi:g}")
            return Verdict.WITHIN_TOLERANCE, notes, False
        p = min((lo, hi), key=lambda x: abs(x - e))
        notes.append("compared against the nearer end of the stated range")

    # 1. EXACT — equal at the available precision.
    if p == e or math.isclose(p, e, rel_tol=1e-12, abs_tol=1e-12):
        return Verdict.EXACT, notes, False

    # 2. WITHIN_TOLERANCE — refined to ROUNDING when that is the only difference.
    if within_tolerance(p, e, tol, tol_kind):
        if _differs_only_by_rounding(parsed, e):
            notes.append("matches the truth rounded to the reported precision")
            return Verdict.ROUNDING, notes, False
        return Verdict.WITHIN_TOLERANCE, notes, False

    # 3. SIGN_ERROR — magnitude matches, sign is flipped (checked before scale: a sign
    #    flip is unambiguous, and a compound sign+scale error should stay a MISMATCH).
    if _sign(p) != _sign(e) and within_tolerance(abs(p), abs(e), tol, tol_kind):
        notes.append("magnitude matches but the sign is flipped")
        if parsed.is_negative_paren:
            notes.append("answer used accounting parentheses to denote a negative")
        return Verdict.SIGN_ERROR, notes, False

    # 4. SCALE_ERROR — right digits, wrong order of magnitude.
    k = _clean_power_of_ten(p, e)
    if k is not None:
        hint = " (e.g. millions vs billions)" if abs(k) == 3 else ""
        notes.append(f"right digits, wrong magnitude — off by 10^{k}{hint}")
        return Verdict.SCALE_ERROR, notes, False

    # 5. UNIT_CONFUSION — a related-unit reinterpretation lands within tolerance.
    reinterpretation = _unit_reinterpretation(parsed, e, tol, tol_kind)
    if reinterpretation is not None:
        notes.append(f"matches the truth under a {reinterpretation} reinterpretation")
        return Verdict.UNIT_CONFUSION, notes, False

    # 6. ROUNDING — last chance (correctly rounded but just outside tolerance).
    if _differs_only_by_rounding(parsed, e):
        notes.append("matches the truth rounded to the reported precision")
        return Verdict.ROUNDING, notes, False

    # 7. MISMATCH — a number is present but genuinely wrong.
    rel = abs(p - e) / abs(e) if e != 0 else math.inf
    looks_fabricated = rel > _FAB_THRESHOLD
    if looks_fabricated:
        notes.append("far outside tolerance and unexplained by scale/sign/unit/rounding")
    return Verdict.MISMATCH, notes, looks_fabricated
