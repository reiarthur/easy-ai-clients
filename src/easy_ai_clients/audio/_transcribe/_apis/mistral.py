"""Mistral Voxtral transcription adapter."""

from __future__ import annotations

from typing import Any

from ._openai_compatible import transcribe_openai_compatible

API_URL = "https://api.mistral.ai/v1/audio/transcriptions"
MODELS_URL = "https://docs.mistral.ai/capabilities/audio/"
PRICING_URL = "https://mistral.ai/products/la-plateforme#pricing"
DOCUMENTED_MODELS: dict[str, dict[str, float]] = {}


def transcribe(audio_input: Any, model: str = "voxtral-mini-latest", **kwargs: Any):
    """Transcribe audio with Mistral's Voxtral Audio API.

    Mistral publishes model availability separately from a deterministic USD
    per-minute table, so the wrapper keeps cost as unavailable unless the
    provider response later exposes usage metadata.
    """

    return transcribe_openai_compatible(
        audio_input,
        provider="mistral",
        model=model,
        url=API_URL,
        env_var="MISTRAL_API_KEY",
        price_per_minute_by_model={},
        **kwargs,
    )


__all__ = ["API_URL", "DOCUMENTED_MODELS", "MODELS_URL", "PRICING_URL", "transcribe"]
