"""Windows implementation of the platform adapter.

Dependencies (pycaw, comtypes, pygetwindow, pyautogui) are imported lazily so
this module can be imported on non-Windows machines without crashing.
"""

from __future__ import annotations

import os
import subprocess

from .base import PlatformAdapter


def _powershell(script: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
        timeout=30,
    )


class WindowsAdapter(PlatformAdapter):
    name = "windows"

    def open_app(self, name: str) -> str:
        try:
            # `start` resolves Start-menu apps, URLs, files, and PATH executables.
            os.startfile(name)  # type: ignore[attr-defined]
            return f"Opened {name}."
        except OSError:
            res = _powershell(f"Start-Process '{name}'")
            if res.returncode == 0:
                return f"Opened {name}."
            return f"Could not open {name}: {res.stderr.strip() or 'not found'}"

    def close_app(self, name: str) -> str:
        proc = name[:-4] if name.lower().endswith(".exe") else name
        res = _powershell(f"Stop-Process -Name '{proc}' -Force -ErrorAction Stop")
        if res.returncode == 0:
            return f"Closed {name}."
        return f"Could not close {name}: {res.stderr.strip() or 'not running'}"

    def set_volume(self, level: int) -> str:
        level = max(0, min(100, int(level)))
        try:
            from comtypes import CLSCTX_ALL  # type: ignore
            from ctypes import POINTER, cast  # noqa: F401
            from pycaw.pycaw import (  # type: ignore
                AudioUtilities,
                IAudioEndpointVolume,
            )

            devices = AudioUtilities.GetSpeakers()
            iface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            vol = cast(iface, POINTER(IAudioEndpointVolume))
            vol.SetMasterVolumeLevelScalar(level / 100.0, None)
            return f"Volume set to {level}%."
        except Exception as exc:  # pragma: no cover - hardware dependent
            return f"Could not set volume: {exc}"

    def get_volume(self) -> int:
        try:
            from comtypes import CLSCTX_ALL  # type: ignore
            from ctypes import POINTER, cast  # noqa: F401
            from pycaw.pycaw import (  # type: ignore
                AudioUtilities,
                IAudioEndpointVolume,
            )

            devices = AudioUtilities.GetSpeakers()
            iface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            vol = cast(iface, POINTER(IAudioEndpointVolume))
            return round(vol.GetMasterVolumeLevelScalar() * 100)
        except Exception:  # pragma: no cover
            return -1

    def lock(self) -> str:
        subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
        return "Workstation locked."

    def sleep(self) -> str:
        subprocess.run(
            ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"]
        )
        return "Going to sleep."

    def shutdown(self) -> str:
        subprocess.run(["shutdown", "/s", "/t", "0"])
        return "Shutting down."

    def restart(self) -> str:
        subprocess.run(["shutdown", "/r", "/t", "0"])
        return "Restarting."

    def screenshot(self, path: str) -> str:
        try:
            import pyautogui  # type: ignore

            pyautogui.screenshot(path)
            return f"Screenshot saved to {path}."
        except Exception as exc:  # pragma: no cover
            return f"Could not take screenshot: {exc}"

    def list_windows(self) -> list[str]:
        try:
            import pygetwindow as gw  # type: ignore

            return [t for t in gw.getAllTitles() if t.strip()]
        except Exception:  # pragma: no cover
            return []
