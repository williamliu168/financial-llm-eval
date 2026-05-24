"""Edge cases around the tolerance band."""

import pytest

from finnum import Verdict, verify


def test_boundary_is_inclusive():
    # Exactly 1% off, with a 1% tolerance -> passes (<=).
    r = verify("1010", 1000, tol=0.01)
    assert r.verdict == Verdict.WITHIN_TOLERANCE


def test_just_outside_boundary_fails():
    r = verify("1011", 1000, tol=0.01)
    assert r.verdict != Verdict.WITHIN_TOLERANCE
    assert not r.passed


def test_expected_zero_uses_absolute_fallback():
    assert verify("0", 0.0).verdict == Verdict.EXACT
    assert verify("0.001", 0.0, tol=0.005).verdict == Verdict.WITHIN_TOLERANCE
    assert verify("0.01", 0.0, tol=0.005).verdict != Verdict.WITHIN_TOLERANCE


def test_absolute_tolerance_kind():
    r = verify("105", 100, tol=10, tol_kind="absolute")
    assert r.verdict == Verdict.WITHIN_TOLERANCE
    r2 = verify("115", 100, tol=10, tol_kind="absolute")
    assert r2.verdict != Verdict.WITHIN_TOLERANCE


def test_relative_tolerance_scales_with_magnitude():
    # 0.4% off a billion-dollar figure is within the 0.5% default. The answer carries more
    # precision than the truth, so this is a tolerance pass, not a rounding match.
    r = verify("$1.2048B", 1_200_000_000)
    assert r.verdict == Verdict.WITHIN_TOLERANCE
    assert r.rel_error == pytest.approx(0.004, rel=1e-2)
