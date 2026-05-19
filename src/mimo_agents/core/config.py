"""Configuration management for MiMo Multi-Agent DevAssistant."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class ModelConfig:
    """Configuration for a specific MiMo model."""

    model_id: str
    max_tokens: int = 8192
    temperature: float = 0.7
    top_p: float = 0.9


@dataclass
class Settings:
    """Application settings loaded from environment variables."""

    api_key: str = field(default_factory=lambda: os.getenv("MIMO_API_KEY", ""))
    base_url: str = field(
        default_factory=lambda: os.getenv(
            "MIMO_BASE_URL", "https://api.xiaomimimo.com/v1"
        )
    )
    reasoning_model: ModelConfig = field(
        default_factory=lambda: ModelConfig(
            model_id=os.getenv("MIMO_REASONING_MODEL", "MiMo-V2.5-Pro"),
            max_tokens=16384,
            temperature=0.3,
        )
    )
    multimodal_model: ModelConfig = field(
        default_factory=lambda: ModelConfig(
            model_id=os.getenv("MIMO_MULTIMODAL_MODEL", "MiMo-V2.5"),
            max_tokens=8192,
            temperature=0.5,
        )
    )
    tts_model: ModelConfig = field(
        default_factory=lambda: ModelConfig(
            model_id=os.getenv("MIMO_TTS_MODEL", "MiMo-V2.5-TTS"),
            max_tokens=4096,
            temperature=0.8,
        )
    )
    max_agent_iterations: int = 10
    enable_voice: bool = False
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> Settings:
        return cls()

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.api_key:
            errors.append("MIMO_API_KEY environment variable is required")
        return errors
