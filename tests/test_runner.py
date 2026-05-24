"""Tests for run_gold_set aggregation and Report serialization."""

import json

from finnum import Verdict, run_gold_set

RECORDS = [
    {"id": "a", "answer_text": "Revenue was $1.2B", "truth": 1_200_000_000, "unit": "currency"},
    {"id": "b", "answer_text": "Net income was $3.4M", "truth": 3_400_000_000, "unit": "currency"},
    {"id": "c", "answer_text": "No figure is given.", "truth": 5.0},
]


def test_aggregation_and_order():
    report = run_gold_set(RECORDS)
    assert report.total == 3
    assert report.record_ids == ("a", "b", "c")
    assert report.results[0].verdict == Verdict.EXACT
    assert report.results[1].verdict == Verdict.SCALE_ERROR
    assert report.results[2].verdict == Verdict.MISSING
    assert report.passed == 1
    assert report.pass_rate == 1 / 3


def test_by_verdict_only_includes_present_verdicts():
    report = run_gold_set(RECORDS)
    present = {cs.verdict for cs in report.by_verdict}
    assert present == {Verdict.EXACT, Verdict.SCALE_ERROR, Verdict.MISSING}
    assert sum(cs.count for cs in report.by_verdict) == 3


def test_report_serialization_round_trips():
    report = run_gold_set(RECORDS)
    as_dict = report.to_dict()
    assert as_dict["total"] == 3
    assert as_dict["results"][0]["id"] == "a"
    # to_json emits valid JSON
    assert json.loads(report.to_json())["passed"] == 1


def test_per_record_tolerance_override():
    rec = [
        {"id": "x", "answer_text": "$1.0B", "truth": 1_050_000_000, "unit": "currency", "tol": 0.1}
    ]
    # 4.76% off, but the per-record 10% tolerance lets it pass.
    assert run_gold_set(rec).results[0].verdict == Verdict.WITHIN_TOLERANCE


def test_table_renders():
    table = run_gold_set(RECORDS).to_table()
    assert "TOTAL 3" in table
    assert "EXACT" in table
