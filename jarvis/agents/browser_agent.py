"""Browser agent: Playwright + accessibility-tree navigation.

The page state is represented as an indexed list of interactive elements
extracted from the accessibility tree — no raw HTML, no screenshots.
The LLM returns a single JSON action per step; the agent executes it and loops.

Requires: playwright (pip install playwright && playwright install chromium)
"""

from __future__ import annotations

import json
import re
from typing import Any

from .base import AgentBase, StepResult

_SYSTEM = (
    "You are a browser-control agent. You receive the current page state "
    "(URL, title, headings, and interactive elements with [index] labels) and a goal. "
    "Return ONLY a single valid JSON action object — no explanation, no markdown:\n"
    '{"action": "navigate", "url": "..."}\n'
    '{"action": "click", "index": N}\n'
    '{"action": "type", "index": N, "text": "..."}\n'
    '{"action": "scroll", "direction": "down"|"up", "amount": N}\n'
    '{"action": "back"}\n'
    '{"action": "extract", "description": "what to read from this page"}\n'
    '{"action": "done", "summary": "what was accomplished"}\n'
    '{"action": "need_confirm", "reason": "why the user must confirm before continuing"}'
)

_INTERACTIVE_SELECTOR = (
    'a[href]:not([href=""]):not([href="#"]), '
    "button:not([disabled]), "
    'input:not([type="hidden"]):not([disabled]), '
    "select:not([disabled]), textarea:not([disabled]), "
    '[role="button"]:not([disabled]), [role="link"], [role="menuitem"]'
)


