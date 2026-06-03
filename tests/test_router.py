"""Model router tier classification."""

from jarvis.brain.router import ModelRouter
from jarvis.config import ModelTiersConfig


def _router():
    return ModelRouter(ModelTiersConfig(fast="7b", smart="32b", vision="vl"))


def test_simple_commands_are_fast():
    r = _router()
    for text in ["what time is it", "set volume to 50", "lock the screen", "hello"]:
        assert r.tier(text) == "fast", f"Expected fast for: {text}"


def test_shopping_routes_smart():
    r = _router()
    for text in [
        "go to amazon and order a keyboard",
        "buy me a coffee mug",
        "book a table at a restaurant",
        "research the best gaming mice",
    ]:
        assert r.tier(text) == "smart", f"Expected smart for: {text}"


def test_vision_keywords_route_vision():
    r = _router()
    for text in [
        "what's on the screen",
        "desktop task: open settings",
        "take a screenshot",
    ]:
        assert r.tier(text) == "vision", f"Expected vision for: {text}"


def test_model_for_returns_correct_name():
    r = _router()
    assert r.model_for("set volume to 40") == "7b"
    assert r.model_for("research the best keyboards") == "32b"
    assert r.model_for("what's on the screen") == "vl"
