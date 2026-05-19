"""OpenRouter text-to-speech adapter."""

from __future__ import annotations

from typing import Any

from ._simple import generate_openai_style_speech

API_URL = "https://openrouter.ai/api/v1/audio/speech"
MODELS_URL = "https://openrouter.ai/docs/guides/overview/multimodal/tts"
PRICING_URL = "https://openrouter.ai/docs/models"


def generate(
    text: str,
    model: str = "openai/gpt-4o-mini-tts-2025-12-15",
    voice: str = "alloy",
    language_code: str = "en",
    **kwargs: Any,
) -> dict[str, Any]:
    """Generate speech through OpenRouter's dedicated speech endpoint."""

    response_format = str(kwargs.pop("response_format", "mp3")).strip().lower()
    timeout_seconds = float(kwargs.pop("timeout_seconds", 180))
    provider_options = kwargs.pop("provider", None)
    payload = {"provider": provider_options} if provider_options else {}
    payload["language"] = language_code
    payload.update(kwargs)
    return generate_openai_style_speech(
        text,
        provider="openrouter",
        api_url=API_URL,
        env_var="OPENROUTER_API_KEY",
        model=model,
        voice=voice,
        response_format=response_format,
        timeout_seconds=timeout_seconds,
        price_per_million_chars=None,
        extra_payload=payload,
    )


__all__ = ["API_URL", "MODELS_URL", "PRICING_URL", "generate"]
