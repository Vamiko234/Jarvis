"""Platform adapter interface.

Each method performs one OS-level action and returns a short human-readable
status string. Implementations must never raise for ordinary failures — they
return a message describing what happened so the assistant can relay it.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class PlatformAdapter(ABC):
    name: str = "base"

    # --- applications ---
    @abstractmethod
    def open_app(self, name: str) -> str: ...

    @abstractmethod
    def close_app(self, name: str) -> str: ...

    # --- audio ---
    @abstractmethod
    def set_volume(self, level: int) -> str:
        """Set master volume to a 0-100 percentage."""

    @abstractmethod
    def get_volume(self) -> int: ...

    # --- power ---
    @abstractmethod
    def lock(self) -> str: ...

    @abstractmethod
    def sleep(self) -> str: ...

    @abstractmethod
    def shutdown(self) -> str: ...

    @abstractmethod
    def restart(self) -> str: ...

    # --- screen / windows ---
    @abstractmethod
    def screenshot(self, path: str) -> str: ...

    @abstractmethod
    def list_windows(self) -> list[str]: ...
