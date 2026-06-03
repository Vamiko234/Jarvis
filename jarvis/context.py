"""Shared runtime context."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .config import Config
from .platform import get_adapter
from .platform.base import PlatformAdapter

ConfirmCallback = Callable[[str, dict[str, Any]], bool]


@dataclass
class Context:
    config: Config
    adapter: PlatformAdapter
    router: Any | None = field(default=None)
    confirm_cb: ConfirmCallback | None = field(default=None)


_CONTEXT: Context | None = None


def init_context(config: Config, force_adapter: str | None = None) -> Context:
    from .brain.router import ModelRouter
    global _CONTEXT
    _CONTEXT = Context(
        config=config,
        adapter=get_adapter(force_adapter),
        router=ModelRouter(config.models),
    )
    return _CONTEXT


def get_context() -> Context:
    if _CONTEXT is None:
        raise RuntimeError("Context not initialized; call init_context() first.")
    return _CONTEXT
