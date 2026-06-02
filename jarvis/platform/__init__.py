"""OS adapters. Windows-specific behavior is isolated here so the brain and
skills stay testable on any platform via the mock adapter."""

from __future__ import annotations

import sys

from .base import PlatformAdapter


def get_adapter(force: str | None = None) -> PlatformAdapter:
    """Return the adapter for the current OS.

    Pass force="mock" / "windows" to override (used by tests and Linux dev).
    """
    name = force or sys.platform
    if name in ("mock", "test"):
        from .mock import MockAdapter

        return MockAdapter()
    if name == "win32" or name == "windows":
        from .windows import WindowsAdapter

        return WindowsAdapter()
    # No native support yet for darwin/linux control -> safe mock so the rest runs.
    from .mock import MockAdapter

    return MockAdapter()
