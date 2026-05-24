"""The bundled EDGAR demo gold set loads and exercises every verdict."""

from finnum import Verdict, run_gold_set
from finnum.adapters import load_demo_gold


def test_demo_gold_loads_with_sources():
    records = load_demo_gold()
    assert len(records) == 24
    assert all(r.source for r in records), "every demo record cites its filing"
    assert all(r.answer_text for r in records)


def test_demo_run_covers_all_eight_verdicts():
    report = run_gold_set(load_demo_gold())
    assert report.total == 24
    present = {cs.verdict for cs in report.by_verdict}
    assert present == set(Verdict), "the demo should illustrate all eight verdicts"


def test_demo_spot_checks():
    report = run_gold_set(load_demo_gold())
    by_id = dict(zip(report.record_ids, report.results, strict=True))
    assert by_id["aapl_rev_2023_exact"].verdict == Verdict.EXACT
    assert by_id["aapl_rev_2023_scale"].verdict == Verdict.SCALE_ERROR
    assert by_id["msft_oi_2023_sign"].verdict == Verdict.SIGN_ERROR
    assert by_id["aapl_gm_2023_unit"].verdict == Verdict.UNIT_CONFUSION
    assert by_id["msft_ni_2023_missing"].verdict == Verdict.MISSING
    assert by_id["msft_rev_2023_fabricated"].looks_fabricated is True
