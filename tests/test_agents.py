"""Agent base: step loop, commit gate, confirm callbacks."""

from jarvis.agents.base import AgentBase, StepResult


class _CountAgent(AgentBase):
    """Runs N steps then returns done."""

    def __init__(self, steps, config=None, confirm=None, extra_kw=None):
        from jarvis.config import Config
        super().__init__(config or Config(), confirm=confirm, extra_commit_keywords=extra_kw)
        self._steps = iter(steps)

    def _step(self, goal, history):
        return next(self._steps)


def test_runs_to_done():
    agent = _CountAgent([
        StepResult("search web", "found 5 results"),
        StepResult("extract info", "got data", done=True, summary="Research complete"),
    ])
    result = agent.run("do something")
    assert result == "Research complete"


def test_commit_gate_blocks_without_confirm():
    called = []
    agent = _CountAgent(
        [StepResult("checkout", "checking out", commit=True)],
        confirm=lambda n, a: False,
    )
    result = agent.run("buy stuff")
    assert "declined" in result or "Stopped" in result


def test_commit_gate_passes_with_confirm():
    agent = _CountAgent(
        [
            StepResult("checkout", "checking out", commit=True),
            StepResult("done", "order placed", done=True, summary="Ordered."),
        ],
        confirm=lambda n, a: True,
    )
    result = agent.run("buy stuff")
    assert result == "Ordered."


def test_keyword_commit_detection():
    agent = _CountAgent([], confirm=lambda n, a: True)
    assert agent.is_commit("place order on amazon")
    assert agent.is_commit("confirm payment")
    assert not agent.is_commit("scroll down the page")
    assert not agent.is_commit("search for keyboards")


def test_extra_commit_keywords():
    agent = _CountAgent([], extra_kw=["delete account"])
    assert agent.is_commit("delete account on this site")
    assert not agent.is_commit("normal action")


def test_step_limit():
    infinite = (StepResult(f"step {i}", "obs") for i in range(1000))
    agent = _CountAgent(infinite)
    agent.max_steps = 5
    result = agent.run("go forever")
    assert "5-step limit" in result
