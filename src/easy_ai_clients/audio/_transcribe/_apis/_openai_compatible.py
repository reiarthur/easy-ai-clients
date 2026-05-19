"""Shared OpenAI-compatible speech-to-text adapter helpers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..post_processing import _build_transcription_bundle, build_raw_transcription_payload
from ..pre_processing import build_request_audio
from ._shared import (
    build_utterances_from_segments,
    build_word_record,
    compute_cost_by_duration,
    get_required_api_key,
    request_with_retries,
    response_json,
)


def transcribe_openai_compatible(
    audio_input: Any,
    *,
    provider: str,
    model: str,
    url: str,
    env_var: str,
    headers_extra: Mapping[str, str] | None = None,
    price_per_minute_by_model: Mapping[str, float] | None = None,
    language: str | None = None,
    prompt: str | None = None,
    response_format: str = "verbose_json",
    temperature: float | None = None,
    timestamp_granularities: Any = ("word", "segment"),
    language_mkd: str | bool = "en",
    timeout_seconds: float = 300,
    **kwargs: Any,
) -> dict[str, Any]:
    """Call an OpenAI-compatible multipart transcription endpoint."""

    request_audio = build_request_audio(audio_input)
    api_key = get_required_api_key(env_var)

    form_fields: list[tuple[str, Any]] = [
        ("model", model),
        ("response_format", response_format),
    ]
    for granularity in _normalize_granularities(timestamp_granularities):
        form_fields.append(("timestamp_granularities[]", granularity))
    if language:
        form_fields.append(("language", language))
    if prompt:
        form_fields.append(("prompt", prompt))
    if temperature is not None:
        form_fields.append(("temperature", float(temperature)))
    for key, value in kwargs.items():
        if value not in (None, "", [], {}):
            form_fields.append((key, value))

    headers = {"Authorization": f"Bearer {api_key}"}
    if headers_extra:
        headers.update(dict(headers_extra))

    response = request_with_retries(
        "POST",
        url,
        headers=headers,
        data=form_fields,
        files={
            "file": (
                request_audio["file_name"],
                request_audio["audio_bytes"],
                request_audio["content_type"],
            )
        },
        timeout=(15.0, float(timeout_seconds)),
    )
    payload = response_json(response)
    duration_seconds = payload.get("duration") or request_audio["audio_duration_seconds"]
    raw_payload = _raw_payload_from_response(
        payload,
        provider=provider,
        model=model,
        duration_seconds=duration_seconds,
        fallback_language=language,
    )
    return _build_transcription_bundle(
        raw_payload,
        language_mkd=language_mkd,
        request_id=_request_id(response, payload),
        **_cost_metadata(
            model=model,
            duration_seconds=duration_seconds,
            prices=price_per_minute_by_model or {},
        ),
    )


def _normalize_granularities(value: Any) -> list[str]:
    if value in (None, False):
        return []
    if isinstance(value, str):
        values = [item.strip() for item in value.split(",") if item.strip()]
    else:
        values = [str(item).strip() for item in list(value or []) if str(item).strip()]
    return values or ["segment"]


def _raw_payload_from_response(
    payload: Mapping[str, Any],
    *,
    provider: str,
    model: str,
    duration_seconds: Any,
    fallback_language: str | None,
) -> dict[str, Any]:
    words = []
    for item in payload.get("words") or []:
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

    segments = [item for item in payload.get("segments") or [] if isinstance(item, Mapping)]
    utterances = build_utterances_from_segments(segments, words)
    return build_raw_transcription_payload(
        provider=provider,
        model=model,
        audio_duration_seconds=duration_seconds,
        language=payload.get("language") or fallback_language,
        text=payload.get("text"),
        words=words,
        utterances=utterances,
        provider_metadata={
            "raw_segments": segments,
            "task": payload.get("task"),
            "usage": payload.get("usage"),
            "raw_response": dict(payload),
        },
    )


def _cost_metadata(
    *,
    model: str,
    duration_seconds: Any,
    prices: Mapping[str, float],
) -> dict[str, Any]:
    if model in prices:
        return {
            "cost_usd": compute_cost_by_duration(
                duration_seconds,
                unit_price=float(prices[model]),
                billing_unit="minute",
            ),
            "cost_source": "official_pricing_table",
            "cost_is_estimated": True,
            "cost_lookup_error": None,
            "cost_details": {"billing_unit": "minute", "model": model},
        }
    return {
        "cost_usd": None,
        "cost_source": "unavailable",
        "cost_is_estimated": False,
        "cost_lookup_error": f"No documented pricing metadata is available for {model}.",
        "cost_details": {"model": model},
    }


def _request_id(response: Any, payload: Mapping[str, Any]) -> str | None:
    for key in ("x-request-id", "request-id", "openai-request-id"):
        value = getattr(response, "headers", {}).get(key)
        if value:
            return str(value)
    value = payload.get("id")
    return str(value) if value else None


__all__ = ["transcribe_openai_compatible"]
