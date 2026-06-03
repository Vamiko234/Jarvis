"""Desktop vision agent: screenshot → vision LLM → pyautogui action (experimental).

Uses a vision-capable local model (e.g. qwen2.5-vl:7b) to look at the screen
and decide what to click/type/press next. This is intentionally marked
experimental — local vision models are less reliable than browser automation.

Requires (Windows): mss, Pillow, pyautogui (install with [windows] extras)
"""

from __future__ import annotations

import base64
import io
import json
import re
from typing import Any

from .base import AgentBase, StepResult

_SYSTEM = (
    "You are a desktop automation agent looking at a screenshot of the user's screen. "
    "Return ONLY a single valid JSON action — no explanation, no markdown:\n"
    '{"action": "click", "x": N, "y": N, "description": "what you are clicking"}\n'
    '{"action": "type", "text": "...", "description": "what you are typing"}\n'
    '{"action": "key", "key": "enter"|"escape"|"tab"|"ctrl+c"|"win+d"|..., "description": "..."}\n'
    '{"action": "scroll", "x": N, "y": N, "direction": "down"|"up", "amount": N}\n'
    '{"action": "screenshot", "description": "re-examine the current state"}\n'
    '{"action": "done", "summary": "what was accomplished"}\n'
    '{"action": "need_confirm", "reason": "why the user must approve before continuing"}\n'
    "Coordinates are pixel positions on the actual screen resolution."
)


class DesktopAgent(AgentBase):
    def __init__(self, config: Any, confirm=None) -> None:
        super().__init__(config, confirm=confirm)
        self.max_steps = 20

    def _screenshot_b64(self) -> str:
        import mss  # type: ignore
        from PIL import Image  # type: ignore

        with mss.mss() as sct:
            monitor = sct.monitors[1]  # primary monitor
            raw = sct.grab(monitor)

        img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
        # Resize to 1280-wide max so the model context stays manageable
        w, h = img.size
        if w > 1280:
            img = img.resize((1280, int(h * 1280 / w)), Image.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=80)
        return base64.b64encode(buf.getvalue()).decode()

    def _call_llm(self, goal: str, img_b64: str, history: list[StepResult]) -> dict:
        from ..context import get_context

        try:
            ctx = get_context()
            model = ctx.router.cfg.vision if ctx.router else self.config.brain.model
        except RuntimeError:
            model = self.config.brain.model

        history_text = ""
        if history:
            recent = history[-4:]
            history_text = "\nRecent actions:\n" + "\n".join(
                f"  {s.action[:60]}: {s.observation[:50]}" for s in recent
            ) + "\n"

        import ollama

        client = ollama.Client(host=self.config.brain.host)
        resp = client.chat(
            model=model,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {
                    "role": "user",
                    "content": f"Goal: {goal}{history_text}\nWhat is the next action?",
                    "images": [img_b64],
                },
            ],
        )
        content = (resp["message"].get("content") or "").strip()
        content = re.sub(r"^```(?:json)?\s*", "", content).strip()
        content = re.sub(r"\s*```$", "", content).strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            m = re.search(r"\{[^{}]+\}", content, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group())
                except Exception:
                    pass
            return {"action": "done", "summary": f"Could not parse output: {content[:200]}"}

    def _execute(self, action: dict) -> str:
        import pyautogui  # type: ignore

        pyautogui.FAILSAFE = True  # move mouse to corner to abort
        act = action.get("action", "")

        if act == "click":
            x, y = int(action.get("x", 0)), int(action.get("y", 0))
            pyautogui.click(x, y)
            return f"Clicked ({x}, {y}): {action.get('description', '')}"

        elif act == "type":
            text = str(action.get("text", ""))
            pyautogui.write(text, interval=0.04)
            return f"Typed: {text[:50]}"

        elif act == "key":
            key = str(action.get("key", ""))
            keys = key.split("+")
            if len(keys) > 1:
                pyautogui.hotkey(*keys)
            else:
                pyautogui.press(key)
            return f"Pressed: {key}"

        elif act == "scroll":
            x = int(action.get("x", 960))
            y = int(action.get("y", 540))
            amount = int(action.get("amount", 3))
            direction = action.get("direction", "down")
            pyautogui.scroll(-amount if direction == "down" else amount, x=x, y=y)
            return f"Scrolled {direction} at ({x}, {y})"

        elif act == "screenshot":
            return "Re-examining screen..."

        return f"Unknown action: {act}"

    def _step(self, goal: str, history: list[StepResult]) -> StepResult:
        img_b64 = self._screenshot_b64()
        action = self._call_llm(goal, img_b64, history)
        act = action.get("action", "")

        if act == "done":
            summary = action.get("summary", "Task complete.")
            return StepResult(action="done", observation=summary, done=True, summary=summary)

        if act == "need_confirm":
            reason = action.get("reason", "requires your confirmation")
            return StepResult(action=reason, observation="Waiting for confirmation", commit=True)

        commit = self.is_commit(str(action))
        try:
            obs = self._execute(action)
        except Exception as exc:
            obs = f"Error: {exc}"
        return StepResult(action=str(action), observation=obs, commit=commit)
