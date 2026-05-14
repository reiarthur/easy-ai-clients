"""Together AI TTS adapter using streaming word alignment.

Last updated: 2026-04-22
"""

from __future__ import annotations

from typing import Any

from .._apis._shared import (
    collect_sse_events,
    compute_cost_by_characters,
    normalize_language_code,
    pcm_to_wav_bytes,
    reject_unknown_kwargs,
    request_with_retries,
    round_cost,
    validate_choice,
)
from ..post_processing import (
    _finalize_synthesis_output,
    build_aligned_chunk_record,
    build_chunk_record,
)
from ..pre_processing import (
    chunk_text_for_provider,
    decode_base64_bytes,
    ensure_env_var,
    resolve_language_code,
    resolve_locale,
)

API_URL = "https://api.together.xyz/v1/audio/speech"
VOICES_URL = "https://api.together.xyz/v1/voices"
GUIDE_URL = "https://docs.together.ai/docs/text-to-speech"
CATALOG_URL = "https://docs.together.ai/docs/serverless-models"
PRICING_URL = "https://docs.together.ai/docs/serverless-models"

DOCUMENTED_MODELS = {
    "canopylabs/orpheus-3b-0.1-ft": {
        "usd_per_million_chars": 15.0,
        "default_voice": "tara",
        "operational_char_limit": 2000,
    },
    "hexgrad/Kokoro-82M": {
        "usd_per_million_chars": 4.0,
        "default_voice": "af_alloy",
        "operational_char_limit": 2000,
    },
    "cartesia/sonic-2": {
        "usd_per_million_chars": 65.0,
        "default_voice": "laidback woman",
        "operational_char_limit": 2000,
    },
    "cartesia/sonic-3": {
        "usd_per_million_chars": 65.0,
        "default_voice": "laidback woman",
        "operational_char_limit": 2000,
    },
    "cartesia/sonic": {
        "usd_per_million_chars": 65.0,
        "default_voice": "laidback woman",
        "operational_char_limit": 2000,
    },
    "deepgram/aura-2": {
        "usd_per_million_chars": 0.0,
        "default_voice": "aura-2-thalia-en",
        "operational_char_limit": 2000,
    },
    "rime-labs/rime-mist-v2": {
        "usd_per_million_chars": 0.0,
        "default_voice": "astra",
        "operational_char_limit": 2000,
    },
    "rime-labs/rime-arcana-v2": {
        "usd_per_million_chars": 0.27,
        "default_voice": "astra",
        "operational_char_limit": 2000,
    },
    "rime-labs/rime-arcana-v3": {
        "usd_per_million_chars": 0.0,
        "default_voice": "astra",
        "operational_char_limit": 2000,
    },
    "rime-labs/rime-arcana-v3-turbo": {
        "usd_per_million_chars": 0.0,
        "default_voice": "astra",
        "operational_char_limit": 2000,
    },
    "minimax/speech-2.6-turbo": {
        "usd_per_million_chars": 0.0,
        "default_voice": "English_CalmWoman",
        "operational_char_limit": 2000,
    },
}

LANGUAGES = {"en", "de", "fr", "es", "hi", "it", "ja", "ko", "nl", "pl", "pt", "ru", "sv", "tr", "zh"}
RESPONSE_FORMATS = {"mp3", "wav", "raw", "mulaw", "opus", "aac", "flac"}
RESPONSE_ENCODINGS = {"pcm_f32le", "pcm_s16le", "pcm_mulaw", "pcm_alaw"}
BIT_RATES = {32000, 64000, 96000, 128000, 192000}
DOCUMENTED_KWARGS = {
    "response_format",
    "response_encoding",
    "sample_rate",
    "bit_rate",
    "stream",
    "alignment",
    "segment",
    "timeout_seconds",
}
DEFAULT_MODEL = "hexgrad/Kokoro-82M"
DEFAULT_VOICE = "af_alloy"
_UNKNOWN_MODEL_METADATA = {
    "usd_per_million_chars": 0.0,
    "default_voice": DEFAULT_VOICE,
    "operational_char_limit": 2000,
}


