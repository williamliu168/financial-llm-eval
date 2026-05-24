"""Loader for the bundled, public-domain EDGAR demo gold set.

The figures are facts transcribed from public SEC filings (cited per record); the
``answer_text`` strings are synthetic illustrations chosen to exercise every verdict.
"""

from __future__ import annotations

import json
from importlib import resources

from ..result import GoldRecord

_DATA_PACKAGE = "finnum.data"
_DATA_FILE = "edgar_gold_v1.json"


def load_demo_gold() -> list[GoldRecord]:
    """Return the bundled EDGAR demo gold set as a list of :class:`GoldRecord`."""
    raw = resources.files(_DATA_PACKAGE).joinpath(_DATA_FILE).read_text(encoding="utf-8")
    return [GoldRecord.from_dict(record) for record in json.loads(raw)]
