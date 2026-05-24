# financial-llm-eval

> **Verify the numbers in an LLM's financial answer — and diagnose *how* they're wrong.**

[![CI](https://github.com/invest-composer-william/financial-llm-eval/actions/workflows/ci.yml/badge.svg)](https://github.com/invest-composer-william/financial-llm-eval/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)

`finnum` is a small, **dependency-free** Python library that checks whether the numbers an
LLM produces over financial text are *correct*, and — when they aren't — classifies the
failure: a scale slip (`$3.4M` vs `$3.4B`), a sign flip (`(1.2)` read as positive), a unit
mix-up (`250 bps` vs `2.5%`), a rounding difference, or a genuine mismatch.

## The gap this fills

General-purpose eval frameworks tell you an answer is *semantically similar*. They do not
know that `$3.4M` and `$3.4B` are a thousandfold apart, that parentheses mean negative in
financial statements, or that 250 basis points is 2.5%, not 250. `finnum` is the
deterministic, finance-aware numeric layer that sits **underneath** those tools.

| | Numeric correctness | Scale / sign / unit diagnosis | Finance-aware parsing | Needs an LLM/API key |
|---|:---:|:---:|:---:|:---:|
| Ragas · DeepEval · promptfoo · OpenAI Evals | partial (string / semantic) | ✗ | ✗ | often |
| **finnum** | ✓ deterministic | ✓ 8-verdict taxonomy | ✓ | **no** |

Numeric correctness is checked with arithmetic, not a language model — so it runs offline,
in CI, with no API key and no nondeterminism.

## Install

```bash
pip install financial-llm-eval   # import as: finnum
```

## 60-second example

```python
from finnum import verify

verify("Apple's revenue was about $1.2B", truth=1_200_000_000, unit="currency").verdict
# Verdict.WITHIN_TOLERANCE

verify("Net income was $3.4M", truth=3_400_000_000).verdict
# Verdict.SCALE_ERROR   — right digits, wrong magnitude (M vs B)

verify("The loss was $(1.2)B", truth=-1_200_000_000).verdict
# Verdict.SIGN_ERROR    — accounting parentheses mean negative

verify("Margins widened 250 bps", truth=0.025, unit="ratio").verdict
# Verdict.UNIT_CONFUSION — 250 bps reported where a ratio was expected
```

Or from the command line, on the bundled public-domain EDGAR demo set:

```bash
finnum demo
```

## The eight verdicts

`verify()` returns a `Result` whose `verdict` says *how* the number relates to the truth:

| Verdict | Meaning | Example (answer → truth) |
|---|---|---|
| `EXACT` | equal at the precision given | `$383.285B` → 383,285,000,000 |
| `WITHIN_TOLERANCE` | inside the tolerance band (default 0.5%) | `$416.0B` → 416,161,000,000 |
| `ROUNDING` | correctly rounded to fewer digits | `$211.9B` → 211,915,000,000 |
| `SCALE_ERROR` | right digits, wrong magnitude | `$3.4M` → 3,400,000,000 |
| `SIGN_ERROR` | magnitude right, sign flipped | `$(1.2)B` → 1,200,000,000 |
| `UNIT_CONFUSION` | related-unit mix-up (bps ↔ % ↔ ratio) | `4413 bps` → 44.13 (%) |
| `MISSING` | no parseable number in the answer | `"revenue grew"` → 5,000,000,000 |
| `MISMATCH` | a number is present but genuinely wrong | `$450B` → 211,915,000,000 |

`Result.passed` is true for `EXACT`, `WITHIN_TOLERANCE`, and `ROUNDING`. A `MISMATCH` far
outside tolerance and unexplained by the other categories also sets `looks_fabricated`.

## Results on the bundled demo set

`finnum demo` runs 24 records built from real Apple and Microsoft 10-K figures (FY2023–2025,
each citing its filing) with synthetic answers chosen to exercise every verdict:

```
TOTAL 24  |  pass 10 (42%)  |  EXACT=4  WITHIN_TOLERANCE=3  ROUNDING=3
          SCALE_ERROR=3  SIGN_ERROR=3  UNIT_CONFUSION=3  MISSING=2  MISMATCH=3
```

The point isn't the pass rate — it's that each wrong answer is *diagnosed*, not just
failed.

## Use it in CI

`finnum run` reads a JSONL gold set (one `{"id", "answer_text", "truth", "unit"}` per line)
and exits non-zero when the pass rate drops below a threshold:

```bash
finnum run my_model_outputs.jsonl --fail-under 0.95
```

## How it works

Three deterministic steps: **extract** every number from the answer (magnitudes, currency,
accounting parentheses, percent/bps, ranges — all from public conventions, documented in
[`PARSING_REFERENCES.md`](PARSING_REFERENCES.md)); **select** the one to judge; and
**classify** it against the truth with a fixed verdict precedence. No model is called.

> Deterministic where numbers matter — and a clean place to bolt on an LLM judge for the
> *qualitative* claims that genuinely need one (a documented v0.2 extension point).

## Honest limitations

A benchmark that only produces good news isn't a benchmark. `finnum` ships **5 documented
cases it cannot yet resolve** (locale decimal commas, bare numbers missing their scale,
mixed units in one clause, and more) as standing `xfail` regressions that run in CI — see
[`KNOWN_LIMITATIONS.md`](KNOWN_LIMITATIONS.md). Two of them have first-class mitigations
already (`scale_hint`, `select=`).

## Data & license

The bundled gold set is transcribed from public-domain SEC EDGAR filings (cited per record).
`finnum` is MIT-licensed — see [`LICENSE`](LICENSE). Built only from public conventions; no
proprietary data or third-party runtime dependencies.
