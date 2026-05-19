"""Groq speech-to-text adapter."""

from __future__ import annotations

from typing import Any

from ._openai_compatible import transcribe_openai_compatible

API_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
MODELS_URL = "https://console.groq.com/docs/speech-to-text"
PRICING_URL = "https://groq.com/pricing/"
DOCUMENTED_MODELS = {
    "whisper-large-v3-turbo": {"price_per_minute": 0.04 / 60.0},
    "whisper-large-v3": {"price_per_minute": 0.111 / 60.0},
    "distil-whisper-large-v3-en": {"price_per_minute": 0.02 / 60.0},
}


def transcribe(audio_input: Any, model: str = "whisper-large-v3-turbo", **kwargs: Any):
    """Transcribe audio with Groq's OpenAI-compatible STT endpoint."""

    return transcribe_openai_compatible(
        audio_input,
        provider="groq",
        model=model,
        url=API_URL,
        env_var="GROQ_API_KEY",
        price_per_minute_by_model={
            key: value["price_per_minute"] for key, value in DOCUMENTED_MODELS.items()
        },
        **kwargs,
    )


__all__ = ["API_URL", "DOCUMENTED_MODELS", "MODELS_URL", "PRICING_URL", "transcribe"]
