"""Stability AI Stable Audio adapter."""

from __future__ import annotations

from typing import Any

from ..pre_processing import ensure_env_var
from ._shared import request_with_retries
from ._simple import _result_from_audio_bytes

API_URL = "https://api.stability.ai/v2beta/audio/stable-audio-2.5/text-to-audio"
MODELS_URL = "https://platform.stability.ai/docs/api-reference"
PRICING_URL = "https://platform.stability.ai/pricing"
DOCUMENTED_MODELS = {"stable-audio-2.5": {"usd_per_generation": 0.20}}


def generate(
    text: str,
    model: str = "stable-audio-2.5",
    voice: str | None = None,
    language_code: str = "en",
    **kwargs: Any,
) -> dict[str, Any]:
    """Generate music or sound effects with Stable Audio."""

    api_key = ensure_env_var("STABILITY_API_KEY")
    timeout_seconds = float(kwargs.pop("timeout_seconds", 300))
    output_format = str(kwargs.pop("output_format", "mp3")).strip().lower()
    url = str(kwargs.pop("api_url", API_URL))
    payload = {
        "prompt": text,
        "output_format": output_format,
    }
    payload.update({key: value for key, value in kwargs.items() if value is not None})
    response = request_with_retries(
        "POST",
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": f"audio/{output_format}",
        },
        data=payload,
        timeout=(15.0, timeout_seconds),
    )
    documented = model in DOCUMENTED_MODELS
    return _result_from_audio_bytes(
        bytes(response.content or b""),
        audio_format=output_format,
        text="",
        cost_usd=DOCUMENTED_MODELS.get(model, {}).get("usd_per_generation", 0.0),
        cost_source="official_pricing_table" if documented else "unavailable",
        cost_is_estimated=bool(documented),
        provider="stability",
        model=model,
        request_id=getattr(response, "headers", {}).get("x-request-id"),
        audio_type=str(kwargs.get("audio_type") or "music"),
        cost_details={"language_code": language_code, "voice": voice},
    )


__all__ = ["API_URL", "DOCUMENTED_MODELS", "MODELS_URL", "PRICING_URL", "generate"]
