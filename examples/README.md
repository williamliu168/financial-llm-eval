# Examples

Everything here runs offline with no API key.

## Python quickstart

```bash
python examples/quickstart.py
```

Verifies a handful of answers and prints the verdict for each.

## CLI

Run the bundled public-domain EDGAR demo gold set:

```bash
finnum demo
```

Run your own answers (one JSON record per line — see `demo_answers.jsonl`):

```bash
finnum run examples/demo_answers.jsonl
finnum run examples/demo_answers.jsonl --format json
finnum run examples/demo_answers.jsonl --fail-under 0.95   # exits non-zero in CI if too low
```

Check a single answer:

```bash
finnum verify --answer "Net income was \$3.4M" --truth 3.4e9
# SCALE_ERROR: parsed=3400000.0 expected=3400000000.0 — right digits, wrong magnitude ...
```

> Note: a negative truth in scientific notation must use the `=` form so the shell/argparse
> doesn't read it as a flag — `finnum verify --answer "..." --truth=-1.2e9`.
