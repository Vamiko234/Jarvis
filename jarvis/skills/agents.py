"""Agent-dispatch skills.

These are the bridge between the conversational brain (which calls skills via
tool-use) and the sub-agents that drive browsers, do research, or control
the desktop.
"""

from __future__ import annotations

from ..context import get_context
from . import skill


@skill(
    name="browser_task",
    description=(
        "Use a web browser to complete a multi-step task: shop online, add items to a cart, "
        "fill forms, log into sites, navigate pages. Pauses for user confirmation before "
        "any checkout, payment, or irreversible submit action."
    ),
    parameters={
        "goal": {
            "type": "string",
            "description": (
                "What to accomplish in the browser. Be specific. "
                "Example: 'go to amazon.com and search for a mechanical tenkeyless keyboard, "
                "find one under $100 with good reviews, and add it to the cart'"
            ),
        }
    },
    group="agents",
)
def browser_task(goal: str) -> str:
    from ..agents.browser_agent import BrowserAgent

    ctx = get_context()
    agent = BrowserAgent(ctx.config, confirm=ctx.confirm_cb)
    return agent.run(goal)


@skill(
    name="research",
    description=(
        "Research a topic thoroughly using multiple web sources. "
        "Returns a spoken summary and saves a full cited markdown report to disk."
    ),
    parameters={
        "topic": {
            "type": "string",
            "description": "Topic or question to research, e.g. 'best mechanical keyboards under $150 in 2025'",
        }
    },
    group="agents",
)
def research(topic: str) -> str:
    from ..agents.research_agent import ResearchAgent

    ctx = get_context()
    agent = ResearchAgent(ctx.config)
    return agent.run(topic)


@skill(
    name="desktop_task",
    description=(
        "[Experimental] Control the desktop visually using screenshots and clicking — "
        "for tasks that are not in a web browser (e.g. in a native app). "
        "Less reliable than browser_task; use browser_task for anything web-based."
    ),
    parameters={
        "goal": {
            "type": "string",
            "description": "What to do on the desktop, e.g. 'open Spotify and play lo-fi playlist'",
        }
    },
    group="agents",
)
def desktop_task(goal: str) -> str:
    from ..agents.desktop_agent import DesktopAgent

    ctx = get_context()
    agent = DesktopAgent(ctx.config, confirm=ctx.confirm_cb)
    return agent.run(goal)
