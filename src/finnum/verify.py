"""Public entry point: :func:`verify` — extract numbers, select one, classify it."""

from __future__ import annotations

from .compare import classify
from .parse import find_numbers
from .result import ParsedNumber, Result, TolKind, Unit
from .select import SELECT_STRATEGIES, prefer_by_hint, select_candidate
from .verdict import Verdict

# Rank used by the ``best_verdict`` selection strategy (lower is better).
_VERDICT_RANK = {
    Verdict.EXACT: 0,
    Verdict.WITHIN_TOLERANCE: 1,
    Verdict.ROUNDING: 2,
    Verdict.SIGN_ERROR: 3,
    Verdict.UNIT_CONFUSION: 4,
    Verdict.SCALE_ERROR: 5,
    Verdict.MISMATCH: 6,
    Verdict.MISSING: 7,
}


def _best_by_verdict(
    candidates: list[ParsedNumber], expected: float, tol: float, tol_kind: TolKind
) -> ParsedNumber:
    def key(c: ParsedNumber) -> tuple[int, float]:
        verdict, _, _ = classify(c, expected, tol=tol, tol_kind=tol_kind)
        return _VERDICT_RANK[verdict], abs(c.value - expected)

    return min(candidates, key=key)


def _choose(
    text: str,
    candidates: list[ParsedNumber],
    expected: float,
    strategy: str,
    target_hint: str | None,
    tol: float,
    tol_kind: TolKind,
) -> ParsedNumber | None:
    if not candidates:
        return None
    if target_hint:
        hinted = prefer_by_hint(text, candidates, target_hint)
        if hinted is not None:
            return hinted
    if strategy == "best_verdict":
        return _best_by_verdict(candidates, expected, tol, tol_kind)
    return select_candidate(candidates, expected, strategy=strategy)


def verify(
    answer_text: str,
    truth: float,
    *,
    unit: Unit | None = None,
    tol: float = 0.005,
    tol_kind: TolKind = "relative",
    scale_hint: int | None = None,
    select: str = "closest",
    target_hint: str | None = None,
) -> Result:
    """Verify the number(s) in ``answer_text`` against ``truth``.

    Extracts candidate numbers, picks the one to judge per ``select`` (default
    ``"closest"``), and classifies it. The returned :class:`Result`'s ``verdict``
    diagnoses *how* the number is wrong (scale, sign, unit, rounding, ...), not merely
    whether it passed.

    Args:
        answer_text: The LLM output to check.
        truth: The ground-truth value, expressed in the same unit you expect the answer in.
        unit: Optional expected unit, recorded on the result.
        tol: Tolerance (default 0.5% relative).
        tol_kind: ``"relative"`` (default) or ``"absolute"``.
        scale_hint: Multiplier for bare numbers (e.g. ``1_000_000`` for an "in millions"
            table); overridden by an explicit magnitude in the text.
        select: Candidate-selection strategy; one of ``closest``, ``first``, ``last``,
            ``only``, ``best_verdict``.
        target_hint: Optional phrase; prefer the number nearest this phrase in the text.
    """
    if select not in SELECT_STRATEGIES:
        raise ValueError(f"unknown select strategy: {select!r} (choose from {SELECT_STRATEGIES})")

    candidates = find_numbers(answer_text, scale_hint=scale_hint)
    chosen = _choose(answer_text, candidates, truth, select, target_hint, tol, tol_kind)

    if chosen is None:
        return Result(
            verdict=Verdict.MISSING,
            parsed_value=None,
            expected=truth,
            expected_unit=unit,
            tol=tol,
            tol_kind=tol_kind,
            candidates=tuple(candidates),
        )

    verdict, notes, looks_fabricated = classify(
        chosen, truth, tol=tol, tol_kind=tol_kind, expected_unit=unit
    )
    abs_error = abs(chosen.value - truth)
    rel_error = abs_error / abs(truth) if truth != 0 else None

    return Result(
        verdict=verdict,
        parsed_value=chosen.value,
        expected=truth,
        abs_error=abs_error,
        rel_error=rel_error,
        matched_span=chosen.span,
        matched_text=chosen.raw_text,
        parsed_unit=chosen.unit,
        expected_unit=unit,
        tol=tol,
        tol_kind=tol_kind,
        notes=tuple(notes),
        candidates=tuple(candidates),
        looks_fabricated=looks_fabricated,
    )
