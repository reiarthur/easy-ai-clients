"""OpenRouter speech-to-text adapter."""

from __future__ import annotations

import base64
from collections.abc import Mapping
from typing import Any

from ..post_processing import _build_transcription_bundle, build_raw_transcription_payload
from ..pre_processing import build_request_audio
from ._shared import (
    build_utterances_from_segments,
    build_word_record,
    get_required_api_key,
    request_with_retries,
    response_json,
)

API_URL = "https://openrouter.ai/api/v1/audio/transcriptions"
MODELS_URL = "https://openrouter.ai/docs/models"
PRICING_URL = "https://openrouter.ai/docs/models"


def transcribe(
    audio_input: Any,
    model: str = "openai/whisper-large-v3",
    *,
    language: str | None = None,
    provider: Mapping[str, Any] | None = None,
    temperature: float | None = None,
    language_mkd: str | bool = "en",
    timeout_seconds: float = 300,
    **kwargs: Any,
):
    """Transcribe audio through OpenRouter's dedicated STT endpoint."""

    request_audio = build_request_audio(audio_input)
    api_key = get_required_api_key("OPENROUTER_API_KEY")
    audio_format = str(request_audio.get("upload_format") or "wav").lower()
    payload: dict[str, Any] = {
        "model": model,
        "input_audio": {
            "data": base64.b64encode(request_audio["audio_bytes"]).decode("ascii"),
            "format": audio_format,
        },
    }
    if language:
        payload["language"] = language
    if provider:
        payload["provider"] = dict(provider)
    if temperature is not None:
        payload["temperature"] = float(temperature)
    payload.update({key: value for key, value in kwargs.items() if value not in (None, "", [], {})})

    response = request_with_retries(
        "POST",
        API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json_body=payload,
        timeout=(15.0, float(timeout_seconds)),
    )
    raw = response_json(response)
    words = _words_from_payload(raw)
    segments = [item for item in raw.get("segments") or [] if isinstance(item, Mapping)]
    raw_payload = build_raw_transcription_payload(
        provider="openrouter",
        model=model,
        audio_duration_seconds=_duration_seconds(raw, request_audio),
        language=raw.get("language") or language,
        text=raw.get("text"),
        words=words,
        utterances=build_utterances_from_segments(segments, words),
        provider_metadata={
            "usage": raw.get("usage"),
            "raw_segments": segments,
            "raw_response": raw,
        },
    )
    return _build_transcription_bundle(
        raw_payload,
        language_mkd=language_mkd,
        request_id=_request_id(response, raw),
        **_cost_metadata(raw),
    )


def _words_from_payload(raw: Mapping[str, Any]) -> list[dict[str, Any]]:
    words = []
    for item in raw.get("words") or []:
        if not isinstance(item, Mapping):
            continue
        word = build_word_record(
            item.get("word") or item.get("text"),
            item.get("start"),
            item.get("end"),
            speaker=item.get("speaker") or item.get("speaker_id"),
        )
        if word:
            words.append(word)
    return words


def _duration_seconds(raw: Mapping[str, Any], request_audio: Mapping[str, Any]) -> Any:
    usage = raw.get("usage") or {}
    if isinstance(usage, Mapping) and usage.get("seconds") is not None:
        return usage["seconds"]
    return raw.get("duration") or request_audio["audio_duration_seconds"]


def _cost_metadata(raw: Mapping[str, Any]) -> dict[str, Any]:
    usage = raw.get("usage") or {}
    if isinstance(usage, Mapping) and usage.get("cost") is not None:
        return {
            "cost_usd": float(usage["cost"]),
            "cost_source": "provider_response",
            "cost_is_estimated": False,
            "cost_lookup_error": None,
            "cost_details": {"usage": dict(usage)},
        }
    return {
        "cost_usd": None,
        "cost_source": "unavailable",
        "cost_is_estimated": False,
        "cost_lookup_error": "OpenRouter transcription response did not include usage.cost.",
        "cost_details": {"usage": dict(usage) if isinstance(usage, Mapping) else {}},
    }


def _request_id(response: Any, payload: Mapping[str, Any]) -> str | None:
    for key in ("x-request-id", "request-id", "x-generation-id"):
        value = getattr(response, "headers", {}).get(key)
        if value:
            return str(value)
    value = payload.get("id")
    return str(value) if value else None


__all__ = ["API_URL", "MODELS_URL", "PRICING_URL", "transcribe"]
