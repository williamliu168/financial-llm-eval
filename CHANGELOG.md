# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Parser no longer merges two different quantities into one range. `"grew 2% to $391.04
  billion"` was read as a percent-tagged range (2e9, 391.04e9) whose span bracketed, and so
  passed, any truth between them. A range is now rejected when its sides carry different
  units (`%` vs `$`, `bps` vs `%`), when a rate unit sits only on the first value, when a
  currency symbol sits only on the second value, or when it is a change phrased
  "from X to Y" ("ranges from X to Y" is still a range). Retires known limitation #3.
- Ranges accept signed endpoints (`-$1.2 to -$1.4B`, `-5% to -3%`).

## [0.1.1] - 2026-05-24

### Added
- FinQA adapter: `load_finqa()` maps the MIT-licensed FinQA benchmark into `GoldRecord`s
  (skipping non-numeric rows), `download_finqa()` fetches a split on demand (data not
  bundled), `attach_answers()` attaches model outputs, and `finnum fetch-finqa` exposes
  the downloader. Documents FinQA's table-units convention.

## [0.1.0] - 2026-05-24

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
- Honest-negatives regression suite: 5 documented cases finnum cannot yet resolve, kept
  as standing `xfail(strict)` tests that run in CI, plus `KNOWN_LIMITATIONS.md`.
- Full README: value proposition, the gap vs general-purpose eval tools, the 8-verdict
  taxonomy, demo results, CI usage, and the honest-limitations section.
