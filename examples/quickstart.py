"""finnum 60-second quickstart — runs offline, no API key.

python examples/quickstart.py
"""

from finnum import Verdict, verify

EXAMPLES = [
    ("Apple's revenue was about $1.2B", 1_200_000_000, "currency"),
    ("Net income was $3.4M", 3_400_000_000, "currency"),  # scale slip: M vs B
    ("The loss was $(1.2)B", -1_200_000_000, "currency"),  # accounting parentheses
    ("Margins widened 250 bps", 0.025, "ratio"),  # bps reported where a ratio was expected
    ("Gross margin was 44.1%", 44.13, "percent"),  # rounded to one decimal
]

for answer, truth, unit in EXAMPLES:
    result = verify(answer, truth, unit=unit)
    note = f"  ({result.notes[0]})" if result.notes else ""
    flag = "PASS" if result.passed else "FAIL"
    print(f"[{flag}] {result.verdict.value:<16} {answer!r}{note}")

assert verify("Revenue was $1.2B", 1_200_000_000).verdict is Verdict.EXACT
