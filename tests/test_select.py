"""Candidate-selection strategies when an answer states several numbers."""

import pytest

from finnum import Verdict, verify

TWO = "Revenue was $1.2B; the prior year was $1.0B"


def test_closest_picks_nearest_to_truth():
    r = verify(TWO, 1_000_000_000, select="closest")
    assert r.matched_text == "$1.0B"
    assert r.verdict == Verdict.EXACT


def test_first_and_last():
    assert verify(TWO, 1_000_000_000, select="first").matched_text == "$1.2B"
    assert verify(TWO, 1_000_000_000, select="last").matched_text == "$1.0B"


def test_only_requires_exactly_one_number():
    assert verify(TWO, 1_000_000_000, select="only").verdict == Verdict.MISSING
    assert verify("Revenue was $1.0B", 1_000_000_000, select="only").verdict == Verdict.EXACT


def test_target_hint_overrides_value_proximity():
    text = "Net income was $5B; revenue was $1.2B"
    # 999 is far from both; the hint must drive the choice, not closeness.
    r = verify(text, 999, target_hint="revenue")
    assert r.matched_text == "$1.2B"


def test_best_verdict_prefers_the_strongest_match():
    r = verify("1,000,000,000 or 1,200,000,000", 1_200_000_000, select="best_verdict")
    assert r.verdict == Verdict.EXACT
    assert r.parsed_value == pytest.approx(1_200_000_000)


def test_unknown_strategy_raises():
    with pytest.raises(ValueError):
        verify("$1B", 1_000_000_000, select="nonsense")
