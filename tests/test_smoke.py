"""Smoke tests — the package imports and the public surface is wired."""

import finnum
from finnum import Verdict


def test_version_is_a_nonempty_string():
    assert isinstance(finnum.__version__, str)
    assert finnum.__version__


def test_verdict_pass_semantics():
    assert Verdict.EXACT.is_pass
    assert Verdict.WITHIN_TOLERANCE.is_pass
    assert Verdict.ROUNDING.is_pass
    assert not Verdict.MISMATCH.is_pass
    assert not Verdict.MISSING.is_pass


def test_verdict_is_str_comparable():
    assert Verdict.EXACT == "EXACT"


def test_verify_is_callable_and_returns_result():
    result = finnum.verify("no number in this sentence", truth=1.0)
    # Milestone A stub: nothing parsed yet.
    assert result.verdict == Verdict.MISSING
    assert result.expected == 1.0
    assert result.passed is False
