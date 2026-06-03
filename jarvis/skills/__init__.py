"""Skill registry.

A skill is a plain Python function decorated with ``@skill``. The decorator
records its name, description, and JSON-schema parameters so the registry can:

  * generate the ``tools`` array passed to Ollama, and
  * dispatch a tool call coming back from the model to the right function.

Adding a new capability is therefore just: write a function, decorate it.
"""

from __future__ import annotations

import importlib
import inspect
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class Skill:
    name: str
    description: str
    parameters: dict[str, Any]
    func: Callable[..., str]
    confirm: bool          # action requires user confirmation before running
    group: str             # which skills.* group it belongs to (for toggling)


_REGISTRY: dict[str, Skill] = {}


def skill(
    *,
    name: str,
    description: str,
    parameters: dict[str, Any] | None = None,
    confirm: bool = False,
    group: str = "misc",
) -> Callable[[Callable[..., str]], Callable[..., str]]:
    """Register a function as an LLM-callable skill.

    ``parameters`` is a JSON-schema ``properties`` dict; required keys are
    inferred from parameters of the function that have no default value.
    """

    def decorator(func: Callable[..., str]) -> Callable[..., str]:
        props = parameters or {}
        sig = inspect.signature(func)
        required = [
            p.name
            for p in sig.parameters.values()
            if p.name in props and p.default is inspect.Parameter.empty
        ]
        _REGISTRY[name] = Skill(
            name=name,
            description=description,
            parameters={
                "type": "object",
                "properties": props,
                "required": required,
            },
            func=func,
            confirm=confirm,
            group=group,
        )
        return func

    return decorator


def load_skills() -> None:
    """Import skill modules so their @skill decorators run (idempotent)."""
    for mod in ("system_control", "files", "web", "productivity", "agents"):
        importlib.import_module(f"jarvis.skills.{mod}")


def enabled_skills(enabled_groups: dict[str, bool]) -> list[Skill]:
    """All registered skills whose group is enabled in config."""
    return [
        s for s in _REGISTRY.values() if enabled_groups.get(s.group, True)
    ]


def tool_schemas(skills: list[Skill]) -> list[dict[str, Any]]:
    """Build the Ollama ``tools`` array from a list of skills."""
    return [
        {
            "type": "function",
            "function": {
                "name": s.name,
                "description": s.description,
                "parameters": s.parameters,
            },
        }
        for s in skills
    ]


def get_skill(name: str) -> Skill | None:
    return _REGISTRY.get(name)


def clear_registry() -> None:
    """Test helper: empty the registry."""
    _REGISTRY.clear()
