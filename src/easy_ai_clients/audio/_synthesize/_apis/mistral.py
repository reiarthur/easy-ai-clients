"""Mistral Voxtral TTS adapter with same-request zero-shot voice cloning.

Last updated: 2026-04-22
"""

from __future__ import annotations

from typing import Any

from .._apis._shared import (
    compute_cost_by_characters,
    normalize_language_code,
    reject_unknown_kwargs,
    request_with_retries,
    response_json,
    round_cost,
    synthesize_json_base64_tts,
    validate_choice,
)
from ..post_processing import _finalize_synthesis_output, build_aligned_chunk_record
from ..pre_processing import (
    chunk_text_for_provider,
    ensure_env_var,
    resolve_locale,
    resolve_reference_audio,
)

API_URL = "https://api.mistral.ai/v1/audio/speech"
VOICES_URL = "https://api.mistral.ai/v1/audio/voices"
MODELS_URL = "https://docs.mistral.ai/models/model-cards/voxtral-tts-26-03"
ENDPOINT_URL = "https://docs.mistral.ai/api/endpoint/audio/speech"
PRICING_URL = "https://docs.mistral.ai/models/model-cards/voxtral-tts-26-03"

SUPPORTED_MODELS = {
    "voxtral-mini-tts-2603": {
        "usd_per_million_chars": 16.0,
        "operational_char_limit": 1800,
    },
    "voxtral-mini-tts-latest": {
        "usd_per_million_chars": 16.0,
        "operational_char_limit": 1800,
    }
}

RESPONSE_FORMATS = {"pcm", "wav", "mp3", "flac", "opus"}
SUPPORTED_KWARGS = {
    "reference_audio",
    "reference_audio_path",
    "reference_audio_base64",
    "reference_audio_url",
    "response_format",
    "stream",
    "timeout_seconds",
}
DEFAULT_VOICE = "default"


def generate(
    text: str,
    model: str = "voxtral-mini-tts-2603",
    voice: str = DEFAULT_VOICE,
    language_code: str = "en",
    **kwargs: Any,
) -> dict[str, Any]:
    """Generate speech with Mistral Voxtral TTS. See `synthesize/docs/mistral.md`."""
    if model not in SUPPORTED_MODELS:
        supported = ", ".join(sorted(SUPPORTED_MODELS))
        raise ValueError(f"Unsupported Mistral TTS model '{model}'. Supported models: {supported}.")

    options = reject_unknown_kwargs("Mistral", model, kwargs, SUPPORTED_KWARGS)
    response_format = str(options.pop("response_format", "mp3")).strip().lower()
    validate_choice(response_format, RESPONSE_FORMATS, parameter_name="response_format", provider="Mistral", model=model)
    stream = bool(options.pop("stream", False))
    if stream:
        raise ValueError("Mistral stream=True is not supported by this repository's AudioSegment return contract.")
    timeout_seconds = float(options.pop("timeout_seconds", 180.0))
    api_key = ensure_env_var("MISTRAL_API_KEY")
    resolved_locale = resolve_locale(normalize_language_code(language_code))
    has_reference_audio = any(
        options.get(name) not in (None, "", [], {})
        for name in ("reference_audio", "reference_audio_path", "reference_audio_base64", "reference_audio_url")
    )
    requested_voice = str(voice or "").strip()
    if has_reference_audio and requested_voice.lower() == DEFAULT_VOICE:
        voice_id = None
    else:
        voice_id = _resolve_voice_id(
            api_key=api_key,
            voice=voice,
            language_code=resolved_locale,
            timeout_seconds=timeout_seconds,
        )
    reference_bundle = resolve_reference_audio(
        voice_id=voice_id,
        reference_audio=options.get("reference_audio"),
        reference_audio_path=options.get("reference_audio_path"),
        reference_audio_base64=options.get("reference_audio_base64"),
        reference_audio_url=options.get("reference_audio_url"),
        export_format="mp3",
        file_stem="mistral_reference",
    )
    if not voice_id and reference_bundle is None:
        raise ValueError(
            "Mistral TTS requires either a saved voice id via voice or a reference_audio* kwarg. "
            "The public default voice='default' could not resolve to an account voice."
        )

    model_config = SUPPORTED_MODELS[model]
    text_chunks = chunk_text_for_provider(text, model_config["operational_char_limit"])

    chunk_records: list[dict[str, Any]] = []
    total_tts_cost = 0.0
    total_alignment_cost = 0.0
    for chunk_text in text_chunks:
        payload: dict[str, Any] = {
            "model": model,
            "input": chunk_text,
            "response_format": response_format,
        }
        if voice_id:
            payload["voice_id"] = voice_id
        if reference_bundle is not None:
            payload["ref_audio"] = reference_bundle["audio_base64"]

        audio_bytes, _, _ = synthesize_json_base64_tts(
            url=API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            payload=payload,
            audio_field="audio_data",
            timeout_seconds=timeout_seconds,
        )
        chunk_record, chunk_alignment_cost = build_aligned_chunk_record(
            text=chunk_text,
            audio_bytes=audio_bytes,
            audio_format=response_format,
            language=resolved_locale,
        )
        chunk_records.append(chunk_record)
        total_tts_cost += compute_cost_by_characters(
            len(chunk_text),
            model_config["usd_per_million_chars"],
        )
        total_alignment_cost += chunk_alignment_cost

    result = _finalize_synthesis_output(chunk_records, cost_usd=0.0)
    result["cost_usd"] = round_cost(total_tts_cost + total_alignment_cost)
    return result


def _resolve_voice_id(
    *,
    api_key: str,
    voice: str,
    language_code: str,
    timeout_seconds: float,
) -> str | None:
    """Resolve the public voice value to a Mistral saved voice id when available."""
    requested_voice = str(voice or "").strip()
    if requested_voice and requested_voice.lower() != DEFAULT_VOICE:
        return requested_voice

    response = request_with_retries(
        "GET",
        VOICES_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=(10.0, min(60.0, float(timeout_seconds))),
    )
    payload = response_json(response)
    voices = [item for item in payload.get("items") or [] if isinstance(item, dict)]
    if not voices:
        return None

    requested_language = str(language_code or "en").split("-", 1)[0].lower()
    for item in voices:
        languages = [str(language or "").split("_", 1)[0].split("-", 1)[0].lower() for language in item.get("languages") or []]
        if requested_language in languages and str(item.get("id") or "").strip():
            return str(item["id"]).strip()
    first_voice_id = str(voices[0].get("id") or "").strip()
    return first_voice_id or None


__all__ = [
    "API_URL",
    "ENDPOINT_URL",
    "MODELS_URL",
    "PRICING_URL",
    "RESPONSE_FORMATS",
    "SUPPORTED_MODELS",
    "VOICES_URL",
    "generate",
]
