"""Shared runtime context.

Skills are plain functions, so they pull the active platform adapter and config
from here rather than receiving them as arguments. ``init_context`` is called
once at startup (and by tests with a mock adapter).
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import Config
from .platform import get_adapter
from .platform.base import PlatformAdapter


@dataclass
class Context:
    config: Config
    adapter: PlatformAdapter


_CONTEXT: Context | None = None


def init_context(config: Config, force_adapter: str | None = None) -> Context:
    global _CONTEXT
    _CONTEXT = Context(config=config, adapter=get_adapter(force_adapter))
    return _CONTEXT


def get_context() -> Context:
    if _CONTEXT is None:
        raise RuntimeError("Context not initialized; call init_context() first.")
    return _CONTEXT
