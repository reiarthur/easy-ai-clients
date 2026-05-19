"""Runway audio generation adapter."""

from __future__ import annotations

from typing import Any

import requests

from ....video._shared import (
    extract_video_url,
    require_env,
    runway_submit,
    runway_wait_for_task,
)
from ._simple import _result_from_audio_bytes

SOUND_EFFECT_URL = "/v1/sound_effect"
TEXT_TO_SPEECH_URL = "/v1/text_to_speech"
MODELS_URL = "https://docs.dev.runwayml.com/guides/models/"
PRICING_URL = "https://docs.dev.runwayml.com/guides/pricing/"
CREDIT_TO_USD = 0.01


def generate(
    text: str,
    model: str = "eleven_text_to_sound_v2",
    voice: str = "clara",
    language_code: str = "en",
    **kwargs: Any,
) -> dict[str, Any]:
    """Generate Runway speech or sound effects from text."""

    api_key = require_env("RUNWAYML_API_SECRET", "Runway")
    audio_type = str(kwargs.pop("audio_type", "sound_effect")).strip().lower()
    sync = bool(kwargs.pop("sync", True))
    timeout_seconds = float(kwargs.pop("timeout_seconds", 900))
    duration = kwargs.pop("duration", kwargs.pop("duration_seconds", None))
    output_format = str(kwargs.pop("output_format", "mp3")).strip().lower()
    if audio_type in {"speech", "tts", "text_to_speech"} or model == "eleven_multilingual_v2":
        endpoint = TEXT_TO_SPEECH_URL
        payload: dict[str, Any] = {
            "model": model,
            "text": text,
            "voice": {"type": "runway-preset", "presetId": voice},
            "languageCode": language_code,
        }
        cost = _speech_cost(text)
        normalized_audio_type = "speech"
    else:
        endpoint = SOUND_EFFECT_URL
        payload = {"model": model, "promptText": text}
        if duration is not None:
            payload["duration"] = float(duration)
        cost = _sound_cost(duration)
        normalized_audio_type = "sound_effect"
    payload.update({key: value for key, value in kwargs.items() if value is not None})
    raw = runway_submit(endpoint, payload, api_key, timeout_seconds=timeout_seconds)
    request_id = raw.get("id") or raw.get("task_id") or raw.get("request_id")
    if not sync:
        return {
            "provider": "runway",
            "model": model,
            "request_id": request_id,
            "status": "submitted",
            "cost_usd": cost,
            "cost_currency": "USD",
            "cost_source": "official_pricing_table",
            "cost_is_estimated": True,
            "cost_details": {"credits": cost / CREDIT_TO_USD},
            "audio": None,
            "words": {},
            "raw_response": raw,
            "audio_type": normalized_audio_type,
        }
    final = runway_wait_for_task(request_id, api_key, timeout_seconds=timeout_seconds)
    audio_url = extract_video_url(final) or extract_video_url(raw)
    if not audio_url:
        raise RuntimeError(f"Runway audio task {request_id} did not return an output URL.")
    audio_bytes = _download_bytes(audio_url, timeout_seconds=timeout_seconds)
    return _result_from_audio_bytes(
        audio_bytes,
        audio_format=output_format,
        text=text,
        cost_usd=cost,
        cost_source="official_pricing_table",
        cost_is_estimated=True,
        provider="runway",
        model=model,
        request_id=request_id,
        audio_type=normalized_audio_type,
        raw_response=final,
        cost_details={"credits": cost / CREDIT_TO_USD},
    )


def _speech_cost(text: str) -> float:
    credits = max(1, -(-len(str(text or "")) // 50))
    return round(float(credits) * CREDIT_TO_USD, 6)


def _sound_cost(duration: Any) -> float:
    if duration is None:
        credits = 2.0
    else:
        credits = max(1.0, float(duration))
    return round(float(credits) * CREDIT_TO_USD, 6)


def _download_bytes(url: str, *, timeout_seconds: float) -> bytes:
    response = requests.get(url, timeout=float(timeout_seconds))
    if response.status_code >= 400:
        raise RuntimeError(f"Runway audio download failed with HTTP {response.status_code}.")
    return bytes(response.content or b"")


__all__ = [
    "CREDIT_TO_USD",
    "MODELS_URL",
    "PRICING_URL",
    "SOUND_EFFECT_URL",
    "TEXT_TO_SPEECH_URL",
    "generate",
]
