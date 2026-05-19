"""DeepInfra speech-to-text adapter."""

from __future__ import annotations

from typing import Any

from ._openai_compatible import transcribe_openai_compatible

API_URL = "https://api.deepinfra.com/v1/openai/audio/transcriptions"
MODELS_URL = "https://docs.deepinfra.com/apis/speech-to-text"
PRICING_URL = "https://deepinfra.com/pricing"
DOCUMENTED_MODELS: dict[str, dict[str, float]] = {}


def transcribe(audio_input: Any, model: str = "openai/whisper-large-v3", **kwargs: Any):
    """Transcribe audio through DeepInfra's OpenAI-compatible STT gateway."""

    return transcribe_openai_compatible(
        audio_input,
        provider="deepinfra",
        model=model,
        url=API_URL,
        env_var="DEEPINFRA_API_KEY",
        price_per_minute_by_model={},
        **kwargs,
    )


__all__ = ["API_URL", "DOCUMENTED_MODELS", "MODELS_URL", "PRICING_URL", "transcribe"]
