"""Tests for the number extractor — one assertion cluster per parsing convention."""

import pytest

from finnum import find_numbers


def values(text, **kw):
    return [p.value for p in find_numbers(text, **kw)]


def only(text, **kw):
    found = find_numbers(text, **kw)
    assert len(found) == 1, f"expected exactly one number in {text!r}, got {found}"
    return found[0]


@pytest.mark.parametrize(
    "text,expected",
    [
        ("1234", 1234.0),
        ("1,234,567", 1_234_567.0),
        ("3.14", 3.14),
        (".5", 0.5),
        ("-5.2", -5.2),
        ("+3", 3.0),
    ],
)
def test_plain_numbers(text, expected):
    assert only(text).value == pytest.approx(expected)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("$1.2B", 1.2e9),
        ("$3.4 million", 3.4e6),
        ("500K", 5e5),
        ("2 trillion", 2e12),
        ("3.4MM", 3.4e6),
        ("5bn", 5e9),
        ("1.2 millions", 1.2e6),  # plural tolerated
        ("€3,400", 3400.0),
        ("£5M", 5e6),
    ],
)
def test_magnitude_and_currency(text, expected):
    assert only(text).value == pytest.approx(expected)


def test_currency_is_tagged():
    p = only("$1.2B")
    assert p.unit == "currency"
    assert p.currency == "USD"


@pytest.mark.parametrize(
    "text,expected",
    [
        ("(1,234)", -1234.0),
        ("$(1.2)B", -1.2e9),  # currency outside, magnitude after the paren
        ("($1.2 million)", -1.2e6),  # currency and magnitude inside the paren
        ("(0.5)", -0.5),
    ],
)
def test_accounting_parentheses_are_negative(text, expected):
    p = only(text)
    assert p.value == pytest.approx(expected)
    assert p.is_negative_paren is True


def test_lone_paren_is_not_treated_as_accounting_negative():
    # The "(" belongs to prose, not to the number.
    p = only("(see note 5)")
    assert p.value == 5.0
    assert p.is_negative_paren is False


@pytest.mark.parametrize("marker", ["~", "about", "approximately", "roughly"])
def test_approximation_markers(marker):
    p = only(f"{marker} $1.2B")
    assert p.value == pytest.approx(1.2e9)
    assert p.is_approximate is True


def test_scale_header_applies_to_bare_numbers():
    assert only("amounts in millions: revenue 1,200").value == pytest.approx(1.2e9)


def test_explicit_magnitude_overrides_scale_header():
    # "$3.4B" inside an "in millions" context is taken literally.
    assert only("(in millions) ... total was $3.4B").value == pytest.approx(3.4e9)


def test_scale_hint_param_applies_and_is_overridden_by_explicit_magnitude():
    assert only("revenue 1,200", scale_hint=1_000_000).value == pytest.approx(1.2e9)
    assert only("revenue $3.4B", scale_hint=1_000_000).value == pytest.approx(3.4e9)


def test_multiple_numbers_in_order():
    assert values("5 cats, 3 dogs, and $7M") == [5.0, 3.0, 7e6]


def test_no_numbers():
    assert find_numbers("no numbers in this sentence") == []
    assert find_numbers("") == []


class TestRanges:
    def test_shared_trailing_magnitude(self):
        p = only("$1.2-1.4B")
        assert p.is_range is True
        assert p.range_value == pytest.approx((1.2e9, 1.4e9))
        assert p.value == pytest.approx(1.3e9)  # midpoint

    def test_word_separator(self):
        p = only("1.2 to 1.4 billion")
        assert p.range_value == pytest.approx((1.2e9, 1.4e9))

    def test_range_is_one_number_not_three(self):
        # longest-match: the range must not be split into its endpoints.
        found = find_numbers("guidance of $1.2-1.4B")
        assert len(found) == 1
        assert found[0].is_range is True


def test_spans_point_into_source_text():
    text = "revenue was $1.2B last year"
    p = only(text)
    start, end = p.span
    assert text[start:end].strip() == "$1.2B"


@pytest.mark.parametrize(
    "text",
    [
        "FY2024",
        "Q3",
        "1Q24",
        "Form 10-K",
        "an 8-K filing",
        "COVID-19",
        "a 3-for-1 split",
        "Item 7A",
    ],
)
def test_identifier_digits_are_not_numbers(text):
    assert find_numbers(text) == []


@pytest.mark.parametrize(
    "text,expected",
    [
        ("US$3.4 million", 3.4e6),  # currency glued to a letter is still a quantity
        ("trades at 12.5x earnings", 12.5),  # a multiple is a quantity
        ("$3.4B.", 3.4e9),
        ("2023-2024", 2023.5),  # a bare year range is not an identifier
    ],
)
def test_identifier_guard_keeps_quantities(text, expected):
    assert only(text).value == pytest.approx(expected)


def test_scale_header_needs_a_word_boundary():
    assert only("EPS came within millions of guidance at 6.08").value == pytest.approx(6.08)
