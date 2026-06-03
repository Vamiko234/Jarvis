"""The brain: an Ollama-backed tool-calling conversation loop.

``Brain.respond`` takes a user utterance, lets the model call skills as needed
(executing each and feeding the result back), and returns the final spoken text.
Destructive skills are gated through an optional confirm callback.
"""

from __future__ import annotations

import json
from typing import Any, Callable

from ..config import Config
from ..context import get_context
from ..skills import (
    enabled_skills,
    get_skill,
    load_skills,
    tool_schemas,
)
from .prompts import system_prompt

# (skill_name, arguments) -> user approves?  Defaults to allow.
ConfirmCallback = Callable[[str, dict[str, Any]], bool]


def _default_confirm(_name: str, _args: dict[str, Any]) -> bool:
    return True


class Brain:
    def __init__(self, config: Config, client: Any | None = None) -> None:
        self.config = config
        load_skills()
        self._skills = enabled_skills(
            {
                "system_control": config.skills.system_control,
                "files": config.skills.files,
                "web": config.skills.web,
                "productivity": config.skills.productivity,
                "agents": config.skills.agents,
            }
        )
        self._tools = tool_schemas(self._skills)
        self._confirm_set = set(config.safety.confirm_actions)
        self._blocked = set(config.safety.blocked_actions)
        self.messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt(config.assistant.name)}
        ]
        if client is not None:
            self.client = client
        else:  # pragma: no cover
            import ollama

            self.client = ollama.Client(host=config.brain.host)

    def _run_tool(self, name: str, args: dict[str, Any], confirm: ConfirmCallback) -> str:
        if name in self._blocked:
            return f"Action '{name}' is blocked by configuration."
        sk = get_skill(name)
        if sk is None:
            return f"Unknown tool: {name}"
        if (sk.confirm or name in self._confirm_set) and not confirm(name, args):
            return f"Cancelled: the user declined to run '{name}'."
        try:
            return sk.func(**args)
        except TypeError as exc:
            return f"Bad arguments for {name}: {exc}"
        except Exception as exc:  # keep the loop alive on skill errors
            return f"Error running {name}: {exc}"

    def respond(self, user_text: str, confirm: ConfirmCallback = _default_confirm) -> str:
        """Process one user turn and return the assistant's final text reply."""
        # Store confirm on context so agent skills can access it
        try:
            ctx = get_context()
            ctx.confirm_cb = confirm
            router = ctx.router
        except RuntimeError:
            router = None

        # Pick model tier based on what the user asked
        if router is not None:
            model = router.model_for(user_text)
        else:
            model = self.config.brain.model

        # Snapshot so a failed turn doesn't leave a dangling user/tool message
        # that would corrupt the next request.
        checkpoint = len(self.messages)
        self.messages.append({"role": "user", "content": user_text})

        try:
            return self._chat_loop(model, confirm)
        except Exception:
            del self.messages[checkpoint:]
            raise

    def _chat_loop(self, model: str, confirm: ConfirmCallback) -> str:
        for _ in range(self.config.brain.max_tool_iterations):
            reply = self.client.chat(
                model=model,
                messages=self.messages,
                tools=self._tools,
            )
            msg = reply["message"]
            self.messages.append(msg)

            tool_calls = msg.get("tool_calls") or []
            if not tool_calls:
                return (msg.get("content") or "").strip()

            for call in tool_calls:
                fn = call["function"]
                name = fn["name"]
                args = fn.get("arguments") or {}
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}
                result = self._run_tool(name, args, confirm)
                self.messages.append(
                    {"role": "tool", "name": name, "content": str(result)}
                )

        # Ran out of tool iterations; ask the model for a final answer with no tools.
        reply = self.client.chat(model=model, messages=self.messages)
        return (reply["message"].get("content") or "").strip()
