"""Text-to-speech. Picks an engine from config; falls back to printing if the
chosen engine's dependencies aren't installed (e.g. on the Linux dev box)."""

from __future__ import annotations

from ..config import VoiceConfig


class TTS:
    def __init__(self, cfg: VoiceConfig) -> None:
        self.cfg = cfg
        self._engine = None
        self._kind = "print"
        self._init_engine()

    def _init_engine(self) -> None:
        if self.cfg.tts_engine == "pyttsx3":
            try:
                import pyttsx3

                self._engine = pyttsx3.init()
                self._kind = "pyttsx3"
                return
            except Exception:
                pass
        elif self.cfg.tts_engine == "piper":
            try:
                from piper.voice import PiperVoice  # type: ignore

                if self.cfg.piper_voice:
                    self._engine = PiperVoice.load(self.cfg.piper_voice)
                    self._kind = "piper"
                    return
            except Exception:
                pass
        self._kind = "print"  # graceful fallback

    def speak(self, text: str) -> None:
        if not text:
            return
        if self._kind == "pyttsx3":
            self._engine.say(text)
            self._engine.runAndWait()
        elif self._kind == "piper":  # pragma: no cover - hardware/voice dependent
            import sounddevice as sd

            for chunk in self._engine.synthesize_stream_raw(text):
                sd.play(chunk, self._engine.config.sample_rate)
                sd.wait()
        else:
            print(f"🔊 {text}")
