"""Google Gemini audio-understanding transcription adapter."""

from __future__ import annotations

import base64
from collections.abc import Mapping
from typing import Any

from ..post_processing import _build_transcription_bundle, build_raw_transcription_payload
from ..pre_processing import build_request_audio
from ._shared import get_required_api_key, request_with_retries, response_json

API_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
MODELS_URL = "https://ai.google.dev/gemini-api/docs/audio"
PRICING_URL = "https://ai.google.dev/gemini-api/docs/pricing"
DEFAULT_PROMPT = "Transcribe this audio. Return only the transcript text."


def transcribe(
    audio_input: Any,
    model: str = "gemini-2.5-flash",
    *,
    prompt: str | None = None,
    language: str | None = None,
    language_mkd: str | bool = "en",
    timeout_seconds: float = 300,
    **kwargs: Any,
):
    """Transcribe audio using Gemini audio understanding."""

    request_audio = build_request_audio(audio_input)
    api_key = get_required_api_key("GOOGLE_API_KEY")
    instruction = str(prompt or DEFAULT_PROMPT)
    if language:
        instruction = f"{instruction}\nExpected language: {language}."
    payload: dict[str, Any] = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": instruction},
                    {
                        "inlineData": {
                            "mimeType": request_audio["content_type"],
                            "data": base64.b64encode(request_audio["audio_bytes"]).decode("ascii"),
                        }
                    },
                ],
            }
        ]
    }
    payload.update({key: value for key, value in kwargs.items() if value not in (None, "", [], {})})
    response = request_with_retries(
        "POST",
        API_URL_TEMPLATE.format(model=model),
        headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
        json_body=payload,
        timeout=(15.0, float(timeout_seconds)),
    )
    raw = response_json(response)
    text = _extract_text(raw)
    raw_payload = build_raw_transcription_payload(
        provider="google",
        model=model,
        audio_duration_seconds=request_audio["audio_duration_seconds"],
        language=language,
        text=text,
        provider_metadata={
            "usage": raw.get("usageMetadata"),
            "raw_response": raw,
        },
    )
    return _build_transcription_bundle(
        raw_payload,
        language_mkd=language_mkd,
        request_id=getattr(response, "headers", {}).get("x-request-id"),
        cost_usd=None,
        cost_source="unavailable",
        cost_is_estimated=False,
        cost_lookup_error=(
            "Gemini audio transcription is billed as multimodal model usage; "
            "this adapter does not infer USD cost without provider usage pricing."
        ),
        cost_details={"usage": raw.get("usageMetadata") or {}},
    )


def _extract_text(raw: Mapping[str, Any]) -> str:
    text_parts: list[str] = []
    for candidate in raw.get("candidates") or []:
        if not isinstance(candidate, Mapping):
            continue
        content = candidate.get("content") or {}
        for part in content.get("parts") or []:
            if isinstance(part, Mapping) and part.get("text"):
                text_parts.append(str(part["text"]))
    return "\n".join(part.strip() for part in text_parts if part.strip()).strip()


__all__ = ["API_URL_TEMPLATE", "DEFAULT_PROMPT", "MODELS_URL", "PRICING_URL", "transcribe"]
