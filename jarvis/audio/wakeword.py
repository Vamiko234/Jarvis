"""Wake-word detection via openWakeWord.

Continuously reads mic frames and blocks until the wake word is detected, then
returns so the orchestrator can record the following command.
"""

from __future__ import annotations

from ..config import VoiceConfig

SAMPLE_RATE = 16000
FRAME = 1280  # 80ms at 16kHz, openWakeWord's expected chunk


class WakeWord:
    def __init__(self, cfg: VoiceConfig) -> None:
        self.cfg = cfg
        self._model = None

    def _ensure_model(self) -> None:
        if self._model is None:
            from openwakeword.model import Model  # type: ignore

            self._model = Model()

    def wait(self, threshold: float = 0.5) -> None:
        """Block until the wake word is heard."""
        import numpy as np
        import sounddevice as sd

        self._ensure_model()
        target = self.cfg.wake_word.lower()
        with sd.InputStream(
            samplerate=SAMPLE_RATE, channels=1, dtype="int16", blocksize=FRAME
        ) as stream:
            while True:
                data, _ = stream.read(FRAME)
                preds = self._model.predict(np.frombuffer(data, dtype=np.int16))
                for label, score in preds.items():
                    if score >= threshold and target in label.lower():
                        return
