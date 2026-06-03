"""FastAPI UI server for Jarvis.

Serves the single-file HTML frontend and provides:
  POST /command          — process a user command, returns reply + step log
  POST /confirm-response — user answers a pending confirmation (yes/no)
  GET  /status           — current model tier, latency, task state

The brain runs synchronously in a thread pool so the async server stays
responsive. Confirmation requests pause the brain thread and wake it
when the user's answer arrives via POST /confirm-response.
"""

from __future__ import annotations

import threading
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from ..assistant import Assistant
from ..config import Config

_STATIC = Path(__file__).parent / "static"

app = FastAPI(title="Jarvis UI")
app.mount("/static", StaticFiles(directory=str(_STATIC)), name="static")

# Shared state — accessed from both the HTTP thread and the brain thread
_state: dict[str, Any] = {
    "model": "—",
    "tier": "fast",
    "latency_ms": 0,
    "task_steps": [],
    "confirm_pending": None,   # {"id": str, "action": str} | None
    "confirm_event": None,     # threading.Event
    "confirm_result": False,
}
_state_lock = threading.Lock()

# The assistant is created once when the server starts via setup()
_assistant: Assistant | None = None


def setup(config: Config, force_adapter: str | None = None) -> None:
    global _assistant
    _assistant = Assistant(config, force_adapter=force_adapter)


def _web_confirm(action: str, args: dict) -> bool:
    """Confirmation callback for the UI: sends a pending request and blocks."""
    confirm_id = str(uuid.uuid4())
    event = threading.Event()
    with _state_lock:
        _state["confirm_pending"] = {"id": confirm_id, "action": action}
        _state["confirm_event"] = event
        _state["confirm_result"] = False

    # Wait up to 120 seconds for the user to click Confirm or Deny
    event.wait(timeout=120)

    with _state_lock:
        result = _state["confirm_result"]
        _state["confirm_pending"] = None
        _state["confirm_event"] = None
    return result


@app.get("/")
def index() -> FileResponse:
    return FileResponse(str(_STATIC / "index.html"))


@app.get("/health")
def health() -> JSONResponse:
    """Returns whether Ollama is reachable. Used by the UI on startup."""
    if _assistant is None:
        return JSONResponse({"ollama": False, "error": "not initialized"})
    try:
        import ollama
        client = ollama.Client(host=_assistant.config.brain.host)
        client.list()
        return JSONResponse({"ollama": True})
    except Exception as exc:
        return JSONResponse({"ollama": False, "error": str(exc)})


@app.post("/command")
def command(body: dict) -> JSONResponse:
    if _assistant is None:
        return JSONResponse({"error": "Assistant not initialized"}, status_code=503)

    text = str(body.get("text", "")).strip()
    if not text:
        return JSONResponse({"error": "Empty command"}, status_code=400)

    # Clear task steps for this new command
    with _state_lock:
        _state["task_steps"] = []

    # Determine model tier for display
    from ..context import get_context
    try:
        ctx = get_context()
        tier = ctx.router.tier(text) if ctx.router else "fast"
        model_name = ctx.router.model_for(text) if ctx.router else ctx.config.brain.model
    except RuntimeError:
        tier, model_name = "fast", "—"

    with _state_lock:
        _state["tier"] = tier
        _state["model"] = model_name

    t0 = time.monotonic()
    try:
        reply = _assistant.brain.respond(text, confirm=_web_confirm)
    except ConnectionError:
        return JSONResponse(
            {"error": "Can't reach Ollama. Start it with `ollama serve` and make "
                      "sure the model is pulled (e.g. `ollama pull qwen2.5:7b`)."},
            status_code=503,
        )
    except Exception as exc:  # surface a readable message instead of a bare 500
        return JSONResponse({"error": f"{type(exc).__name__}: {exc}"}, status_code=500)
    latency = round((time.monotonic() - t0) * 1000)

    with _state_lock:
        _state["latency_ms"] = latency
        steps = list(_state["task_steps"])

    return JSONResponse({"reply": reply, "steps": steps, "model": model_name, "latency_ms": latency})


@app.get("/status")
def status() -> JSONResponse:
    with _state_lock:
        return JSONResponse({
            "model": _state["model"],
            "tier": _state["tier"],
            "latency_ms": _state["latency_ms"],
            "confirm_pending": _state["confirm_pending"],
        })


@app.post("/confirm-response")
def confirm_response(body: dict) -> JSONResponse:
    confirm_id = body.get("id")
    approved = bool(body.get("approved", False))
    with _state_lock:
        pending = _state["confirm_pending"]
        event = _state["confirm_event"]
        if pending and pending["id"] == confirm_id and event:
            _state["confirm_result"] = approved
            event.set()
            return JSONResponse({"ok": True})
    return JSONResponse({"ok": False, "error": "No matching pending confirmation"}, status_code=404)


def run(config: Config, host: str = "127.0.0.1", port: int = 8765,
        force_adapter: str | None = None) -> None:
    import uvicorn  # type: ignore

    setup(config, force_adapter=force_adapter)
    print(f"Jarvis UI → http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="warning")
