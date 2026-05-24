"""Offline tests for the FinQA adapter (no network — uses a committed fixture)."""

from pathlib import Path

from finnum import Verdict, run_gold_set
from finnum.adapters import attach_answers, load_finqa

FIXTURE = Path(__file__).parent / "data" / "finqa_sample.json"


def test_load_finqa_maps_and_skips_non_numeric():
    records = load_finqa(FIXTURE)
    # The "yes" row (non-numeric exe_ans) is skipped.
    assert len(records) == 2
    ids = [r.id for r in records]
    assert ids == ["AAPL/2023/page_30.pdf-1", "MSFT/2023/page_12.pdf-2"]


def test_truth_unit_and_metadata():
    numeric, percent = load_finqa(FIXTURE)
    assert numeric.truth == 11043.0
    assert numeric.unit == "unknown"
    assert numeric.answer_text == ""  # FinQA provides gold, not a model answer
    assert numeric.source == "FinQA"
    assert numeric.meta["program"].startswith("subtract")
    assert percent.truth == 0.069
    assert percent.unit == "percent"


def test_attach_answers_then_run():
    records = load_finqa(FIXTURE)
    answered = attach_answers(
        records,
        {
            # FinQA's exe_ans is in the table's units (millions here), so the answer is
            # compared in the same convention rather than in absolute dollars.
            "AAPL/2023/page_30.pdf-1": "Net sales fell by about 11,043 year over year.",
            "MSFT/2023/page_12.pdf-2": "Revenue grew about 6.9%.",
        },
    )
    report = run_gold_set(answered)
    by_id = dict(zip(report.record_ids, report.results, strict=True))
    assert by_id["AAPL/2023/page_30.pdf-1"].verdict == Verdict.EXACT
    # 6.9% reported where the gold is the ratio 0.069 -> flagged as a unit confusion.
    assert by_id["MSFT/2023/page_12.pdf-2"].verdict == Verdict.UNIT_CONFUSION


def test_attach_answers_leaves_unmatched_unchanged():
    records = load_finqa(FIXTURE)
    result = attach_answers(records, {})
    assert len(result) == 2
    assert all(r.answer_text == "" for r in result)
