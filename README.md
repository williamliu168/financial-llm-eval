# financial-llm-eval

> **Verify the numbers in an LLM's financial answer — and diagnose *how* they're wrong.**

`finnum` is a small, dependency-free Python library that checks whether the numbers an
LLM produces over financial text are *correct*, and — when they aren't — classifies the
failure: a scale slip (`$3.4M` vs `$3.4B`), a sign flip (`(1.2)` read as positive), a
unit mix-up (`250 bps` vs `2.5%`), a rounding difference, or a genuine mismatch.

General-purpose eval frameworks tell you an answer is "semantically similar." They do not
know that `$3.4M` and `$3.4B` are a thousandfold apart, that parentheses mean negative in
financial statements, or that 250 basis points is 2.5%, not 250. `finnum` is the
deterministic, finance-aware numeric layer that sits underneath them.

> **Status:** early development. The API and CLI are taking shape milestone by milestone;
> see [`CHANGELOG.md`](./CHANGELOG.md).

## Why this exists

- **Deterministic where numbers matter.** Numeric correctness is checked with arithmetic,
  not a language model — no API key, no nondeterminism, runs offline in CI.
- **Diagnosis, not just a score.** Every result is one of eight verdicts that tells you
  *how* the number is wrong, so you can act on it.
- **Honest about its limits.** Cases the checker cannot resolve are kept as standing,
  visible regression tests rather than hidden (see `KNOWN_LIMITATIONS.md`).

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
# Verdict.SCALE_ERROR  — right digits, wrong magnitude (M vs B)

verify("The loss was $(1.2)B", truth=-1_200_000_000).verdict
# Verdict.SIGN_ERROR  — accounting parentheses mean negative
```

## License

MIT — see [`LICENSE`](./LICENSE).
