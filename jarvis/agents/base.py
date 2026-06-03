"""Base agent: a step loop with a commit-gate.

Subclasses implement _step(goal, history) -> StepResult.
The commit-gate intercepts any action whose description contains a commit
keyword (checkout, buy, pay, submit, send, etc.) and demands user confirmation
before executing it.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Callable

ConfirmCallback = Callable[[str, dict[str, Any]], bool]

_COMMIT_KEYWORDS = frozenset([
    "checkout", "place order", "buy now", "confirm order",
    "pay", "payment", "purchase", "complete order",
    "send message", "submit form", "confirm payment",
    "submit order", "send email", "post comment", "submit",
])


@dataclasses.dataclass
class StepResult:
    action: str
    observation: str
    done: bool = False
    commit: bool = False
    summary: str = ""


class AgentBase:
    max_steps: int = 30

    def __init__(
        self,
        config: Any,
        confirm: ConfirmCallback | None = None,
        extra_commit_keywords: list[str] | None = None,
    ) -> None:
        self.config = config
        self.confirm = confirm or (lambda n, a: True)
        self._commit_kw = _COMMIT_KEYWORDS | frozenset(
            kw.lower() for kw in (extra_commit_keywords or [])
        )

    def is_commit(self, description: str) -> bool:
        low = description.lower()
        return any(kw in low for kw in self._commit_kw)

    def run(self, goal: str) -> str:
        history: list[StepResult] = []
        for _ in range(self.max_steps):
            result = self._step(goal, history)
            if result.commit or self.is_commit(result.action):
                if not self.confirm(result.action, {"goal": goal}):
                    return f"Stopped before '{result.action}' — you declined."
            history.append(result)
            if result.done:
                return result.summary or result.observation
        last = history[-1].observation if history else "n/a"
        return f"Reached {self.max_steps}-step limit. Last state: {last}"

    def _step(self, goal: str, history: list[StepResult]) -> StepResult:
        raise NotImplementedError
