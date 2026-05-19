"""Hugging Face Inference Providers ASR adapter."""

from __future__ import annotations

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

API_URL_TEMPLATE = "https://api-inference.huggingface.co/models/{model}"
MODELS_URL = "https://huggingface.co/docs/inference-providers/tasks/automatic-speech-recognition"
PRICING_URL = "https://huggingface.co/pricing"


def transcribe(
    audio_input: Any,
    model: str = "openai/whisper-large-v3",
    *,
    language: str | None = None,
    language_mkd: str | bool = "en",
    timeout_seconds: float = 300,
    **kwargs: Any,
):
    """Transcribe audio using the official Hugging Face Inference API surface."""

    request_audio = build_request_audio(audio_input)
    api_key = get_required_api_key("HUGGINGFACE_API_KEY")
    response = request_with_retries(
        "POST",
        API_URL_TEMPLATE.format(model=model),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": request_audio["content_type"],
        },
        data=request_audio["audio_bytes"],
        params={key: value for key, value in kwargs.items() if value not in (None, "", [], {})},
        timeout=(15.0, float(timeout_seconds)),
    )
    raw = response_json(response)
    words = _words_from_payload(raw)
    segments = [item for item in raw.get("chunks") or raw.get("segments") or [] if isinstance(item, Mapping)]
    raw_payload = build_raw_transcription_payload(
        provider="huggingface",
        model=model,
        audio_duration_seconds=request_audio["audio_duration_seconds"],
        language=raw.get("language") or language,
        text=raw.get("text") or raw.get("transcription"),
        words=words,
        utterances=build_utterances_from_segments(segments, words),
        provider_metadata={"raw_segments": segments, "raw_response": raw},
    )
    return _build_transcription_bundle(
        raw_payload,
        language_mkd=language_mkd,
        request_id=getattr(response, "headers", {}).get("x-request-id"),
        cost_usd=None,
        cost_source="unavailable",
        cost_is_estimated=False,
        cost_lookup_error="Hugging Face ASR response did not include a provider-independent USD cost.",
        cost_details={},
    )


def _words_from_payload(raw: Mapping[str, Any]) -> list[dict[str, Any]]:
    words = []
    for item in raw.get("words") or raw.get("chunks") or []:
        if not isinstance(item, Mapping):
            continue
        timestamp = item.get("timestamp") or item.get("timestamps") or []
        start = item.get("start")
        end = item.get("end")
        if isinstance(timestamp, list | tuple) and len(timestamp) >= 2:
            start, end = timestamp[0], timestamp[1]
        word = build_word_record(item.get("word") or item.get("text"), start, end)
        if word:
            words.append(word)
    return words


__all__ = ["API_URL_TEMPLATE", "MODELS_URL", "PRICING_URL", "transcribe"]
