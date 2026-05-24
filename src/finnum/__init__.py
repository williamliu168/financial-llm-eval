"""finnum — finance-aware numeric verification & error diagnosis for LLM outputs.

Verify the numbers in an LLM's financial answer against ground truth, and diagnose
*how* a number is wrong (scale, sign, unit, rounding, ...) rather than just pass/fail.
"""

from __future__ import annotations

from ._version import __version__
from .result import CategoryStat, GoldRecord, ParsedNumber, Report, Result, Unit
from .verdict import FABRICATED, Verdict
from .verify import verify

__all__ = [
    "__version__",
    "Verdict",
    "FABRICATED",
    "ParsedNumber",
    "Result",
    "GoldRecord",
    "CategoryStat",
    "Report",
    "Unit",
    "verify",
]
