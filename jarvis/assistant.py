"""Orchestrator: ties the brain, voice I/O, and confirmation flow into a loop.

Two run modes:
  * text  — type a request, read the reply (no audio deps needed)
  * voice  — wait for the wake word, record, transcribe, act, speak
"""

from __future__ import annotations

from typing import Any

from .brain.llm import Brain
from .config import Config
from .context import init_context


class Assistant:
    def __init__(self, config: Config, force_adapter: str | None = None) -> None:
        self.config = config
        init_context(config, force_adapter=force_adapter)
        self.brain = Brain(config)

    # --- confirmation callbacks ---
    def _text_confirm(self, name: str, args: dict[str, Any]) -> bool:
        ans = input(f"⚠️  Confirm '{name}' {args or ''}? [y/N] ").strip().lower()
        return ans in ("y", "yes")

    def _voice_confirm(self, tts, stt):
        def _confirm(name: str, args: dict[str, Any]) -> bool:
            tts.speak(f"Do you want me to {name.replace('_', ' ')}? Say yes or no.")
            answer = stt.listen(seconds=3).lower()
            return "yes" in answer
        return _confirm

    # --- run modes ---
    def run_text(self) -> None:
        print(f"{self.config.assistant.name} (text mode). Type 'quit' to exit.\n")
        while True:
            try:
                user = input("you › ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if user.lower() in ("quit", "exit"):
                break
            if not user:
                continue
            try:
                reply = self.brain.respond(user, confirm=self._text_confirm)
            except ConnectionError:
                print(
                    f"{self.config.assistant.name} › [Ollama is not running. "
                    "Start it with `ollama serve` then try again.]\n"
                )
                continue
            except Exception as exc:
                print(f"{self.config.assistant.name} › [Error: {exc}]\n")
                continue
            print(f"{self.config.assistant.name} › {reply}\n")

    def run_voice(self) -> None:  # pragma: no cover - requires audio hardware
        from .audio.stt import STT
        from .audio.tts import TTS
        from .audio.wakeword import WakeWord

        tts = TTS(self.config.voice)
        stt = STT(self.config.voice)
        wake = WakeWord(self.config.voice)
        confirm = self._voice_confirm(tts, stt)

        name = self.config.assistant.name
        print(f"{name} (voice mode). Say '{self.config.voice.wake_word}'. Ctrl+C to exit.")
        tts.speak(f"{name} online.")
        while True:
            try:
                wake.wait()
                tts.speak("Yes?")
                user = stt.listen(seconds=6)
                if not user:
                    continue
                print(f"you › {user}")
                reply = self.brain.respond(user, confirm=confirm)
                print(f"{name} › {reply}")
                tts.speak(reply)
            except KeyboardInterrupt:
                break
