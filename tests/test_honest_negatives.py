"""Honest negatives — cases finnum cannot yet resolve, kept as standing regressions.

Each case has two tests:

1. ``test_current_behavior_is_locked`` pins what finnum does *today*, so the behavior
   can't drift silently.
2. ``test_ideal_behavior_not_yet_achieved`` asserts what we *wish* it did, marked
   ``xfail(strict=True)``. These run on every CI build and show up as expected failures —
   visible, not hidden. If a future change makes one start passing, ``strict`` turns the
   surprise pass into a CI failure, forcing us to consciously promote it out of this list.

See ``KNOWN_LIMITATIONS.md`` for the human-readable table.
"""

import pytest

from finnum import Verdict, verify

# (id, answer, truth, kwargs, ideal_passed, current_verdict)
KNOWN_LIMITATIONS = [
    (
        "locale_decimal_comma",
        "The value was 1.234,56",
        1234.56,
        {},
        True,
        Verdict.MISMATCH,
    ),
    (
        "bare_number_missing_scale",
        "Net income of 3.4",
        3_400_000.0,
        {},
        True,
        Verdict.MISMATCH,
    ),
    (
        "mixed_units_one_sentence",
        "Margin improved 250 bps to 12.5%",
        0.125,
        {},
        True,
        Verdict.SCALE_ERROR,
    ),
    (
        "closest_masks_fabrication",
        "Revenue was $1.2B, though some put it near $1.0B",
        1_000_000_000.0,
        {},
        False,
        Verdict.EXACT,
    ),
    (
        "scale_gap_beyond_1e4",
        "Revenue was $383 thousand",
        383_000_000_000.0,
        {},
        True,
        Verdict.MISMATCH,
    ),
]

_IDS = [case[0] for case in KNOWN_LIMITATIONS]


@pytest.mark.parametrize("case", KNOWN_LIMITATIONS, ids=_IDS)
def test_current_behavior_is_locked(case):
    _id, answer, truth, kwargs, _ideal_passed, current_verdict = case
    assert verify(answer, truth, **kwargs).verdict == current_verdict


@pytest.mark.xfail(strict=True, reason="documented known limitation; see KNOWN_LIMITATIONS.md")
@pytest.mark.parametrize("case", KNOWN_LIMITATIONS, ids=_IDS)
def test_ideal_behavior_not_yet_achieved(case):
    _id, answer, truth, kwargs, ideal_passed, _current_verdict = case
    # The behavior we want but cannot yet deliver. This assertion is expected to FAIL
    # today; strict xfail makes any future fix announce itself as an XPASS.
    assert verify(answer, truth, **kwargs).passed is ideal_passed
