"""xAI text-to-speech adapter with centralized Deepgram alignment.

Last updated: 2026-04-22
"""

from __future__ import annotations

from typing import Any

from .._apis._shared import (
    compute_cost_by_characters,
    normalize_language_code,
    pcm_to_wav_bytes,
    reject_unknown_kwargs,
    request_with_retries,
    round_cost,
    validate_choice,
)
from ..post_processing import _finalize_synthesis_output, build_aligned_chunk_record
from ..pre_processing import chunk_text_for_provider, ensure_env_var, resolve_locale

API_URL = "https://api.x.ai/v1/tts"
MODELS_URL = "https://docs.x.ai/developers/models/text-to-speech"
PRICING_URL = "https://docs.x.ai/developers/models"

DOCUMENTED_MODELS = {
    "text-to-speech": {
        "usd_per_million_chars": 4.2,
        "operational_char_limit": 2200,
    }
}

VOICES = {"ara", "eve", "leo", "rex", "sal"}
LANGUAGES = {
    "auto",
    "en",
    "ar-EG",
    "ar-SA",
    "ar-AE",
    "bn",
    "zh",
    "fr",
    "de",
    "hi",
    "id",
    "it",
    "ja",
    "ko",
    "pt-BR",
    "pt-PT",
    "ru",
    "es-MX",
    "es-ES",
    "tr",
    "vi",
}
CODECS = {"mp3", "wav", "pcm", "mulaw", "ulaw", "alaw"}
SAMPLE_RATES = {8000, 16000, 22050, 24000, 44100, 48000}
BIT_RATES = {32000, 64000, 96000, 128000, 192000}
DOCUMENTED_KWARGS = {"codec", "sample_rate", "bit_rate", "text_normalization", "timeout_seconds"}
_UNKNOWN_MODEL_METADATA = {
    "usd_per_million_chars": 0.0,
    "operational_char_limit": 2200,
}


def generate(
    text: str,
    model: str = "text-to-speech",
    voice: str = "eve",
    language_code: str = "en",
    **kwargs: Any,
) -> dict[str, Any]:
    """Generate speech with xAI TTS. See `synthesize/docs/xai.md`."""
    model_config = DOCUMENTED_MODELS.get(model, _UNKNOWN_MODEL_METADATA)
    documented_model = model in DOCUMENTED_MODELS
    options = reject_unknown_kwargs("xAI", model, kwargs, DOCUMENTED_KWARGS)
    codec = str(options.pop("codec", "mp3")).strip().lower()
    if codec == "ulaw":
        codec = "mulaw"
    validate_choice(voice, VOICES, parameter_name="voice", provider="xAI", model=model)
    validate_choice(codec, CODECS - {"ulaw"}, parameter_name="codec", provider="xAI", model=model)
    resolved_locale = normalize_language_code(language_code)
    validate_choice(resolved_locale, LANGUAGES, parameter_name="language_code", provider="xAI", model=model)
    sample_rate = options.pop("sample_rate", None)
    if sample_rate is not None:
        sample_rate = int(sample_rate)
        validate_choice(sample_rate, SAMPLE_RATES, parameter_name="sample_rate", provider="xAI", model=model)
    bit_rate = options.pop("bit_rate", None)
    if bit_rate is not None:
        bit_rate = int(bit_rate)
        validate_choice(bit_rate, BIT_RATES, parameter_name="bit_rate", provider="xAI", model=model)
    text_normalization = options.pop("text_normalization", None)
    timeout_seconds = float(options.pop("timeout_seconds", 180.0))

    api_key = ensure_env_var("XAI_API_KEY")
    text_chunks = chunk_text_for_provider(text, model_config["operational_char_limit"])
    alignment_locale = resolve_locale(resolved_locale)

    chunk_records: list[dict[str, Any]] = []
    total_alignment_cost = 0.0
    total_tts_cost = 0.0
    for chunk_text in text_chunks:
        payload: dict[str, Any] = {
            "model": model,
            "text": chunk_text,
            "voice": voice,
            "language": resolved_locale,
            "codec": codec,
        }
        if sample_rate is not None:
            payload["sample_rate"] = int(sample_rate)
        if bit_rate is not None:
            payload["bit_rate"] = int(bit_rate)
        if text_normalization is not None:
            payload["text_normalization"] = bool(text_normalization)
        payload.update({key: value for key, value in options.items() if value is not None})

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
            raise ValueError("xAI TTS returned an empty audio payload.")

        normalized_audio_bytes, audio_format = _normalize_audio_bytes(
            audio_bytes,
            codec=codec,
            sample_rate=sample_rate or 24000,
        )
        chunk_record, chunk_alignment_cost = build_aligned_chunk_record(
            text=chunk_text,
            audio_bytes=normalized_audio_bytes,
            audio_format=audio_format,
            language=alignment_locale,
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
        result["warnings"] = f"No documented pricing metadata is available for xAI model `{model}`."
    return result


def _normalize_audio_bytes(audio_bytes: bytes, *, codec: str, sample_rate: int) -> tuple[bytes, str]:
    """Wrap raw xAI audio codecs in WAV when needed by downstream decoding."""
    if codec == "pcm":
        return pcm_to_wav_bytes(audio_bytes, sample_rate=sample_rate, sample_width=2, channels=1), "wav"
    if codec in {"mulaw", "alaw"}:
        import audioop

        pcm_bytes = audioop.ulaw2lin(audio_bytes, 2) if codec == "mulaw" else audioop.alaw2lin(audio_bytes, 2)
        return pcm_to_wav_bytes(pcm_bytes, sample_rate=sample_rate, sample_width=2, channels=1), "wav"
    return audio_bytes, codec


__all__ = [
    "API_URL",
    "CODECS",
    "LANGUAGES",
    "MODELS_URL",
    "PRICING_URL",
    "SAMPLE_RATES",
    "DOCUMENTED_MODELS",
    "VOICES",
    "generate",
]
