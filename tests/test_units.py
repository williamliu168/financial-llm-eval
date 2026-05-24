"""Tests for unit tagging and the canonical ``as_ratio`` of rate-like numbers."""

import pytest

from finnum import find_numbers


def only(text):
    found = find_numbers(text)
    assert len(found) == 1, f"expected one number in {text!r}, got {found}"
    return found[0]


@pytest.mark.parametrize("text", ["12.5%", "12.5 percent", "12.5 pct"])
def test_percent_unit_and_ratio(text):
    p = only(text)
    assert p.unit == "percent"
    assert p.value == pytest.approx(12.5)
    assert p.as_ratio == pytest.approx(0.125)


@pytest.mark.parametrize("text", ["250 bps", "250bps", "250 bp", "250 basis points"])
def test_bps_unit_and_ratio(text):
    p = only(text)
    assert p.unit == "bps"
    assert p.value == pytest.approx(250.0)
    assert p.as_ratio == pytest.approx(0.025)


def test_currency_unit_has_no_ratio():
    p = only("$1.2B")
    assert p.unit == "currency"
    assert p.as_ratio is None


def test_bare_number_unit_is_unknown():
    p = only("1234")
    assert p.unit == "unknown"
    assert p.as_ratio is None


def test_percent_range_carries_ratio_midpoint():
    p = only("12% to 14%")
    assert p.unit == "percent"
    assert p.value == pytest.approx(13.0)
    assert p.as_ratio == pytest.approx(0.13)
