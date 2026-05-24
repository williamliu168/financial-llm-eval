"""Adapters that load gold sets into finnum's :class:`GoldRecord` shape."""

from __future__ import annotations

from .base import attach_answers
from .edgar_demo import load_demo_gold
from .finqa import download_finqa, load_finqa

__all__ = ["load_demo_gold", "load_finqa", "download_finqa", "attach_answers"]
