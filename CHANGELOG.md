# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Project scaffold: `src` layout, packaging (`pyproject.toml`, hatchling), MIT license,
  CI (ruff + pytest on Python 3.10–3.12).
- `Verdict` taxonomy and the core dataclasses (`ParsedNumber`, `Result`, `GoldRecord`,
  `Report`).
- `verify()` public entry point (stub; full pipeline in progress).
- `find_numbers()` finance-aware number/unit parser: magnitudes (K/M/MM/B/bn/T),
  currency symbols, accounting-parenthesis negatives, percent/bps with canonical ratios,
  ranges, approximation markers, thousands separators, and "(in millions)" scale headers.
  Public conventions documented in `PARSING_REFERENCES.md`.
- `verify()` pipeline: extract → select → classify. Verdicts EXACT, WITHIN_TOLERANCE,
  SCALE_ERROR, SIGN_ERROR, MISSING, MISMATCH (ROUNDING and UNIT_CONFUSION arrive next),
  with a fixed precedence (sign before scale; compound errors stay MISMATCH) and a
  `looks_fabricated` flag. Selection strategies: closest, first, last, only, best_verdict,
  plus `target_hint`. Default tolerance 0.5% relative.
- ROUNDING and UNIT_CONFUSION verdicts. Rounding is detected in the number's surface form
  (scale removed); a coarse whole-number answer is not excused. Unit confusion covers
  percent ↔ ratio ↔ bps and is checked before scale for rate-tagged numbers (their
  confusions are factors of ten). All eight verdicts are now live.
- `run_gold_set()` + `Report` aggregation, and a plain-text results table.
- CLI subcommands `finnum verify | run | demo`, with `--fail-under` as a CI gate and
  `--format table|json|jsonl`.
- Bundled, public-domain EDGAR demo gold set (24 records from real 10-K figures, cited per
  record) exercising all eight verdicts; `finnum demo` runs it offline.
- Parser now reads a leading sign before a currency symbol (e.g. `-$88.5B`).
- `examples/` with a runnable quickstart and a sample JSONL gold set.
