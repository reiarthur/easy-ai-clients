"""xAI speech-to-text adapter."""

from __future__ import annotations

from typing import Any

from ._openai_compatible import transcribe_openai_compatible

API_URL = "https://api.x.ai/v1/stt"
MODELS_URL = "https://docs.x.ai/developers/models/speech-to-text"
PRICING_URL = "https://docs.x.ai/developers/models/speech-to-text"
DOCUMENTED_MODELS = {
    "speech-to-text": {"price_per_minute": 0.10 / 60.0},
}


def transcribe(audio_input: Any, model: str = "speech-to-text", **kwargs: Any):
    """Transcribe audio with xAI batch STT."""

    return transcribe_openai_compatible(
        audio_input,
        provider="xai",
        model=model,
        url=API_URL,
        env_var="XAI_API_KEY",
        price_per_minute_by_model={
            key: value["price_per_minute"] for key, value in DOCUMENTED_MODELS.items()
        },
        **kwargs,
    )


__all__ = ["API_URL", "DOCUMENTED_MODELS", "MODELS_URL", "PRICING_URL", "transcribe"]
