"""Speech-to-text via faster-whisper, recording from the default microphone.

Imports are lazy so the package works on machines without audio deps installed.
"""

from __future__ import annotations

from ..config import VoiceConfig

SAMPLE_RATE = 16000


class STT:
    def __init__(self, cfg: VoiceConfig) -> None:
        self.cfg = cfg
        self._model = None

    def _ensure_model(self) -> None:
        if self._model is None:
            from faster_whisper import WhisperModel  # type: ignore

            self._model = WhisperModel(self.cfg.stt_model, compute_type="int8")

    def record(self, seconds: float = 5.0):
        """Record mono audio from the default mic and return a numpy float32 array."""
        import numpy as np  # noqa: F401
        import sounddevice as sd

        audio = sd.rec(
            int(seconds * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="float32"
        )
        sd.wait()
        return audio.flatten()

    def transcribe(self, audio) -> str:
        self._ensure_model()
        segments, _ = self._model.transcribe(audio, language="en")
        return " ".join(seg.text for seg in segments).strip()

    def listen(self, seconds: float = 5.0) -> str:
        """Record then transcribe one utterance."""
        return self.transcribe(self.record(seconds))
