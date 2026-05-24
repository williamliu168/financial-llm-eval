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
