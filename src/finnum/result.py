"""Data types passed across the public API: parsed numbers, per-answer results, gold
records, and the aggregated report.

These are intentionally plain, frozen dataclasses with no third-party dependencies so
the library stays pure-stdlib and the types are trivial to serialize.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, fields
from typing import Literal

from .verdict import Verdict

# Canonical unit tags. "unknown" means we made no unit claim about the number.
Unit = Literal[
    "currency",
    "percent",
    "bps",
    "ratio",
    "shares",
    "per_share",
    "count",
    "unknown",
]

TolKind = Literal["relative", "absolute"]


@dataclass(frozen=True)
class ParsedNumber:
    """One number extracted from free text, normalized to a canonical value.

    ``value`` already has the sign resolved and any magnitude/scale folded in, so the
    classifier can compare it directly. The surface form is retained in ``raw_text`` for
    auditability (e.g. so a reviewer can see we read ``(1.2)`` as ``-1.2``).
    """

    raw_text: str
    span: tuple[int, int]
    value: float
    unit: Unit = "unknown"
    scale: int = 1  # power-of-ten multiplier already folded into ``value`` (audit aid)
    is_negative_paren: bool = False
    is_approximate: bool = False
    is_range: bool = False
    range_value: tuple[float, float] | None = None
    currency: str | None = None
    # Canonical ratio form for percent/bps/ratio numbers (e.g. "12.5%" -> 0.125), used by
    # the unit-confusion check. ``None`` for non-rate numbers.
    as_ratio: float | None = None


@dataclass(frozen=True)
class Result:
    """The verdict and supporting diagnostics for one verified answer."""

    verdict: Verdict
    parsed_value: float | None
    expected: float
    abs_error: float | None = None
    rel_error: float | None = None
    matched_span: tuple[int, int] | None = None
    matched_text: str | None = None
    parsed_unit: Unit | None = None
    expected_unit: Unit | None = None
    tol: float = 0.005
    tol_kind: TolKind = "relative"
    notes: tuple[str, ...] = ()
    candidates: tuple[ParsedNumber, ...] = ()
    looks_fabricated: bool = False

    @property
    def passed(self) -> bool:
        return self.verdict.is_pass

    def to_dict(self) -> dict:
        return {
            "verdict": self.verdict.value,
            "parsed_value": self.parsed_value,
            "expected": self.expected,
            "abs_error": self.abs_error,
            "rel_error": self.rel_error,
            "matched_text": self.matched_text,
            "parsed_unit": self.parsed_unit,
            "expected_unit": self.expected_unit,
            "tol": self.tol,
            "tol_kind": self.tol_kind,
            "notes": list(self.notes),
            "looks_fabricated": self.looks_fabricated,
        }


@dataclass(frozen=True)
class GoldRecord:
    """One gold-standard item: an LLM ``answer_text`` to check against ``truth``."""

    id: str
    answer_text: str
    truth: float
    unit: Unit = "unknown"
    scale_hint: int | None = None  # e.g. 1_000_000 when the source table is "in millions"
    tol: float | None = None  # per-record override of the run default
    tol_kind: TolKind | None = None
    question: str | None = None
    source: str | None = None  # provenance, e.g. "AAPL 10-K FY2023 (CIK 0000320193)"
    meta: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict) -> GoldRecord:
        """Build a record from a plain dict (e.g. a JSONL line), routing unknown keys
        into ``meta`` rather than raising."""
        known = {f.name for f in fields(cls)}
        kwargs = {k: v for k, v in d.items() if k in known}
        extra = {k: v for k, v in d.items() if k not in known}
        if extra:
            merged = dict(kwargs.get("meta") or {})
            merged.update(extra)
            kwargs["meta"] = merged
        return cls(**kwargs)


@dataclass(frozen=True)
class CategoryStat:
    verdict: Verdict
    count: int
    pct: float


@dataclass(frozen=True)
class Report:
    """Aggregated outcome of running a gold set."""

    total: int
    passed: int
    pass_rate: float
    by_verdict: tuple[CategoryStat, ...]
    results: tuple[Result, ...]
    record_ids: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "passed": self.passed,
            "pass_rate": self.pass_rate,
            "by_verdict": {cs.verdict.value: cs.count for cs in self.by_verdict},
            "results": [
                {"id": rid, **r.to_dict()}
                for rid, r in zip(self.record_ids, self.results, strict=True)
            ],
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def to_table(self) -> str:
        # Imported lazily to keep the data module free of formatting concerns.
        from .report import format_table

        return format_table(self)
