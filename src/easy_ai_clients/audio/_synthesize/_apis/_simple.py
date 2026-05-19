"""Small helpers for providers that return one audio payload per request."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..post_processing import _finalize_synthesis_output, build_chunk_record
from ..pre_processing import ensure_env_var
from ._shared import compute_cost_by_characters, request_with_retries, round_cost


def generate_openai_style_speech(
    text: str,
    *,
    provider: str,
    api_url: str,
    env_var: str,
    model: str,
    voice: str,
    response_format: str = "mp3",
    timeout_seconds: float = 180,
    price_per_million_chars: float | None = None,
    extra_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Call an OpenAI Audio Speech-compatible endpoint and normalize audio."""

    api_key = ensure_env_var(env_var)
    payload = {
        "model": model,
        "input": text,
        "voice": voice,
        "response_format": response_format,
    }
    if extra_payload:
        payload.update({key: value for key, value in extra_payload.items() if value is not None})
    response = request_with_retries(
        "POST",
        api_url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json_body=payload,
        timeout=(15.0, float(timeout_seconds)),
    )
    result = _result_from_audio_bytes(
        bytes(response.content or b""),
        audio_format=response_format,
        text=text,
        cost_usd=compute_cost_by_characters(len(text), price_per_million_chars or 0.0)
        if price_per_million_chars is not None
        else 0.0,
        cost_source="official_pricing_table" if price_per_million_chars is not None else "unavailable",
        cost_is_estimated=True if price_per_million_chars is not None else False,
        provider=provider,
        model=model,
        request_id=_header_id(response),
    )
    if price_per_million_chars is None:
        result["warnings"] = f"No documented pricing metadata is available for {provider} model `{model}`."
    return result


def _result_from_audio_bytes(
    audio_bytes: bytes,
    *,
    audio_format: str,
    text: str,
    cost_usd: float,
    cost_source: str,
    cost_is_estimated: bool,
    provider: str,
    model: str,
    request_id: str | None = None,
    audio_type: str = "speech",
    raw_response: Mapping[str, Any] | None = None,
    cost_details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if not audio_bytes:
        raise ValueError(f"{provider} audio request returned an empty audio payload.")
    result = _finalize_synthesis_output(
        [
            build_chunk_record(
                text=text if audio_type == "speech" else "",
                audio_bytes=audio_bytes,
                audio_format=audio_format,
            )
        ],
        cost_usd=round_cost(cost_usd),
    )
    result.update(
        {
            "provider": provider,
            "model": model,
            "request_id": request_id,
            "cost_source": cost_source,
            "cost_is_estimated": bool(cost_is_estimated),
            "cost_details": dict(cost_details or {}),
            "raw_response": dict(raw_response or {}),
            "audio_type": audio_type,
        }
    )
    if audio_type != "speech":
        result["words"] = {}
    return result


def _header_id(response: Any) -> str | None:
    for key in ("x-request-id", "request-id", "x-generation-id"):
        value = getattr(response, "headers", {}).get(key)
        if value:
            return str(value)
    return None


__all__ = ["generate_openai_style_speech", "_result_from_audio_bytes"]
