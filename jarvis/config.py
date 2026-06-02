"""Load and validate Jarvis configuration from config.yaml."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class BrainConfig(BaseModel):
    host: str = "http://localhost:11434"
    model: str = "llama3.1"
    max_tool_iterations: int = 5


class AssistantConfig(BaseModel):
    name: str = "Jarvis"
    persona: str = "polite"


class VoiceConfig(BaseModel):
    enabled: bool = True
    wake_word: str = "jarvis"
    stt_model: str = "base.en"
    tts_engine: str = "pyttsx3"
    piper_voice: str = ""


class SkillsConfig(BaseModel):
    system_control: bool = True
    files: bool = True
    web: bool = True
    productivity: bool = True
    file_roots: list[str] = Field(default_factory=list)
    data_dir: str = "~/.jarvis"


class SafetyConfig(BaseModel):
    confirm_actions: list[str] = Field(default_factory=list)
    blocked_actions: list[str] = Field(default_factory=list)


class Config(BaseModel):
    brain: BrainConfig = Field(default_factory=BrainConfig)
    assistant: AssistantConfig = Field(default_factory=AssistantConfig)
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    skills: SkillsConfig = Field(default_factory=SkillsConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)

    @property
    def data_path(self) -> Path:
        """Resolved data directory, created on first access."""
        p = Path(os.path.expanduser(self.skills.data_dir))
        p.mkdir(parents=True, exist_ok=True)
        return p

    def resolved_file_roots(self) -> list[Path]:
        """File roots that file skills may touch (defaults to the home directory)."""
        if not self.skills.file_roots:
            return [Path.home()]
        return [Path(os.path.expanduser(r)).resolve() for r in self.skills.file_roots]


def load_config(path: str | os.PathLike | None = None) -> Config:
    """Load config from the given path, or config.yaml at the project root."""
    if path is None:
        path = Path(__file__).resolve().parent.parent / "config.yaml"
    path = Path(path)
    if not path.exists():
        return Config()
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return Config(**data)
