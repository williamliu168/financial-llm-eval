"""Choosing which number in an answer to judge, when an answer states several.

The default ``closest`` strategy is forgiving — it gives the model the benefit of the
doubt and surfaces the most informative diagnosis. That can mask a fabricated number when
a coincidentally-close one is also present; use ``only`` or ``first`` when you want to be
strict about fabrication. See the README's "Honest limitations".
"""

from __future__ import annotations

import math

from .result import ParsedNumber

SELECT_STRATEGIES = ("closest", "first", "last", "only", "best_verdict")


def select_candidate(
    candidates: list[ParsedNumber],
    expected: float,
    *,
    strategy: str = "closest",
) -> ParsedNumber | None:
    """Pick one candidate by ``strategy`` (excluding ``best_verdict``, handled in verify)."""
    if not candidates:
        return None
    if strategy == "first":
        return candidates[0]
    if strategy == "last":
        return candidates[-1]
    if strategy == "only":
        # Ambiguous unless the answer states exactly one number.
        return candidates[0] if len(candidates) == 1 else None
    if strategy in ("closest", "best_verdict"):
        # best_verdict is resolved in verify (it needs the classifier); closest is the
        # sensible fallback there too.
        return min(candidates, key=lambda c: (abs(c.value - expected), c.span[0]))
    raise ValueError(f"unknown select strategy: {strategy!r} (choose from {SELECT_STRATEGIES})")


def prefer_by_hint(text: str, candidates: list[ParsedNumber], hint: str) -> ParsedNumber | None:
    """Return the candidate the ``hint`` phrase refers to, or ``None`` if it does not appear.

    A claim reads "``<hint>`` was ``<number>``", so the relevant number is the closest one
    that *follows* an occurrence of the hint. If no candidate follows the hint, fall back
    to the nearest by absolute distance.
    """
    low, hint_low = text.lower(), hint.lower()
    ends, start = [], low.find(hint_low)
    while start != -1:
        ends.append(start + len(hint_low))
        start = low.find(hint_low, start + 1)
    if not ends:
        return None

    def forward_gap(c: ParsedNumber) -> float:
        after = [c.span[0] - end for end in ends if end <= c.span[0]]
        return min(after) if after else math.inf

    best = min(candidates, key=lambda c: (forward_gap(c), c.span[0]))
    if forward_gap(best) == math.inf:
        # Nothing follows the hint; pick the nearest occurrence in either direction.
        return min(candidates, key=lambda c: (min(abs(c.span[0] - e) for e in ends), c.span[0]))
    return best
