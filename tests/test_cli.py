"""CLI smoke tests for the verify / run / demo subcommands."""

import json

import pytest

from finnum.cli import main


def test_version_exits_zero():
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0


def test_verify_pass_returns_zero(capsys):
    rc = main(["verify", "--answer", "Revenue was $1.2B", "--truth", "1.2e9"])
    assert rc == 0
    assert "EXACT" in capsys.readouterr().out


def test_verify_failure_returns_one(capsys):
    rc = main(["verify", "--answer", "Net income was $3.4M", "--truth", "3.4e9"])
    assert rc == 1
    assert "SCALE_ERROR" in capsys.readouterr().out


def test_verify_json_output(capsys):
    rc = main(["verify", "--answer", "$1.2B", "--truth", "1.2e9", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["verdict"] == "EXACT"


def test_demo_runs(capsys):
    rc = main(["demo"])
    assert rc == 0
    assert "TOTAL 24" in capsys.readouterr().out


def test_run_with_fail_under_gate(tmp_path, capsys):
    gold = tmp_path / "gold.jsonl"
    gold.write_text(
        "\n".join(
            [
                json.dumps({"id": "ok", "answer_text": "$1.2B", "truth": 1_200_000_000}),
                json.dumps({"id": "bad", "answer_text": "$3.4M", "truth": 3_400_000_000}),
            ]
        ),
        encoding="utf-8",
    )
    # 50% pass rate is below the 0.99 gate -> non-zero exit.
    assert main(["run", str(gold), "--fail-under", "0.99"]) == 1
    # ... and passes a lenient gate.
    assert main(["run", str(gold), "--fail-under", "0.4"]) == 0


def test_run_json_format(tmp_path, capsys):
    gold = tmp_path / "g.jsonl"
    record = {"id": "x", "answer_text": "$1.2B", "truth": 1_200_000_000}
    gold.write_text(json.dumps(record), encoding="utf-8")
    rc = main(["run", str(gold), "--format", "json"])
    assert rc == 0
    assert json.loads(capsys.readouterr().out)["total"] == 1
