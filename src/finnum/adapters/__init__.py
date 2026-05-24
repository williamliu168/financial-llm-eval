"""Adapters that load gold sets into finnum's :class:`GoldRecord` shape."""

from __future__ import annotations

from .edgar_demo import load_demo_gold

__all__ = ["load_demo_gold"]
