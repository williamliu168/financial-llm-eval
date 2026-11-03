# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-11-03

### Changed
- Dev tooling: pin `ruff>=0.17,<0.18`. `ruff>=0.4` installed whatever was newest, and ruff 0.17
  started formatting Markdown code blocks, so a new release could break `ruff format --check`
  without any code change.

### Fixed
- Parser no longer merges two different quantities into one range. `"grew 2% to $391.04
  billion"` was read as a percent-tagged range (2e9, 391.04e9) whose span bracketed, and so
  passed, any truth between them. A range is now rejected when its sides carry different
  units (`%` vs `$`, `bps` vs `%`), when a rate unit sits only on the first value, when a
  currency symbol sits only on the second value, or when it is a change phrased
  "from X to Y" ("ranges from X to Y" is still a range). Retires known limitation #3.
- Ranges accept signed endpoints (`-$1.2 to -$1.4B`, `-5% to -3%`).
- A sign must touch what it negates: `"Revenue - $5B"` (a spaced dash) was read as
  -5e9; `-$5B` and `$-5B` are still negative.
- Digits inside identifiers are no longer extracted as numbers: `FY2024`, `Q3`, `1Q24`,
  `Form 10-K`, `COVID-19`, `3-for-1`, `Item 7A`. They produced false passes under the
  default `closest` selection (`"Per its Form 10-K, EPS was $6.80"` vs a truth of 10 was
  EXACT) and made `select="only"`/`"first"` unusable on answers that cite a filing.
- A "(in millions)" scale header must start at a word boundary ("within millions" no
  longer scales every bare number by 1e6).
- `finnum demo`/`run`/`verify` no longer crash with `UnicodeEncodeError` when stdout is
  redirected on Windows (cp1252); unencodable characters are replaced.
- README: the install line pointed at an unpublished PyPI name; two 60-second-example
  comments stated the wrong verdict (`about $1.2B` vs 1.2e9 is EXACT; `$(1.2)B` vs a
  *negative* truth is EXACT, not SIGN_ERROR). README code block reformatted for
  `ruff format --check .` (ruff 0.17 formats Markdown code blocks).
- Type annotations: `run_gold_set(tol_kind=...)` is `TolKind`; mypy is clean.

### Added
- A loss stated in words carries the sign, like accounting parentheses: `"net loss of $1.2
  billion"`, `"diluted loss per share was $0.56"`, `"negative $88.5 billion"` parse as
  negative (amounts only; never rates, never on top of an explicit sign). Previously a
  correct answer for a loss-making company was a SIGN_ERROR. `ParsedNumber.sign_from_words`
  records it, and a SIGN_ERROR carries a note when the sign came from wording.
- Calendar dates (`September 28, 2024`, `Sept. 28, 2024`, `28 September 2024`,
  `2024-09-28`, `9/28/2024`) are masked before extraction, so an answer that echoes the
  period ("for the fiscal year ended September 28, 2024") still works with
  `select="only"`/`"first"`, the mitigation recommended for known limitation #4.

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
