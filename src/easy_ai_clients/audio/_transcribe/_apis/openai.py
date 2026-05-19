"""OpenAI speech-to-text adapter."""

from __future__ import annotations

from typing import Any

from ._openai_compatible import transcribe_openai_compatible

API_URL = "https://api.openai.com/v1/audio/transcriptions"
MODELS_URL = "https://platform.openai.com/docs/guides/speech-to-text"
PRICING_URL = "https://platform.openai.com/docs/pricing/"
DOCUMENTED_MODELS = {
    "gpt-4o-transcribe": {"price_per_minute": 0.006},
    "gpt-4o-mini-transcribe": {"price_per_minute": 0.003},
    "whisper-1": {"price_per_minute": 0.006},
}


def transcribe(audio_input: Any, model: str = "gpt-4o-mini-transcribe", **kwargs: Any):
    """Transcribe audio with OpenAI's current Audio API."""

    return transcribe_openai_compatible(
        audio_input,
        provider="openai",
        model=model,
        url=API_URL,
        env_var="OPENAI_API_KEY",
        price_per_minute_by_model={
            key: value["price_per_minute"] for key, value in DOCUMENTED_MODELS.items()
        },
        **kwargs,
    )


__all__ = ["API_URL", "DOCUMENTED_MODELS", "MODELS_URL", "PRICING_URL", "transcribe"]
