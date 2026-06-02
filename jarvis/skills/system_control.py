"""System control skills: apps, volume, power, screen."""

from __future__ import annotations

import os
from datetime import datetime

from ..context import get_context
from . import skill


@skill(
    name="open_app",
    description="Open/launch an application, file, or URL by name.",
    parameters={"name": {"type": "string", "description": "App, file path, or URL to open"}},
    group="system_control",
)
def open_app(name: str) -> str:
    return get_context().adapter.open_app(name)


@skill(
    name="close_app",
    description="Close/quit a running application by process or window name.",
    parameters={"name": {"type": "string", "description": "Application/process name"}},
    group="system_control",
)
def close_app(name: str) -> str:
    return get_context().adapter.close_app(name)


@skill(
    name="set_volume",
    description="Set the system master volume to a percentage from 0 to 100.",
    parameters={"level": {"type": "integer", "description": "Volume percent 0-100"}},
    group="system_control",
)
def set_volume(level: int) -> str:
    return get_context().adapter.set_volume(level)


@skill(
    name="get_volume",
    description="Get the current system master volume percentage.",
    group="system_control",
)
def get_volume() -> str:
    level = get_context().adapter.get_volume()
    return f"Volume is at {level}%." if level >= 0 else "Could not read volume."


@skill(
    name="lock_screen",
    description="Lock the workstation.",
    group="system_control",
)
def lock_screen() -> str:
    return get_context().adapter.lock()


@skill(
    name="sleep_pc",
    description="Put the computer to sleep.",
    group="system_control",
)
def sleep_pc() -> str:
    return get_context().adapter.sleep()


@skill(
    name="shutdown",
    description="Shut the computer down. Destructive — confirm first.",
    confirm=True,
    group="system_control",
)
def shutdown() -> str:
    return get_context().adapter.shutdown()


@skill(
    name="restart",
    description="Restart the computer. Destructive — confirm first.",
    confirm=True,
    group="system_control",
)
def restart() -> str:
    return get_context().adapter.restart()


@skill(
    name="take_screenshot",
    description="Capture a screenshot of the screen, saved to the data directory.",
    group="system_control",
)
def take_screenshot() -> str:
    ctx = get_context()
    fname = f"screenshot-{datetime.now():%Y%m%d-%H%M%S}.png"
    path = os.fspath(ctx.config.data_path / fname)
    return ctx.adapter.screenshot(path)


@skill(
    name="list_windows",
    description="List the titles of currently open windows.",
    group="system_control",
)
def list_windows() -> str:
    titles = get_context().adapter.list_windows()
    if not titles:
        return "No open windows found."
    return "Open windows:\n" + "\n".join(f"- {t}" for t in titles)
