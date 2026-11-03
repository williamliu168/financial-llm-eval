"""Run :func:`verify` across a gold set and aggregate the verdicts into a Report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from .result import CategoryStat, GoldRecord, Report, TolKind
from .verdict import Verdict
from .verify import verify


def run_gold_set(
    records: Iterable[GoldRecord | dict],
    *,
    tol: float = 0.005,
    tol_kind: TolKind = "relative",
    select: str = "closest",
) -> Report:
    """Verify every record and return an aggregated :class:`Report`.

    Accepts typed :class:`GoldRecord` objects or plain dicts (e.g. parsed JSONL lines).
    Per-record ``tol`` / ``tol_kind`` / ``scale_hint`` overrides take precedence over the
    run-wide defaults.
    """
    recs = [r if isinstance(r, GoldRecord) else GoldRecord.from_dict(r) for r in records]

    results = tuple(
        verify(
            r.answer_text,
            r.truth,
            unit=r.unit,
            tol=r.tol if r.tol is not None else tol,
            tol_kind=r.tol_kind if r.tol_kind is not None else tol_kind,
            scale_hint=r.scale_hint,
            select=select,
        )
        for r in recs
    )

    total = len(results)
    passed = sum(1 for r in results if r.passed)
    pass_rate = passed / total if total else 0.0

    counts = Counter(r.verdict for r in results)
    by_verdict = tuple(
        CategoryStat(verdict=v, count=counts[v], pct=counts[v] / total if total else 0.0)
        for v in Verdict
        if counts[v]
    )

    return Report(
        total=total,
        passed=passed,
        pass_rate=pass_rate,
        by_verdict=by_verdict,
        results=results,
        record_ids=tuple(r.id for r in recs),
    )
