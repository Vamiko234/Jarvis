"""Productivity skills: time, timers, reminders, clipboard, and quick notes."""

from __future__ import annotations

import json
import threading
from datetime import datetime

from ..context import get_context
from . import skill


@skill(
    name="get_time",
    description="Get the current date and time.",
    group="productivity",
)
def get_time() -> str:
    return datetime.now().strftime("It is %A, %d %B %Y, %I:%M %p.")


@skill(
    name="set_timer",
    description="Start a countdown timer that prints a message when it elapses.",
    parameters={
        "seconds": {"type": "integer", "description": "Duration in seconds"},
        "label": {"type": "string", "description": "What the timer is for"},
    },
    group="productivity",
)
def set_timer(seconds: int, label: str = "Timer") -> str:
    def _fire() -> None:
        print(f"\n⏰ {label} finished ({seconds}s elapsed).")

    threading.Timer(max(1, seconds), _fire).start()
    return f"Timer set for {seconds} seconds: {label}."


def _notes_file():
    return get_context().config.data_path / "notes.json"


def _load_notes() -> list[dict]:
    f = _notes_file()
    if f.exists():
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
    return []


@skill(
    name="add_note",
    description="Save a quick note for later.",
    parameters={"text": {"type": "string", "description": "Note contents"}},
    group="productivity",
)
def add_note(text: str) -> str:
    notes = _load_notes()
    notes.append({"text": text, "at": datetime.now().isoformat(timespec="seconds")})
    _notes_file().write_text(json.dumps(notes, indent=2), encoding="utf-8")
    return "Note saved."


@skill(
    name="list_notes",
    description="List all saved quick notes.",
    group="productivity",
)
def list_notes() -> str:
    notes = _load_notes()
    if not notes:
        return "You have no saved notes."
    return "Your notes:\n" + "\n".join(
        f"{i+1}. {n['text']} ({n['at']})" for i, n in enumerate(notes)
    )


@skill(
    name="read_clipboard",
    description="Read the current text contents of the system clipboard.",
    group="productivity",
)
def read_clipboard() -> str:
    try:
        import pyperclip
    except ImportError:
        return "Clipboard unavailable: install pyperclip."
    try:
        return f"Clipboard: {pyperclip.paste()}"
    except Exception as exc:
        return f"Could not read clipboard: {exc}"


@skill(
    name="write_clipboard",
    description="Copy text to the system clipboard.",
    parameters={"text": {"type": "string", "description": "Text to copy"}},
    group="productivity",
)
def write_clipboard(text: str) -> str:
    try:
        import pyperclip
    except ImportError:
        return "Clipboard unavailable: install pyperclip."
    try:
        pyperclip.copy(text)
        return "Copied to clipboard."
    except Exception as exc:
        return f"Could not write clipboard: {exc}"
