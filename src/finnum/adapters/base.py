"""Shared helpers for adapters.

An adapter turns an external benchmark into a list of :class:`GoldRecord`. Many benchmarks
ship the *gold* answer but not a *model* answer; such adapters produce records with an
empty ``answer_text`` that you fill with your own model's outputs via :func:`attach_answers`
before running :func:`finnum.run_gold_set`.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import replace

from ..result import GoldRecord


def attach_answers(
    records: Iterable[GoldRecord], answers_by_id: Mapping[str, str]
) -> list[GoldRecord]:
    """Return records with ``answer_text`` filled from ``answers_by_id`` (keyed by ``id``).

    Records without a provided answer are returned unchanged (an empty answer verifies as
    ``MISSING``), so the result aligns one-to-one with the input.
    """
    out = []
    for record in records:
        if record.id in answers_by_id:
            out.append(replace(record, answer_text=answers_by_id[record.id]))
        else:
            out.append(record)
    return out
