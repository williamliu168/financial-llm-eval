# Known limitations (honest negatives)

These are cases `finnum` v0.1 **cannot resolve correctly**, kept deliberately as standing
regression tests rather than hidden. A good evaluator should be candid about where it
fails; these run on every CI build (as `xfail`) in
[`tests/test_honest_negatives.py`](tests/test_honest_negatives.py), and if a future change
fixes one, the strict-xfail turns the surprise pass into a CI failure so the limitation is
consciously retired rather than silently "fixed."

| # | Case | Example | Current verdict | Ideal | Why it's hard / mitigation |
|---|------|---------|-----------------|-------|----------------------------|
| 1 | Locale decimal comma | `"1.234,56"` (meaning 1234.56) | MISMATCH | EXACT | European `1.234,56` is ambiguous against US thousands separators. v0.1 assumes US/UK formatting. |
| 2 | Bare number missing scale | `"Net income of 3.4"` vs 3,400,000 | MISMATCH | pass (scale) | A bare `3.4` with no magnitude word carries no scale. Pass `scale_hint=1_000_000` (e.g. an "in millions" table) to resolve it. |
| 3 | Accounting-parenthesis range | `"$(1.2)-(1.4)B"` vs -1.3e9 | MISMATCH | pass (range) | Ranges accept `-` signs (`-$1.2 to -$1.4B`) but not parentheses, so the two sides parse separately and the first loses the shared `B`. |
| 4 | `closest` masks fabrication | `"Revenue was $1.2B, though some put it near $1.0B"` vs $1.0B | EXACT | flag wrong primary claim | The forgiving default picks the coincidentally-correct secondary number. Use `select="first"` or `select="only"` to judge the primary claim. |
| 5 | Scale gap beyond 10⁴ | `"$383 thousand"` vs $383B | MISMATCH | SCALE_ERROR | Scale detection caps at 10⁴ to avoid excusing wild errors, so a thousand-vs-billion (10⁶) gap reads as a plain mismatch. |

Two of these (2 and 4) have first-class mitigations already in the API (`scale_hint`,
`select`). The rest are genuine v0.1 gaps, named here on purpose.

**Retired:** "mixed units in one clause" (`"improved 250 bps to 12.5%"`, formerly #3) was
fixed in 0.1.2: a range whose two sides carry different units, or a change phrased
"from X to Y", is no longer merged into one range. See `tests/test_range_coherence.py`.
