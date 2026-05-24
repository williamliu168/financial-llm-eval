"""Public entry point: :func:`verify`.

Milestone A ships a stub that always returns ``MISSING``; the extract -> select ->
classify pipeline lands in Milestone C.
"""

from __future__ import annotations

from .result import Result, TolKind, Unit
from .verdict import Verdict

# one of: closest | first | last | only | best_verdict (validated in Milestone C)
SelectStrategy = str


def verify(
    answer_text: str,
    truth: float,
    *,
    unit: Unit | None = None,
    tol: float = 0.005,
    tol_kind: TolKind = "relative",
    scale_hint: int | None = None,
    select: SelectStrategy = "closest",
    target_hint: str | None = None,
) -> Result:
    """Extract candidate numbers from ``answer_text``, pick the one to judge, and
    classify it against ``truth``.

    Returns a :class:`Result` whose ``verdict`` diagnoses *how* the number is wrong.
    """
    # TODO(Milestone C): wire find_numbers -> select -> classify.
    return Result(
        verdict=Verdict.MISSING,
        parsed_value=None,
        expected=truth,
        expected_unit=unit,
        tol=tol,
        tol_kind=tol_kind,
    )
