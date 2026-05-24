"""Adapter for FinQA (Chen et al., 2021) — numeric reasoning over S&P 500 filings.

FinQA is MIT-licensed and hosted at https://github.com/czyssrs/FinQA. Its data is **not**
bundled with finnum; :func:`download_finqa` fetches a split on demand into a directory you
should keep out of version control (the default ``.finqa_data`` is gitignored).

Each FinQA row carries the gold answer (``qa.exe_ans``, the executed numeric result) but
not a model answer, so :func:`load_finqa` produces records with an empty ``answer_text``.
Run your model over ``record.question`` and attach the outputs with
:func:`finnum.adapters.attach_answers` before scoring.

Caveat: FinQA's ``exe_ans`` is expressed in the *source table's units* (frequently
millions), not absolute dollars — so compare model answers in the same convention (e.g.
"11,043", not "$11,043 million"), or rescale the truth to match how your model answers.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..result import GoldRecord

# FinQA splits live under dataset/ in the GitHub repo. Branch name has varied across forks,
# so we try the common ones. Override `urls` in download_finqa if your source differs.
_DEFAULT_URLS: dict[str, list[str]] = {
    split: [
        f"https://raw.githubusercontent.com/czyssrs/FinQA/{branch}/dataset/{split}.json"
        for branch in ("master", "main")
    ]
    for split in ("train", "dev", "test")
}


def _truth_and_unit(qa: dict) -> tuple[float, str] | None:
    """Map a FinQA ``qa`` block to ``(truth, unit)``, or ``None`` if non-numeric.

    ``exe_ans`` is FinQA's executed numeric answer. Some rows answer "yes"/"no" or a span;
    those are skipped. A trailing "%" in the textual answer tags the unit as percent — note
    that FinQA often stores such answers already as a ratio (e.g. 0.141 for "14.1%"), so you
    may prefer ``unit="ratio"`` depending on how your model phrases answers.
    """
    try:
        truth = float(qa["exe_ans"])
    except (KeyError, TypeError, ValueError):
        return None
    answer_text = str(qa.get("answer", "")).strip()
    unit = "percent" if answer_text.endswith("%") else "unknown"
    return truth, unit


def load_finqa(path: str | Path) -> list[GoldRecord]:
    """Load a FinQA split file into gold-only :class:`GoldRecord` objects.

    Records have an empty ``answer_text`` (FinQA provides gold, not a model answer). Rows
    whose ``exe_ans`` is non-numeric are skipped.
    """
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    records: list[GoldRecord] = []
    for row in rows:
        qa = row.get("qa") or row.get("qa_0") or {}
        mapped = _truth_and_unit(qa)
        if mapped is None:
            continue
        truth, unit = mapped
        records.append(
            GoldRecord(
                id=str(row.get("id", f"finqa-{len(records)}")),
                answer_text="",
                truth=truth,
                unit=unit,  # type: ignore[arg-type]
                question=qa.get("question"),
                source="FinQA",
                meta={"gold_answer": qa.get("answer"), "program": qa.get("program")},
            )
        )
    return records


def download_finqa(
    split: str = "dev",
    dest: str | Path = ".finqa_data",
    urls: dict[str, list[str]] | None = None,
) -> Path:  # pragma: no cover - network I/O, exercised manually
    """Download a FinQA split to ``dest`` (idempotent). Returns the file path.

    FinQA data is not redistributed by finnum; this fetches it from the upstream
    MIT-licensed repository. Keep ``dest`` out of version control.
    """
    import urllib.request

    dest_dir = Path(dest)
    dest_dir.mkdir(parents=True, exist_ok=True)
    out = dest_dir / f"{split}.json"
    if out.exists():
        return out

    candidates = (urls or _DEFAULT_URLS).get(split)
    if not candidates:
        raise ValueError(f"unknown FinQA split: {split!r}")

    errors = []
    for url in candidates:
        try:
            urllib.request.urlretrieve(url, out)  # noqa: S310 (trusted upstream URL)
            print(f"Downloaded FinQA '{split}' from {url}")
            print("FinQA (Chen et al., 2021) is MIT-licensed: https://github.com/czyssrs/FinQA")
            return out
        except Exception as exc:  # noqa: BLE001 - try the next candidate URL
            errors.append((url, repr(exc)))
    raise RuntimeError(f"could not download FinQA '{split}'. Tried: {errors}")
