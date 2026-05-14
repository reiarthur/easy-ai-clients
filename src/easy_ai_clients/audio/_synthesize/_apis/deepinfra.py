"""DeepInfra TTS gateway adapter with centralized external alignment.

Last updated: 2026-04-22
"""

from __future__ import annotations

from typing import Any

from .._apis._shared import (
    compute_cost_by_characters,
    discover_deepinfra_tts_models,
    normalize_language_code,
    pcm_to_wav_bytes,
    reject_unknown_kwargs,
    request_with_retries,
    round_cost,
    validate_choice,
    validate_number_range,
)
from ..post_processing import _finalize_synthesis_output, build_aligned_chunk_record
from ..pre_processing import (
    chunk_text_for_provider,
    ensure_env_var,
    resolve_language_code,
    resolve_locale,
)

API_URL = "https://api.deepinfra.com/v1/openai/audio/speech"
CATALOG_URL = "https://api.deepinfra.com/models/list"
MODELS_URL = "https://deepinfra.com/models/text-to-speech"
SCHEMA_URL = "https://docs.deepinfra.com/api-reference/model-schema"

DOCUMENTED_MODELS = {
    "hexgrad/Kokoro-82M": {
        "usd_per_million_chars": 0.0,
        "default_voice": "af_bella",
        "operational_char_limit": 1800,
    },
    "Qwen/Qwen3-TTS": {
        "usd_per_million_chars": 20.0,
        "default_voice": "Vivian",
        "operational_char_limit": 1800,
    },
    "Qwen/Qwen3-TTS-VoiceDesign": {
        "usd_per_million_chars": 20.0,
        "default_voice": "uma voz feminina brasileira serena, acolhedora e natural",
        "operational_char_limit": 1800,
    },
    "ResembleAI/chatterbox": {
        "usd_per_million_chars": 0.0,
        "default_voice": "default",
        "operational_char_limit": 1800,
    },
    "ResembleAI/chatterbox-turbo": {
        "usd_per_million_chars": 0.0,
        "default_voice": "default",
        "operational_char_limit": 1800,
    },
    "ResembleAI/chatterbox-multilingual": {
        "usd_per_million_chars": 0.0,
        "default_voice": "default",
        "operational_char_limit": 1800,
        "default_language_id": "en",
    },
    "Zyphra/Zonos-v0.1-hybrid": {
        "usd_per_million_chars": 0.0,
        "default_voice": "random",
        "operational_char_limit": 1800,
    },
    "Zyphra/Zonos-v0.1-transformer": {
        "usd_per_million_chars": 0.0,
        "default_voice": "random",
        "operational_char_limit": 1800,
    },
    "bosonai/HiggsAudioV2.5": {
        "usd_per_million_chars": 0.0,
        "default_voice": "belinda",
        "operational_char_limit": 1800,
        "raw_pcm_output": True,
        "sample_rate": 24000,
    },
    "canopylabs/orpheus-3b-0.1-ft": {
        "usd_per_million_chars": 0.0,
        "default_voice": "tara",
        "operational_char_limit": 1800,
    },
    "inworld-ai/inworld-tts-1.5-max": {
        "usd_per_million_chars": 0.0,
        "default_voice": "Ashley",
        "operational_char_limit": 1800,
    },
    "inworld-ai/inworld-tts-1.5-mini": {
        "usd_per_million_chars": 0.0,
        "default_voice": "Ashley",
        "operational_char_limit": 1800,
    },
    "sesame/csm-1b": {
        "usd_per_million_chars": 0.0,
        "default_voice": "none",
        "operational_char_limit": 1800,
    },
}

RESPONSE_FORMATS = {"mp3", "wav", "pcm", "flac", "opus"}
SERVICE_TIERS = {"default", "priority"}
DOCUMENTED_KWARGS = {
    "response_format",
    "service_tier",
    "speed",
    "extra_body",
    "timeout_seconds",
    "language",
    "instruct",
    "voice_id",
    "language_id",
    "exaggeration",
    "cfg",
    "temperature",
    "seed",
    "top_p",
    "min_p",
    "repetition_penalty",
    "top_k",
    "preset_voice",
    "output_format",
    "speaker_rate",
    "speaking_rate",
    "sample_rate",
    "return_timestamps",
    "max_tokens",
    "speaker_audio",
    "speaker_transcript",
    "max_audio_length_ms",
}
MODEL_LIMITATIONS = {
    "ResembleAI/chatterbox": "DeepInfra exposes this model through the live TTS schema; validation depends on the gateway accepting the generic OpenAI-compatible TTS surface.",
    "ResembleAI/chatterbox-turbo": "DeepInfra exposes this model through the live TTS schema; validation depends on the gateway accepting the generic OpenAI-compatible TTS surface.",
    "ResembleAI/chatterbox-multilingual": "DeepInfra exposes this model through the live TTS schema; prior Portuguese alignment validation was unreliable.",
    "Zyphra/Zonos-v0.1-hybrid": "Reference-audio controls are model-specific and may require additional account assets.",
    "Zyphra/Zonos-v0.1-transformer": "Reference-audio controls are model-specific and may require additional account assets.",
    "sesame/csm-1b": "Speaker-audio cloning controls are model-specific and may require reference audio for best quality.",
}

