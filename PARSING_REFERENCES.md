# Parsing references

`finnum`'s number parser is built entirely from **public conventions** for how numbers
appear in financial prose. This file documents the source of each rule so the parser can
be audited as general knowledge rather than anything domain-proprietary. The parser reads
a number *as written*; it never reconstructs a financial concept, reconciles figures, or
applies any synthesis/normalization beyond surface canonicalization.

| Rule | Convention | Public basis |
|---|---|---|
| Parentheses denote a negative, e.g. `(1.2)` = `-1.2` | Standard financial-statement presentation | US GAAP / SEC filing presentation norms; visible in any public 10-K balance sheet |
| `(in thousands)` / `$ in millions` scale headers | Statement column headers declaring the reporting scale | US GAAP / SEC filing presentation norms |
| Magnitude words/abbreviations: `K`, `M`, `MM`, `mn`, `B`, `bn`, `T`, thousand/million/billion/trillion | Common English and finance shorthand for orders of magnitude | General usage; `MM`/`mn` = million and `bn` = billion are conventional finance abbreviations |
| Currency symbols `$ € £ ¥` → ISO codes (tag only) | Currency identification | ISO 4217; Unicode "Currency Symbols" block. No FX conversion is performed. |
| Basis points: `1 bp = 0.01% = 0.0001` | Rate convention | Standard financial definition of a basis point |
| Percent ↔ ratio: `12.5% = 0.125` | Arithmetic definition of percent | General mathematics |
| Thousands separators (`1,234,567`) and decimal point | US/UK number formatting | CLDR / common number formatting |
| Ranges (`$1.2–1.4B`, `1.2 to 1.4 billion`) | Guidance/estimate phrasing; a range is one quantity, so `2% to $391B` and `from $383B to $391B` are two numbers | General usage |
| "Net loss of $1.2B" = -1.2B; "negative $88.5B" = -88.5B | Wording that carries the sign of an amount | US GAAP captions ("Net income (loss)", "Net loss per share"); visible in any 10-K income statement |
| Approximation markers (`~`, "about", "approximately") | Estimate phrasing | General usage |

## Acknowledged limitation (kept as an honest negative, not silently mis-parsed)

- **Locale decimal commas** (e.g. European `1.234,56`) are ambiguous against US thousands
  separators. v0.1 assumes US/UK conventions; the European form is a documented known
  limitation rather than a best-effort guess. See `KNOWN_LIMITATIONS.md`.