def generate(
    text: str,
    model: str = DEFAULT_MODEL,
    voice: str = DEFAULT_VOICE,
    language_code: str = "en",
    **kwargs: Any,
) -> dict[str, Any]:
    """Generate speech with Together AI TTS. See `synthesize/docs/together.md`."""
    model_config = DOCUMENTED_MODELS.get(model, _UNKNOWN_MODEL_METADATA)
    documented_model = model in DOCUMENTED_MODELS
    options = reject_unknown_kwargs("Together", model, kwargs, DOCUMENTED_KWARGS)
    response_format = str(options.pop("response_format", "raw")).strip().lower()
    response_encoding = str(options.pop("response_encoding", "pcm_s16le")).strip().lower()
    sample_rate = int(options.pop("sample_rate", 24000))
    bit_rate = options.pop("bit_rate", None)
    stream = bool(options.pop("stream", True))
    alignment = str(options.pop("alignment", "word")).strip().lower()
    segment = str(options.pop("segment", "sentence")).strip()
    timeout_seconds = float(options.pop("timeout_seconds", 180.0))
    validate_choice(response_format, RESPONSE_FORMATS, parameter_name="response_format", provider="Together", model=model)
    validate_choice(response_encoding, RESPONSE_ENCODINGS, parameter_name="response_encoding", provider="Together", model=model)
    if bit_rate is not None:
        bit_rate = int(bit_rate)
        validate_choice(bit_rate, BIT_RATES, parameter_name="bit_rate", provider="Together", model=model)

    api_key = ensure_env_var("TOGETHER_API_KEY")
    resolved_language = resolve_language_code(normalize_language_code(language_code))
    validate_choice(resolved_language, LANGUAGES, parameter_name="language_code", provider="Together", model=model)
    chosen_voice = _resolve_voice(api_key, model, voice)
    text_chunks = chunk_text_for_provider(text, model_config["operational_char_limit"])

    chunk_records: list[dict[str, Any]] = []
    total_tts_cost = 0.0
    total_alignment_cost = 0.0
    for chunk_text in text_chunks:
        request_payload: dict[str, Any] = {
            "model": model,
            "input": chunk_text,
            "voice": chosen_voice,
            "language": resolved_language,
            "stream": stream,
            "response_format": response_format,
            "sample_rate": int(sample_rate),
        }
        if response_format == "raw":
            request_payload["response_encoding"] = response_encoding
        if bit_rate is not None:
            request_payload["bit_rate"] = int(bit_rate)
        if stream and alignment == "word":
            request_payload["alignment"] = "word"
            request_payload["segment"] = segment
        elif alignment:
            request_payload["alignment"] = alignment
        request_payload.update({key: value for key, value in options.items() if value is not None})

        response = request_with_retries(
            "POST",
            API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json_body=request_payload,
            timeout=(15.0, float(timeout_seconds)),
            stream=stream,
        )
        if stream:
            events = collect_sse_events(response)
            pcm_chunks = [
                decode_base64_bytes(event.get("delta") or event.get("audio"))
                for event in events
                if str(event.get("type") or "").strip() in {"conversation.item.audio_output.delta", "delta"}
            ]
            if not pcm_chunks:
                raise ValueError(f"Together TTS did not return audio chunks for model '{model}'.")

            chunk_records.append(
                build_chunk_record(
                    text=chunk_text,
                    audio_bytes=pcm_to_wav_bytes(
                        b"".join(pcm_chunks),
                        sample_rate=int(sample_rate),
                        sample_width=2,
                        channels=1,
                    ),
                    audio_format="wav",
                    timing_events=events,
                )
            )
        else:
            audio_bytes = bytes(response.content or b"")
            if not audio_bytes:
                raise ValueError(f"Together TTS did not return audio bytes for model '{model}'.")
            chunk_record, chunk_alignment_cost = build_aligned_chunk_record(
                text=chunk_text,
                audio_bytes=audio_bytes if response_format != "raw" else pcm_to_wav_bytes(
                    audio_bytes,
                    sample_rate=int(sample_rate),
                    sample_width=2,
                    channels=1,
                ),
                audio_format=response_format if response_format != "raw" else "wav",
                language=resolve_locale(resolved_language),
            )
            chunk_records.append(chunk_record)
            total_alignment_cost += chunk_alignment_cost
        total_tts_cost += compute_cost_by_characters(
            len(chunk_text),
            model_config["usd_per_million_chars"],
        )

    result = _finalize_synthesis_output(chunk_records, cost_usd=0.0)
    result["cost_usd"] = round_cost(total_tts_cost + total_alignment_cost) if documented_model else 0.0
    if not documented_model:
        result["warnings"] = f"No documented pricing metadata is available for Together model `{model}`."
    return result


def _resolve_voice(api_key: str, model: str, voice: str) -> str:
    """Resolve and validate a Together voice for the selected model."""
    model_default = str(DOCUMENTED_MODELS.get(model, _UNKNOWN_MODEL_METADATA)["default_voice"]).strip()
    chosen_voice = str(voice or "").strip() or model_default
    if model != DEFAULT_MODEL and chosen_voice == DEFAULT_VOICE:
        chosen_voice = model_default
    return chosen_voice


__all__ = [
    "API_URL",
    "CATALOG_URL",
    "DEFAULT_MODEL",
    "DEFAULT_VOICE",
    "GUIDE_URL",
    "LANGUAGES",
    "PRICING_URL",
    "RESPONSE_ENCODINGS",
    "RESPONSE_FORMATS",
    "DOCUMENTED_MODELS",
    "VOICES_URL",
    "generate",
]