class BrowserAgent(AgentBase):
    def __init__(self, config: Any, confirm=None) -> None:
        browser_cfg = getattr(config, "browser", None)
        extra_kw = list(getattr(browser_cfg, "commit_keywords", []))
        super().__init__(config, confirm=confirm, extra_commit_keywords=extra_kw)
        if browser_cfg:
            self.max_steps = browser_cfg.max_steps
        self._page = None
        self._browser = None
        self._pw = None

    # ------------------------------------------------------------------ #
    # Browser lifecycle
    # ------------------------------------------------------------------ #
    def _ensure_browser(self) -> None:
        if self._page is not None:
            return
        from playwright.sync_api import sync_playwright  # type: ignore

        import os

        browser_cfg = getattr(self.config, "browser", None)
        headless = getattr(browser_cfg, "headless", False) if browser_cfg else False
        profile_dir = None
        if browser_cfg and browser_cfg.profile_dir:
            profile_dir = os.path.expanduser(browser_cfg.profile_dir)
            os.makedirs(profile_dir, exist_ok=True)

        self._pw = sync_playwright().start()
        if profile_dir:
            self._browser = self._pw.chromium.launch_persistent_context(
                profile_dir,
                headless=headless,
                args=["--start-maximized"],
                viewport=None,
            )
            self._page = (
                self._browser.pages[0]
                if self._browser.pages
                else self._browser.new_page()
            )
        else:
            self._browser = self._pw.chromium.launch(headless=headless)
            ctx = self._browser.new_context(viewport={"width": 1280, "height": 800})
            self._page = ctx.new_page()

    def __del__(self) -> None:
        try:
            if self._browser:
                self._browser.close()
        except Exception:
            pass
        try:
            if self._pw:
                self._pw.stop()
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # Page snapshot
    # ------------------------------------------------------------------ #
    def _snapshot(self) -> str:
        page = self._page
        url = page.url
        try:
            title = page.title()
        except Exception:
            title = ""

        headings: list[str] = []
        try:
            for h in page.query_selector_all("h1, h2")[:3]:
                t = (h.inner_text() or "").strip()[:50]
                if t:
                    headings.append(t)
        except Exception:
            pass

        items: list[str] = []
        try:
            els = page.query_selector_all(_INTERACTIVE_SELECTOR)
            for i, el in enumerate(els[:60]):
                try:
                    tag = el.evaluate("el => el.tagName.toLowerCase()")
                    text = (el.inner_text() or "").strip()[:60].replace("\n", " ")
                    ph = el.get_attribute("placeholder") or ""
                    aria = el.get_attribute("aria-label") or ""
                    label = text or ph or aria or tag
                    items.append(f"[{i}] {tag}: {label}")
                except Exception:
                    continue
        except Exception:
            pass

        lines = [f"URL: {url}", f"Title: {title}"]
        if headings:
            lines.append("Headings: " + " | ".join(headings))
        lines.append("\nInteractive elements:")
        lines.extend(items or ["(none found)"])
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # LLM call
    # ------------------------------------------------------------------ #
    def _call_llm(self, goal: str, snapshot: str, history: list[StepResult]) -> dict:
        from ..context import get_context

        try:
            ctx = get_context()
            model = ctx.router.cfg.smart if ctx.router else self.config.models.smart
        except RuntimeError:
            model = getattr(self.config.models, "smart", self.config.brain.model)

        history_text = ""
        if history:
            recent = history[-5:]
            history_text = "\nRecent steps:\n" + "\n".join(
                f"  {s.action[:60]}: {s.observation[:60]}" for s in recent
            ) + "\n"

        import ollama

        client = ollama.Client(host=self.config.brain.host)
        resp = client.chat(
            model=model,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {
                    "role": "user",
                    "content": f"Goal: {goal}{history_text}\n\nPage state:\n{snapshot}\n\nNext action?",
                },
            ],
        )
        content = (resp["message"].get("content") or "").strip()
        # Strip markdown fences
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
            return {"action": "done", "summary": f"Could not parse LLM output: {content[:200]}"}

    # ------------------------------------------------------------------ #
    # Action execution
    # ------------------------------------------------------------------ #
    def _execute(self, action: dict) -> str:
        page = self._page
        act = action.get("action", "")

        if act == "navigate":
            url = str(action.get("url", ""))
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            page.goto(url, timeout=30_000, wait_until="domcontentloaded")
            return f"Navigated to {url}"

        elif act == "click":
            idx = int(action.get("index", 0))
            els = page.query_selector_all(_INTERACTIVE_SELECTOR)
            if idx < len(els):
                label = (els[idx].inner_text() or "").strip()[:40]
                els[idx].click(timeout=10_000)
                try:
                    page.wait_for_load_state("domcontentloaded", timeout=10_000)
                except Exception:
                    pass
                return f"Clicked [{idx}] {label}"
            return f"Element [{idx}] not found (page has {len(els)} elements)"

        elif act == "type":
            idx = int(action.get("index", 0))
            text = str(action.get("text", ""))
            inputs = page.query_selector_all(
                'input:not([type="hidden"]):not([disabled]), textarea:not([disabled])'
            )
            if idx < len(inputs):
                inputs[idx].fill(text)
                return f"Typed '{text[:40]}' into field [{idx}]"
            # Fall back: press key sequence in currently focused element
            page.keyboard.type(text)
            return f"Typed '{text[:40]}' (fallback keyboard)"

        elif act == "scroll":
            direction = action.get("direction", "down")
            amount = int(action.get("amount", 3)) * 300
            page.mouse.wheel(0, amount if direction == "down" else -amount)
            return f"Scrolled {direction}"

        elif act == "back":
            page.go_back(timeout=10_000)
            return "Navigated back"

        elif act == "extract":
            desc = action.get("description", "page content")
            try:
                text = page.inner_text("body")[:3000]
            except Exception:
                text = "(could not extract body text)"
            return f"Extracted ({desc}): {text}"

        return f"Unknown action: {act}"

    # ------------------------------------------------------------------ #
    # Step
    # ------------------------------------------------------------------ #
    def _step(self, goal: str, history: list[StepResult]) -> StepResult:
        self._ensure_browser()
        snapshot = self._snapshot()
        action = self._call_llm(goal, snapshot, history)
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
