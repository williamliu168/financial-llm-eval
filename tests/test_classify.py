"""One assertion cluster per verdict, plus the tricky precedence cases."""

import pytest

from finnum import Verdict, verify


def test_exact():
    r = verify("Revenue was $1.2B", 1_200_000_000)
    assert r.verdict == Verdict.EXACT
    assert r.passed
    assert r.matched_text == "$1.2B"
    assert r.parsed_unit == "currency"


def test_within_tolerance():
    r = verify("Revenue was about $1.205B", 1_200_000_000, tol=0.005)
    assert r.verdict == Verdict.WITHIN_TOLERANCE
    assert r.passed
    assert r.rel_error == pytest.approx(0.004167, rel=1e-3)


def test_scale_error_millions_vs_billions():
    r = verify("Net income was $3.4M", 3_400_000_000)
    assert r.verdict == Verdict.SCALE_ERROR
    assert not r.passed
    assert any("10^3" in n for n in r.notes)


def test_sign_error_plain():
    r = verify("The figure was $1.2B", -1_200_000_000)
    assert r.verdict == Verdict.SIGN_ERROR


def test_sign_error_from_accounting_parentheses():
    r = verify("A loss of $(1.2)B", 1_200_000_000)
    assert r.verdict == Verdict.SIGN_ERROR
    assert any("parenthes" in n for n in r.notes)


def test_missing():
    r = verify("There is no number in this sentence.", 5.0)
    assert r.verdict == Verdict.MISSING
    assert r.parsed_value is None
    assert not r.passed


def test_mismatch_and_fabrication_flag():
    r = verify("Revenue was $5B", 1_200_000_000)
    assert r.verdict == Verdict.MISMATCH
    assert r.looks_fabricated is True


def test_compound_sign_and_scale_is_a_plain_mismatch():
    # Magnitude AND sign both wrong: we do not pretend to diagnose a single cause.
    r = verify("Net income was $3.4M", -3_400_000_000)
    assert r.verdict == Verdict.MISMATCH


class TestRanges:
    def test_truth_inside_range_passes(self):
        r = verify("Guidance of $1.2-1.4B", 1_300_000_000)
        assert r.verdict == Verdict.WITHIN_TOLERANCE
        assert any("within the stated range" in n for n in r.notes)

    def test_truth_outside_range_compares_nearest_endpoint(self):
        r = verify("Guidance of $1.2-1.4B", 3_000_000_000)
        assert r.verdict == Verdict.MISMATCH


def test_candidates_are_recorded_for_transparency():
    r = verify("5 cats, 3 dogs, $7M revenue", 7_000_000)
    assert len(r.candidates) == 3


@pytest.mark.parametrize(
    "answer,truth",
    [
        ("Per its Form 10-K, diluted EPS was $6.80.", 10.0),  # "10" from "10-K"
        ("In Q3 2026, diluted EPS was $1.50.", 3.0),  # "3" from "Q3"
    ],
)
def test_identifier_digits_cannot_produce_a_false_pass(answer, truth):
    assert not verify(answer, truth).passed


def test_strict_selection_survives_citations():
    r = verify(
        "Per the FY2024 Form 10-K, revenue was $391.04 billion", 391_040_000_000, select="only"
    )
    assert r.verdict == Verdict.EXACT
