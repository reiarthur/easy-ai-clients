"""Deepgram Aura text-to-speech adapter."""

from __future__ import annotations

from typing import Any

from ..pre_processing import ensure_env_var
from ._shared import compute_cost_by_characters, request_with_retries, round_cost
from ._simple import _result_from_audio_bytes

API_URL = "https://api.deepgram.com/v1/speak"
MODELS_URL = "https://developers.deepgram.com/docs/text-to-speech"
PRICING_URL = "https://deepgram.com/pricing"
DOCUMENTED_MODELS = {
    "aura-2-thalia-en": {"price_per_million_chars": 30.0},
}


def generate(
    text: str,
    model: str = "aura-2-thalia-en",
    voice: str | None = None,
    language_code: str = "en",
    **kwargs: Any,
) -> dict[str, Any]:
    """Generate speech with Deepgram Aura TTS."""

    api_key = ensure_env_var("DEEPGRAM_API_KEY")
    response_format = str(kwargs.pop("response_format", "mp3")).strip().lower()
    timeout_seconds = float(kwargs.pop("timeout_seconds", 180))
    params = {"model": voice or model}
    if response_format:
        params["encoding"] = response_format
    params.update({key: value for key, value in kwargs.pop("params", {}).items() if value is not None})
    payload = {"text": text}
    payload.update({key: value for key, value in kwargs.items() if value is not None})
    response = request_with_retries(
        "POST",
        API_URL,
        headers={"Authorization": f"Token {api_key}", "Content-Type": "application/json"},
        params=params,
        json_body=payload,
        timeout=(15.0, timeout_seconds),
    )
    documented = model in DOCUMENTED_MODELS
    price = DOCUMENTED_MODELS.get(model, {}).get("price_per_million_chars", 0.0)
    return _result_from_audio_bytes(
        bytes(response.content or b""),
        audio_format=response_format,
        text=text,
        cost_usd=round_cost(compute_cost_by_characters(len(text), price)) if documented else 0.0,
        cost_source="official_pricing_table" if documented else "unavailable",
        cost_is_estimated=bool(documented),
        provider="deepgram",
        model=model,
        request_id=getattr(response, "headers", {}).get("x-request-id"),
        cost_details={"characters": len(text), "language_code": language_code},
    )


__all__ = ["API_URL", "DOCUMENTED_MODELS", "MODELS_URL", "PRICING_URL", "generate"]
