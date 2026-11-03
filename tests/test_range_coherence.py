"""A range is one quantity's interval. Two different quantities joined by "to", or a
change stated as "from X to Y", must not be merged into a range (which would bracket,
and so falsely pass, any truth in between)."""

import pytest

from finnum import Verdict, find_numbers, verify


def summary(text):
    return [(p.raw_text, p.unit, p.is_range) for p in find_numbers(text)]


@pytest.mark.parametrize(
    "text,expected",
    [
        (
            "Revenue grew 2% to $391.04 billion.",
            [("2%", "percent", False), ("$391.04 billion", "currency", False)],
        ),
        ("EPS rose 3% to $6.08", [("3%", "percent", False), ("$6.08", "currency", False)]),
        (
            "Margin improved 250 bps to 12.5%",
            [("250 bps", "bps", False), ("12.5%", "percent", False)],
        ),
        ("$5M to 10%", [("$5M", "currency", False), ("10%", "percent", False)]),
        ("fell 3% to 1,234 units", [("3%", "percent", False), ("1,234", "unknown", False)]),
        (
            "rose 7 points to $8.2 billion",
            [("7", "unknown", False), ("$8.2 billion", "currency", False)],
        ),
        (
            "rose from $383.3B to $391.0B",
            [("$383.3B", "currency", False), ("$391.0B", "currency", False)],
        ),
        ("up from 2.1% to 2.4%", [("2.1%", "percent", False), ("2.4%", "percent", False)]),
    ],
)
def test_two_quantities_are_not_one_range(text, expected):
    assert summary(text) == expected


@pytest.mark.parametrize(
    "text,lo,hi",
    [
        ("$1.2-1.4B", 1.2e9, 1.4e9),
        ("1.2 to 1.4 billion", 1.2e9, 1.4e9),
        ("$1.2 to $1.4 billion", 1.2e9, 1.4e9),
        ("12% to 14%", 12.0, 14.0),
        ("12 to 14%", 12.0, 14.0),
        ("guidance ranges from $1.2B to $1.4B", 1.2e9, 1.4e9),  # "ranges from" is a range
        ("-$1.2 to -$1.4B", -1.2e9, -1.4e9),  # signed endpoints, shared magnitude
        ("-5% to -3%", -5.0, -3.0),
        ("-1% to 2%", -1.0, 2.0),  # signs are per endpoint, never shared
    ],
)
def test_genuine_ranges_still_parse(text, lo, hi):
    found = find_numbers(text)
    assert len(found) == 1 and found[0].is_range
    assert found[0].range_value == pytest.approx((lo, hi))


def test_rejected_range_rescans_for_a_range_at_the_second_value():
    found = find_numbers("grew 2% to $1.2-1.4B")
    assert [p.raw_text for p in found] == ["2%", "$1.2-1.4B"]
    assert found[1].range_value == pytest.approx((1.2e9, 1.4e9))


@pytest.mark.parametrize(
    "answer,truth",
    [
        ("Revenue grew 2% to $391.04 billion.", 211_915_000_000),  # was WITHIN_TOLERANCE
        ("EPS rose 3% to $6.08", 4.50),  # was WITHIN_TOLERANCE
        ("Revenue rose from $300 billion to $400 billion", 350_000_000_000),
    ],
)
def test_no_false_pass_from_a_merged_range(answer, truth):
    assert not verify(answer, truth).passed


def test_mixed_unit_clause_now_verifies():  # formerly KNOWN_LIMITATIONS #3
    assert verify("Margin improved 250 bps to 12.5%", 12.5, unit="percent").verdict == (
        Verdict.EXACT
    )
    assert verify("Revenue grew 2% to $391.04 billion.", 391_040_000_000).verdict == (Verdict.EXACT)


def test_signed_range_brackets_a_negative_truth():
    assert verify("a loss of -$1.2 to -$1.4B", -1_300_000_000).passed
