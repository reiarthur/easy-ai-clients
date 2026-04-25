"""OpenAI text-to-speech adapter with centralized post-alignment.

Last updated: 2026-04-22
"""

from __future__ import annotations

from typing import Any

from .._apis._shared import (
    compute_cost_by_characters,
    compute_cost_by_minutes,
    normalize_language_code,
    reject_unknown_kwargs,
    request_with_retries,
    round_cost,
    validate_choice,
    validate_number_range,
)
from ..post_processing import _finalize_synthesis_output, build_aligned_chunk_record
from ..pre_processing import chunk_text_for_provider, ensure_env_var, resolve_locale

API_URL = "https://api.openai.com/v1/audio/speech"
MODELS_URL = "https://platform.openai.com/docs/api-reference/audio/create-speech"
CATALOG_URL = "https://platform.openai.com/docs/models/gpt-4o-mini-tts"
PRICING_URL = "https://platform.openai.com/docs/pricing/"

SUPPORTED_MODELS = {
    "tts-1": {
        "pricing_mode": "characters",
        "usd_per_million_chars": 15.0,
        "operational_char_limit": 1800,
        "voice_set": "classic",
    },
    "tts-1-1106": {
        "pricing_mode": "characters",
        "usd_per_million_chars": 15.0,
        "operational_char_limit": 1800,
        "voice_set": "classic",
    },
    "tts-1-hd": {
        "pricing_mode": "characters",
        "usd_per_million_chars": 30.0,
        "operational_char_limit": 1800,
        "voice_set": "classic",
    },
    "tts-1-hd-1106": {
        "pricing_mode": "characters",
        "usd_per_million_chars": 30.0,
        "operational_char_limit": 1800,
        "voice_set": "classic",
    },
    "gpt-4o-mini-tts": {
        "pricing_mode": "estimated_minutes",
        "usd_per_minute_estimate": 0.015,
        "operational_char_limit": 1800,
        "voice_set": "omni",
    },
    "gpt-4o-mini-tts-2025-03-20": {
        "pricing_mode": "estimated_minutes",
        "usd_per_minute_estimate": 0.015,
        "operational_char_limit": 1800,
        "voice_set": "omni",
    },
    "gpt-4o-mini-tts-2025-12-15": {
        "pricing_mode": "estimated_minutes",
        "usd_per_minute_estimate": 0.015,
        "operational_char_limit": 1800,
        "voice_set": "omni",
    },
}

CLASSIC_VOICES = {"alloy", "ash", "coral", "echo", "fable", "nova", "onyx", "sage", "shimmer"}
OMNI_VOICES = CLASSIC_VOICES | {"ballad", "verse", "marin", "cedar"}
RESPONSE_FORMATS = {"mp3", "opus", "aac", "flac", "wav", "pcm"}
STREAM_FORMATS = {"audio", "sse"}
SUPPORTED_KWARGS = {
    "response_format",
    "speed",
    "instructions",
    "stream_format",
    "timeout_seconds",
}


def generate(
    text: str,
    model: str = "tts-1",
    voice: str = "alloy",
    language_code: str = "en",
    **kwargs: Any,
) -> dict[str, Any]:
    """Generate speech with OpenAI TTS. See `synthesize/docs/openai.md`."""
    if model not in SUPPORTED_MODELS:
        supported = ", ".join(sorted(SUPPORTED_MODELS))
        raise ValueError(f"Unsupported OpenAI TTS model '{model}'. Supported models: {supported}.")

    options = reject_unknown_kwargs("OpenAI", model, kwargs, SUPPORTED_KWARGS)
    response_format = str(options.pop("response_format", "mp3")).strip().lower()
    speed = validate_number_range(
        options.pop("speed", 1.0),
        parameter_name="speed",
        provider="OpenAI",
        model=model,
        minimum=0.25,
        maximum=4.0,
    )
    instructions = options.pop("instructions", None)
    stream_format = str(options.pop("stream_format", "audio")).strip().lower()
    timeout_seconds = float(options.pop("timeout_seconds", 180.0))

    validate_choice(response_format, RESPONSE_FORMATS, parameter_name="response_format", provider="OpenAI", model=model)
    validate_choice(stream_format, STREAM_FORMATS, parameter_name="stream_format", provider="OpenAI", model=model)
    if stream_format == "sse":
        if model.startswith("tts-1"):
            raise ValueError("OpenAI stream_format='sse' is not supported by tts-1 or tts-1-hd models.")
        raise ValueError("OpenAI stream_format='sse' is not supported by this repository's AudioSegment return contract.")
    allowed_voices = CLASSIC_VOICES if SUPPORTED_MODELS[model]["voice_set"] == "classic" else OMNI_VOICES
    validate_choice(str(voice), allowed_voices, parameter_name="voice", provider="OpenAI", model=model)
    if instructions and SUPPORTED_MODELS[model]["voice_set"] == "classic":
        raise ValueError(f"OpenAI instructions are not supported for model '{model}'.")

    api_key = ensure_env_var("OPENAI_API_KEY")
    model_config = SUPPORTED_MODELS[model]
    text_chunks = chunk_text_for_provider(text, model_config["operational_char_limit"])
    resolved_locale = resolve_locale(normalize_language_code(language_code))

    chunk_records: list[dict[str, Any]] = []
    alignment_cost_usd = 0.0
    tts_character_cost_usd = 0.0
    for chunk_text in text_chunks:
        payload: dict[str, Any] = {
            "model": model,
            "input": chunk_text,
            "voice": voice,
            "response_format": response_format,
            "speed": speed,
        }
        if instructions:
            payload["instructions"] = instructions

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
        audio_bytes = bytes(response.content or b"")
        if not audio_bytes:
            raise ValueError("OpenAI TTS returned an empty audio payload.")

        chunk_record, chunk_alignment_cost = build_aligned_chunk_record(
            text=chunk_text,
            audio_bytes=audio_bytes,
            audio_format=response_format,
            language=resolved_locale,
        )
        chunk_records.append(chunk_record)
        alignment_cost_usd += chunk_alignment_cost

        if model_config["pricing_mode"] == "characters":
            tts_character_cost_usd += compute_cost_by_characters(
                len(chunk_text),
                model_config["usd_per_million_chars"],
            )

    result = _finalize_synthesis_output(chunk_records, cost_usd=0.0)
    if model_config["pricing_mode"] == "characters":
        tts_cost_usd = tts_character_cost_usd
    else:
        tts_cost_usd = compute_cost_by_minutes(
            len(result["audio"]) / 1000.0,
            model_config["usd_per_minute_estimate"],
        )
    result["cost_usd"] = round_cost(tts_cost_usd + alignment_cost_usd)
    return result


__all__ = [
    "API_URL",
    "CATALOG_URL",
    "MODELS_URL",
    "PRICING_URL",
    "RESPONSE_FORMATS",
    "SUPPORTED_MODELS",
    "generate",
]
