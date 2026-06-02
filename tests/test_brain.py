"""Brain tool-calling loop using a fake Ollama client."""

from jarvis.brain.llm import Brain


class FakeClient:
    """Replays a scripted list of responses, one per chat() call."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def chat(self, model, messages, tools=None):
        self.calls.append({"messages": list(messages), "tools": tools})
        return self._responses.pop(0)


def _tool_msg(name, args):
    return {"message": {"role": "assistant", "content": "",
                        "tool_calls": [{"function": {"name": name, "arguments": args}}]}}


def _text_msg(text):
    return {"message": {"role": "assistant", "content": text}}


def test_plain_answer_no_tools(config):
    client = FakeClient([_text_msg("Hello there.")])
    brain = Brain(config, client=client)
    assert brain.respond("hi") == "Hello there."


def test_tool_call_then_answer(ctx, config):
    client = FakeClient([
        _tool_msg("set_volume", {"level": 30}),
        _text_msg("Volume is now at 30 percent."),
    ])
    brain = Brain(config, client=client)
    reply = brain.respond("set volume to 30")
    assert "30" in reply
    assert ctx.adapter.get_volume() == 30
    # a tool result message was fed back to the model
    assert any(m.get("role") == "tool" for m in client.calls[1]["messages"])


def test_confirm_declined_cancels_action(ctx, config):
    config.safety.confirm_actions = ["set_volume"]
    client = FakeClient([
        _tool_msg("set_volume", {"level": 90}),
        _text_msg("Okay, I won't change it."),
    ])
    brain = Brain(config, client=client)
    brain.respond("crank it up", confirm=lambda n, a: False)
    # volume unchanged from the mock default
    assert ctx.adapter.get_volume() == 50


def test_blocked_action(ctx, config):
    config.safety.blocked_actions = ["shutdown"]
    client = FakeClient([
        _tool_msg("shutdown", {}),
        _text_msg("That action is blocked."),
    ])
    brain = Brain(config, client=client)
    brain.respond("shut down")
    assert ("shutdown", ()) not in ctx.adapter.calls
