"""The classification decision tree — the intellectual core of the library.

Given a parsed number and a ground-truth value, decide *how* (if at all) they differ. The
verdicts are assigned in a fixed precedence so the most specific, most actionable
diagnosis wins, and so a value that could be read several ways gets one deterministic
answer. The tree reasons only about the numbers themselves; it never reconstructs a
financial concept.
"""

from __future__ import annotations

import math
import re

from .result import ParsedNumber, TolKind, Unit
from .verdict import Verdict

# Decimal places written in a number's surface form, e.g. "3.14" -> 2, "1,200" -> 0.
_DECIMALS_RE = re.compile(r"\d*\.(\d+)")

# Units whose confusions (bps vs % vs ratio) are factors of ten and would otherwise be
# mislabeled as scale errors; for these we check unit confusion *before* scale.
_RATE_UNITS = ("percent", "bps", "ratio")

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


def _decimal_places(raw_text: str) -> int:
    match = _DECIMALS_RE.search(raw_text.replace(",", ""))
    return len(match.group(1)) if match else 0


def _differs_only_by_rounding(parsed: ParsedNumber, expected: float) -> bool:
    """True if the answer equals the truth rounded to the precision it reported.

    Comparison is done in the number's *surface* form (scale removed) so that, e.g.,
    "$3.14B" vs a truth of 3.14159e9 is recognized as a 2-decimal rounding rather than a
    spurious mismatch at billions scale.
    """
    if parsed.value == expected or parsed.scale == 0:
        return False
    decimals = _decimal_places(parsed.raw_text)
    surface_parsed = parsed.value / parsed.scale
    surface_expected = expected / parsed.scale
    return round(surface_expected, decimals) == round(surface_parsed, decimals)


def _unit_reinterpretation(
    parsed: ParsedNumber, expected: float, tol: float, tol_kind: TolKind
) -> str | None:
    """Name the related-unit reinterpretation of ``parsed`` that lands within tolerance of
    ``expected``, or ``None``. Covers percent ↔ ratio ↔ bps confusions."""
    v = parsed.value
    if parsed.unit == "percent":
        options = [("percent→ratio", v / 100.0), ("percent→bps", v * 100.0)]
    elif parsed.unit == "bps":
        options = [("bps→percent", v / 100.0), ("bps→ratio", v / 10_000.0)]
    elif parsed.unit in ("unknown", "ratio"):
        options = [
            ("ratio→percent", v * 100.0),
            ("percent→ratio", v / 100.0),
            ("ratio→bps", v * 10_000.0),
        ]
    else:
        return None
    for name, candidate in options:
        if within_tolerance(candidate, expected, tol, tol_kind):
            return name
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
        if parsed.sign_from_words:
            notes.append("answer stated a loss (or 'negative') in words; read as negative")
        return Verdict.SIGN_ERROR, notes, False

    # 4 & 5. SCALE_ERROR vs UNIT_CONFUSION. Both surface as factor-of-ten gaps, so the
    #        order matters: when the number carries a rate unit (%, bps) a ten-fold gap is
    #        far more likely a unit mix-up than a magnitude slip, so test that first.
    def scale_error() -> Verdict | None:
        k = _clean_power_of_ten(p, e)
        if k is None:
            return None
        hint = " (e.g. millions vs billions)" if abs(k) == 3 else ""
        notes.append(f"right digits, wrong magnitude — off by 10^{k}{hint}")
        return Verdict.SCALE_ERROR

    def unit_confusion() -> Verdict | None:
        reinterpretation = _unit_reinterpretation(parsed, e, tol, tol_kind)
        if reinterpretation is None:
            return None
        notes.append(f"matches the truth under a {reinterpretation} reinterpretation")
        return Verdict.UNIT_CONFUSION

    rate_tagged = parsed.unit in _RATE_UNITS or expected_unit in _RATE_UNITS
    checks = (unit_confusion, scale_error) if rate_tagged else (scale_error, unit_confusion)
    for check in checks:
        verdict = check()
        if verdict is not None:
            return verdict, notes, False

    # 6. ROUNDING — last chance: correctly rounded but just outside tolerance. Require at
    #    least one reported decimal, so a coarse whole-number answer (e.g. "$3B" for a
    #    truth of $3.49B) is not excused as rounding.
    if _decimal_places(parsed.raw_text) >= 1 and _differs_only_by_rounding(parsed, e):
        notes.append("matches the truth rounded to the reported precision")
        return Verdict.ROUNDING, notes, False

    # 7. MISMATCH — a number is present but genuinely wrong.
    rel = abs(p - e) / abs(e) if e != 0 else math.inf
    looks_fabricated = rel > _FAB_THRESHOLD
    if looks_fabricated:
        notes.append("far outside tolerance and unexplained by scale/sign/unit/rounding")
    return Verdict.MISMATCH, notes, looks_fabricated
