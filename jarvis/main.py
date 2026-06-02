"""Jarvis entrypoint.

Usage:
    python -m jarvis.main --text     # typed mode (default)
    python -m jarvis.main --voice    # wake word + speech
"""

from __future__ import annotations

import argparse

from .assistant import Assistant
from .config import load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Jarvis — a PC assistant.")
    parser.add_argument("--voice", action="store_true", help="run in voice mode")
    parser.add_argument("--text", action="store_true", help="run in text mode (default)")
    parser.add_argument("--config", help="path to config.yaml")
    parser.add_argument(
        "--adapter",
        help="force a platform adapter (e.g. 'mock' for dev without a real OS)",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    assistant = Assistant(config, force_adapter=args.adapter)

    if args.voice and config.voice.enabled:
        assistant.run_voice()
    else:
        assistant.run_text()


if __name__ == "__main__":
    main()
