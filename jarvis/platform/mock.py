"""Mock adapter: records actions instead of performing them.

Used for development on Linux and for unit tests, so the brain + skills can be
exercised end-to-end without touching a real OS.
"""

from __future__ import annotations

from .base import PlatformAdapter


class MockAdapter(PlatformAdapter):
    name = "mock"

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple]] = []
        self._volume = 50

    def _record(self, action: str, *args) -> None:
        self.calls.append((action, args))

    def open_app(self, name: str) -> str:
        self._record("open_app", name)
        return f"[mock] opened {name}"

    def close_app(self, name: str) -> str:
        self._record("close_app", name)
        return f"[mock] closed {name}"

    def set_volume(self, level: int) -> str:
        level = max(0, min(100, int(level)))
        self._volume = level
        self._record("set_volume", level)
        return f"[mock] volume set to {level}%"

    def get_volume(self) -> int:
        return self._volume

    def lock(self) -> str:
        self._record("lock")
        return "[mock] locked"

    def sleep(self) -> str:
        self._record("sleep")
        return "[mock] sleeping"

    def shutdown(self) -> str:
        self._record("shutdown")
        return "[mock] shutting down"

    def restart(self) -> str:
        self._record("restart")
        return "[mock] restarting"

    def screenshot(self, path: str) -> str:
        self._record("screenshot", path)
        return f"[mock] screenshot saved to {path}"

    def list_windows(self) -> list[str]:
        self._record("list_windows")
        return ["[mock] Window A", "[mock] Window B"]
