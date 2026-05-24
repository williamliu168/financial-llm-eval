"""Thin command-line interface (``finnum``): verify | run | demo."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from . import __version__
from .adapters import load_demo_gold
from .report import format_table
from .result import Report
from .runner import run_gold_set
from .select import SELECT_STRATEGIES
from .verify import verify


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="finnum",
        description="Verify numbers in an LLM's financial answer; diagnose how they're wrong.",
    )
    parser.add_argument("--version", action="version", version=f"finnum {__version__}")
    sub = parser.add_subparsers(dest="command")

    v = sub.add_parser("verify", help="verify a single answer against a truth value")
    v.add_argument("--answer", required=True, help="the LLM answer text")
    v.add_argument("--truth", required=True, type=float, help="the ground-truth value")
    v.add_argument("--unit", default=None, help="expected unit (currency, percent, bps, ...)")
    v.add_argument("--tol", type=float, default=0.005, help="tolerance (default 0.005)")
    v.add_argument("--tol-kind", choices=["relative", "absolute"], default="relative")
    v.add_argument("--scale-hint", type=int, default=None, help="multiplier for bare numbers")
    v.add_argument("--select", choices=SELECT_STRATEGIES, default="closest")
    v.add_argument("--json", action="store_true", help="emit the result as JSON")

    for name, help_text in (
        ("run", "run a JSONL gold set (one record per line)"),
        ("demo", "run the bundled public-domain EDGAR demo gold set"),
    ):
        p = sub.add_parser(name, help=help_text)
        if name == "run":
            p.add_argument("gold", help="path to a JSONL gold set")
        p.add_argument("--tol", type=float, default=0.005)
        p.add_argument("--tol-kind", choices=["relative", "absolute"], default="relative")
        p.add_argument("--select", choices=SELECT_STRATEGIES, default="closest")
        p.add_argument("--format", choices=["table", "json", "jsonl"], default="table")
        p.add_argument("--out", default=None, help="write the report to a file instead of stdout")
        p.add_argument(
            "--fail-under",
            type=float,
            default=None,
            help="exit non-zero if the pass rate is below this fraction (CI gate)",
        )

    f = sub.add_parser("fetch-finqa", help="download a FinQA split (MIT-licensed; not bundled)")
    f.add_argument("--split", choices=["train", "dev", "test"], default="dev")
    f.add_argument("--dest", default=".finqa_data", help="download directory (keep gitignored)")
    return parser


def _read_jsonl(path: str) -> list[dict]:
    records = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def _render(report: Report, fmt: str) -> str:
    if fmt == "json":
        return report.to_json()
    if fmt == "jsonl":
        return "\n".join(
            json.dumps({"id": rid, **res.to_dict()})
            for rid, res in zip(report.record_ids, report.results, strict=True)
        )
    return format_table(report)


def _cmd_verify(args: argparse.Namespace) -> int:
    result = verify(
        args.answer,
        args.truth,
        unit=args.unit,
        tol=args.tol,
        tol_kind=args.tol_kind,
        scale_hint=args.scale_hint,
        select=args.select,
    )
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        note = f" — {result.notes[0]}" if result.notes else ""
        print(
            f"{result.verdict.value}: parsed={result.parsed_value} expected={result.expected}{note}"
        )
    return 0 if result.passed else 1


def _cmd_run(args: argparse.Namespace, records: list[dict]) -> int:
    report = run_gold_set(records, tol=args.tol, tol_kind=args.tol_kind, select=args.select)
    rendered = _render(report, args.format)
    if args.out:
        Path(args.out).write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    if args.fail_under is not None and report.pass_rate < args.fail_under:
        print(
            f"pass rate {report.pass_rate:.1%} is below --fail-under {args.fail_under:.1%}",
            file=sys.stderr,
        )
        return 1
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "verify":
        return _cmd_verify(args)
    if args.command == "run":
        return _cmd_run(args, _read_jsonl(args.gold))
    if args.command == "demo":
        return _cmd_run(args, list(load_demo_gold()))
    if args.command == "fetch-finqa":  # pragma: no cover - network I/O
        from .adapters import download_finqa

        path = download_finqa(args.split, args.dest)
        print(f"FinQA '{args.split}' available at {path}")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
