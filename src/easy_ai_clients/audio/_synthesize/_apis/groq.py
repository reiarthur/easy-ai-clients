"""Groq text-to-speech adapter."""

from __future__ import annotations

from typing import Any

from ._simple import generate_openai_style_speech

API_URL = "https://api.groq.com/openai/v1/audio/speech"
MODELS_URL = "https://console.groq.com/docs/text-to-speech"
PRICING_URL = "https://groq.com/pricing/"


def generate(
    text: str,
    model: str = "playai-tts",
    voice: str = "Fritz-PlayAI",
    language_code: str = "en",
    **kwargs: Any,
) -> dict[str, Any]:
    """Generate speech through Groq's OpenAI-compatible speech endpoint."""

    response_format = str(kwargs.pop("response_format", "mp3")).strip().lower()
    timeout_seconds = float(kwargs.pop("timeout_seconds", 180))
    payload = {"language": language_code}
    payload.update(kwargs)
    return generate_openai_style_speech(
        text,
        provider="groq",
        api_url=API_URL,
        env_var="GROQ_API_KEY",
        model=model,
        voice=voice,
        response_format=response_format,
        timeout_seconds=timeout_seconds,
        price_per_million_chars=None,
        extra_payload=payload,
    )


__all__ = ["API_URL", "MODELS_URL", "PRICING_URL", "generate"]
