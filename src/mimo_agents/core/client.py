"""MiMo API client wrapper using OpenAI-compatible interface."""

from __future__ import annotations

from typing import Any

from openai import OpenAI

from mimo_agents.core.config import ModelConfig, Settings
from mimo_agents.core.models import TokenUsage


class MiMoClient:
    """Client for interacting with MiMo API via OpenAI-compatible endpoint."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = OpenAI(
            api_key=settings.api_key,
            base_url=settings.base_url,
        )
        self._total_usage = TokenUsage()

    def chat(
        self,
        messages: list[dict[str, Any]],
        model_config: ModelConfig | None = None,
        tools: list[dict[str, Any]] | None = None,
        response_format: dict[str, str] | None = None,
    ) -> tuple[str, TokenUsage]:
        """Send a chat completion request to MiMo API."""
        config = model_config or self.settings.reasoning_model

        kwargs: dict[str, Any] = {
            "model": config.model_id,
            "messages": messages,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "top_p": config.top_p,
        }
        if tools:
            kwargs["tools"] = tools
        if response_format:
            kwargs["response_format"] = response_format

        response = self._client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content or ""
        usage = TokenUsage(
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
            total_tokens=response.usage.total_tokens if response.usage else 0,
            model=config.model_id,
        )
        self._accumulate(usage)

        return content, usage

    def chat_with_vision(
        self,
        text_prompt: str,
        image_url: str | None = None,
        image_base64: str | None = None,
    ) -> tuple[str, TokenUsage]:
        """Send a multimodal request with image understanding."""
        content_parts: list[dict[str, Any]] = [{"type": "text", "text": text_prompt}]

        if image_url:
            content_parts.append({
                "type": "image_url",
                "image_url": {"url": image_url},
            })
        elif image_base64:
            content_parts.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image_base64}"},
            })

        messages = [{"role": "user", "content": content_parts}]
        return self.chat(messages, model_config=self.settings.multimodal_model)

    def text_to_speech(self, text: str, voice: str = "alloy") -> tuple[str, TokenUsage]:
        """Generate speech from text using MiMo TTS model."""
        messages = [
            {
                "role": "system",
                "content": f"You are a voice narrator. Use voice: {voice}. "
                "Read the following text naturally and expressively.",
            },
            {"role": "user", "content": text},
        ]
        return self.chat(messages, model_config=self.settings.tts_model)

    def get_total_usage(self) -> TokenUsage:
        return self._total_usage

    def _accumulate(self, usage: TokenUsage) -> None:
        self._total_usage.prompt_tokens += usage.prompt_tokens
        self._total_usage.completion_tokens += usage.completion_tokens
        self._total_usage.total_tokens += usage.total_tokens