DEFAULT_MODEL = "hexgrad/Kokoro-82M"
DEFAULT_VOICE = "af_bella"
_UNKNOWN_MODEL_METADATA = {
    "usd_per_million_chars": 0.0,
    "default_voice": DEFAULT_VOICE,
    "operational_char_limit": 1800,
}


def generate(
    text: str,
    model: str = DEFAULT_MODEL,
    voice: str = DEFAULT_VOICE,
    language_code: str = "en",
    **kwargs: Any,
) -> dict[str, Any]:
    """Generate speech with DeepInfra TTS. See `synthesize/docs/deepinfra.md`."""
    model_config = DOCUMENTED_MODELS.get(model, _UNKNOWN_MODEL_METADATA)
    documented_model = model in DOCUMENTED_MODELS
    options = reject_unknown_kwargs("DeepInfra", model, kwargs, DOCUMENTED_KWARGS)
    response_format = str(options.pop("response_format", "mp3")).strip().lower()
    validate_choice(response_format, RESPONSE_FORMATS, parameter_name="response_format", provider="DeepInfra", model=model)
    service_tier = str(options.pop("service_tier", "default")).strip().lower()
    validate_choice(service_tier, SERVICE_TIERS, parameter_name="service_tier", provider="DeepInfra", model=model)
    speed = validate_number_range(options.pop("speed", 1.0), parameter_name="speed", provider="DeepInfra", model=model, minimum=0.25, maximum=4.0)
    timeout_seconds = float(options.pop("timeout_seconds", 180.0))
    extra_body = options.pop("extra_body", None)
    if extra_body is not None and not isinstance(extra_body, dict):
        raise TypeError("DeepInfra extra_body must be a dictionary when provided.")

    api_key = ensure_env_var("DEEPINFRA_API_KEY")
    chosen_voice = _resolve_voice(model, voice)
    text_chunks = chunk_text_for_provider(text, model_config["operational_char_limit"])
    resolved_locale = resolve_locale(normalize_language_code(language_code))
    provider_extra_body = _build_extra_body(
        options,
        _build_extra_body(dict(extra_body or {}), _default_model_extra_body(model, language_code)),
    )

    chunk_records: list[dict[str, Any]] = []
    total_tts_cost = 0.0
    total_alignment_cost = 0.0
    for chunk_text in text_chunks:
        payload: dict[str, Any] = {
            "model": model,
            "input": chunk_text,
            "response_format": response_format,
            "service_tier": service_tier,
            "speed": speed,
        }
        if chosen_voice and chosen_voice != "default":
            payload["voice"] = chosen_voice
        if provider_extra_body:
            payload["extra_body"] = provider_extra_body

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
            raise ValueError("DeepInfra TTS returned an empty audio payload.")
        chunk_audio_format = response_format
        if model_config.get("raw_pcm_output"):
            audio_bytes = pcm_to_wav_bytes(
                audio_bytes,
                sample_rate=int(model_config.get("sample_rate", 24000)),
                sample_width=2,
                channels=1,
            )
            chunk_audio_format = "wav"

        chunk_record, chunk_alignment_cost = build_aligned_chunk_record(
            text=chunk_text,
            audio_bytes=audio_bytes,
            audio_format=chunk_audio_format,
            language=resolved_locale,
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
        result["warnings"] = f"No documented pricing metadata is available for DeepInfra model `{model}`."
    return result


def _resolve_voice(model: str, voice: str) -> str:
    """Choose the safest DeepInfra voice for the selected model."""
    model_default = str(DOCUMENTED_MODELS.get(model, _UNKNOWN_MODEL_METADATA)["default_voice"]).strip()
    chosen_voice = str(voice or "").strip() or model_default
    if model != DEFAULT_MODEL and chosen_voice == DEFAULT_VOICE:
        return model_default
    return chosen_voice


def _build_extra_body(options: dict[str, Any], extra_body: dict[str, Any] | None) -> dict[str, Any]:
    """Merge model-specific DeepInfra schema fields into extra_body."""
    merged = dict(extra_body or {})
    for key, value in options.items():
        if value in (None, "", [], {}):
            continue
        merged[key] = value
    return merged


def _default_model_extra_body(model: str, language_code: str) -> dict[str, Any]:
    """Return model-specific DeepInfra defaults that are needed for valid output."""
    model_config = DOCUMENTED_MODELS.get(model, _UNKNOWN_MODEL_METADATA)
    defaults: dict[str, Any] = {}
    if "default_language_id" in model_config:
        defaults["language_id"] = resolve_language_code(
            language_code,
            default=str(model_config["default_language_id"]),
        )
    return defaults


def discover_catalog() -> list[dict[str, Any]]:
    """Return the current live DeepInfra TTS catalog for manual inspection/tests."""
    api_key = ensure_env_var("DEEPINFRA_API_KEY")
    return discover_deepinfra_tts_models(api_key)


__all__ = [
    "API_URL",
    "CATALOG_URL",
    "DEFAULT_MODEL",
    "DEFAULT_VOICE",
    "MODEL_LIMITATIONS",
    "MODELS_URL",
    "RESPONSE_FORMATS",
    "SCHEMA_URL",
    "DOCUMENTED_MODELS",
    "discover_catalog",
    "generate",
]
