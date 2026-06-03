"""Jarvis entrypoint.

Usage:
    python -m jarvis.main --text           # typed terminal mode (default)
    python -m jarvis.main --voice          # wake word + speech
    python -m jarvis.main --ui             # browser UI at http://127.0.0.1:8765
    python -m jarvis.main --ui --port 9000 # custom port
"""

from __future__ import annotations

import argparse

from .assistant import Assistant
from .config import load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Jarvis — a PC assistant.")
    parser.add_argument("--voice", action="store_true", help="run in voice mode")
    parser.add_argument("--text", action="store_true", help="run in text mode (default)")
    parser.add_argument("--ui", action="store_true", help="run the browser UI server")
    parser.add_argument("--port", type=int, default=8765, help="port for --ui mode (default 8765)")
    parser.add_argument("--config", help="path to config.yaml")
    parser.add_argument(
        "--adapter",
        help="force a platform adapter (e.g. 'mock' for dev/testing)",
    )
    args = parser.parse_args()

    config = load_config(args.config)

    if args.ui:
        from .ui.server import run as run_ui
        run_ui(config, port=args.port, force_adapter=args.adapter)
    elif args.voice and config.voice.enabled:
        assistant = Assistant(config, force_adapter=args.adapter)
        assistant.run_voice()
    else:
        assistant = Assistant(config, force_adapter=args.adapter)
        assistant.run_text()


if __name__ == "__main__":
    main()
