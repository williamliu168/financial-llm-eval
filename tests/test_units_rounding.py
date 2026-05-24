"""Verdict-level tests for UNIT_CONFUSION and ROUNDING (Milestone D)."""

from finnum import Verdict, verify


class TestUnitConfusion:
    def test_bps_reported_as_ratio(self):
        r = verify("Margins widened 250 bps", 0.025)
        assert r.verdict == Verdict.UNIT_CONFUSION
        assert any("bps→ratio" in n for n in r.notes)

    def test_bps_reported_as_percent(self):
        r = verify("Margins widened 250 bps", 2.5)
        assert r.verdict == Verdict.UNIT_CONFUSION
        assert any("bps→percent" in n for n in r.notes)

    def test_percent_reported_as_ratio(self):
        r = verify("Operating margin was 12.5%", 0.125)
        assert r.verdict == Verdict.UNIT_CONFUSION
        assert any("percent→ratio" in n for n in r.notes)

    def test_bare_number_against_ratio_expectation(self):
        # expected_unit drives the rate interpretation for an untagged number.
        r = verify("Operating margin was 12.5", 0.125, unit="ratio")
        assert r.verdict == Verdict.UNIT_CONFUSION

    def test_correct_percent_is_exact_not_confusion(self):
        assert verify("Operating margin was 12.5%", 12.5).verdict == Verdict.EXACT


class TestRounding:
    def test_rounding_within_tolerance_is_labeled_rounding(self):
        r = verify("Revenue was $3.14B", 3_141_590_000, tol=0.005)
        assert r.verdict == Verdict.ROUNDING
        assert r.passed  # ROUNDING counts as a pass

    def test_rounding_just_outside_tolerance(self):
        r = verify("The ratio was 3.1", 3.14, tol=0.001)
        assert r.verdict == Verdict.ROUNDING

    def test_incorrectly_rounded_value_is_a_mismatch(self):
        # 3.2 is not a correct rounding of 3.14 at one decimal place.
        r = verify("The ratio was 3.2", 3.14, tol=0.001)
        assert r.verdict == Verdict.MISMATCH

    def test_coarse_whole_number_is_not_excused_as_rounding(self):
        # "$3B" for $3.14B (4.5% off, no decimals reported) must not pass as ROUNDING.
        r = verify("Revenue was $3B", 3_140_000_000, tol=0.005)
        assert r.verdict != Verdict.ROUNDING
        assert not r.passed
