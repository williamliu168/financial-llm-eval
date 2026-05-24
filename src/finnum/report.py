"""Plain-text rendering of a :class:`Report` — no third-party dependencies."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .result import Report


def _human(value: float | None) -> str:
    """Compact human-readable number, e.g. 383285000000 -> '383.3B', 44.13 -> '44.13'."""
    if value is None:
        return "—"
    magnitude = abs(value)
    for suffix, scale in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if magnitude >= scale:
            return f"{value / scale:.4g}{suffix}"
    return f"{value:.4g}"


def _pct(value: float | None) -> str:
    return "—" if value is None else f"{value * 100:.2f}%"


def format_table(report: Report) -> str:
    """Render per-record verdicts plus a summary footer as a monospace table."""
    headers = ("id", "verdict", "parsed", "expected", "rel_err", "notes")
    rows = []
    for rid, result in zip(report.record_ids, report.results, strict=True):
        rows.append(
            (
                rid,
                result.verdict.value,
                _human(result.parsed_value),
                _human(result.expected),
                _pct(result.rel_error),
                result.notes[0] if result.notes else "",
            )
        )

    widths = [
        max(len(headers[i]), *(len(row[i]) for row in rows)) if rows else len(headers[i])
        for i in range(len(headers))
    ]

    def fmt(cells: tuple[str, ...]) -> str:
        return "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(cells)).rstrip()

    lines = [fmt(headers), "  ".join("-" * w for w in widths)]
    lines.extend(fmt(row) for row in rows)

    breakdown = "  ".join(f"{cs.verdict.value}={cs.count}" for cs in report.by_verdict)
    lines.append("-" * len(lines[1]))
    lines.append(
        f"TOTAL {report.total}  |  pass {report.passed} "
        f"({report.pass_rate * 100:.0f}%)  |  {breakdown}"
    )
    return "\n".join(lines)
