"""Google AI Studio / Gemini TTS adapter with centralized Deepgram alignment.

Last updated: 2026-04-22
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .._apis._shared import (
    normalize_language_code,
    pcm_to_wav_bytes,
    reject_unknown_kwargs,
    request_with_retries,
    response_json,
    round_cost,
    validate_choice,
)
from ..post_processing import _finalize_synthesis_output, build_aligned_chunk_record
from ..pre_processing import chunk_text_for_provider, ensure_env_var, resolve_locale

API_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
MODELS_URL = "https://ai.google.dev/gemini-api/docs/models"
GUIDE_URL = "https://ai.google.dev/gemini-api/docs/speech-generation"
PRICING_URL = "https://ai.google.dev/gemini-api/docs/pricing"

DOCUMENTED_MODELS = {
    "gemini-2.5-flash-preview-tts": {
        "input_price_per_million_tokens": 0.50,
        "output_audio_price_per_million_tokens": 10.0,
        "operational_char_limit": 3200,
    },
    "gemini-2.5-pro-preview-tts": {
        "input_price_per_million_tokens": 1.00,
        "output_audio_price_per_million_tokens": 20.0,
        "operational_char_limit": 3200,
    },
    "gemini-3.1-flash-tts-preview": {
        "input_price_per_million_tokens": 0.50,
        "output_audio_price_per_million_tokens": 10.0,
        "operational_char_limit": 3200,
    },
}

VOICE_NAMES = {
    "Achernar",
    "Achird",
    "Algenib",
    "Algieba",
    "Alnilam",
    "Aoede",
    "Autonoe",
    "Callirrhoe",
    "Charon",
    "Despina",
    "Enceladus",
    "Erinome",
    "Fenrir",
    "Gacrux",
    "Iapetus",
    "Kore",
    "Laomedeia",
    "Leda",
    "Orus",
    "Puck",
    "Pulcherrima",
    "Rasalgethi",
    "Sadachbia",
    "Sadaltager",
    "Schedar",
    "Sulafat",
    "Umbriel",
    "Vindemiatrix",
    "Zephyr",
    "Zubenelgenubi",
}
DOCUMENTED_KWARGS = {
    "multi_speaker_voice_config",
    "speaker_voice_configs",
    "timeout_seconds",
}

_UNKNOWN_MODEL_METADATA = {
    "input_price_per_million_tokens": 0.0,
    "output_audio_price_per_million_tokens": 0.0,
    "operational_char_limit": 3200,
}


def generate(
    text: str,
    model: str = "gemini-2.5-flash-preview-tts",
    voice: str = "Aoede",
    language_code: str = "en",
    **kwargs: Any,
) -> dict[str, Any]:
    """Generate speech with Google Gemini TTS. See `synthesize/docs/google.md`."""
    model_config = DOCUMENTED_MODELS.get(model, _UNKNOWN_MODEL_METADATA)
    documented_model = model in DOCUMENTED_MODELS
    options = reject_unknown_kwargs("Google", model, kwargs, DOCUMENTED_KWARGS)
    validate_choice(voice, VOICE_NAMES, parameter_name="voice", provider="Google", model=model)
    timeout_seconds = float(options.pop("timeout_seconds", 180.0))
    multi_speaker_voice_config = options.pop("multi_speaker_voice_config", None)
    speaker_voice_configs = options.pop("speaker_voice_configs", None)
    if multi_speaker_voice_config is not None and speaker_voice_configs is not None:
        raise ValueError("Google Gemini TTS accepts either multi_speaker_voice_config or speaker_voice_configs, not both.")

    api_key = ensure_env_var("GOOGLE_API_KEY")
    text_chunks = chunk_text_for_provider(text, model_config["operational_char_limit"])
    resolved_locale = resolve_locale(normalize_language_code(language_code))

    chunk_records: list[dict[str, Any]] = []
    total_tts_cost = 0.0
    total_alignment_cost = 0.0
    for chunk_text in text_chunks:
        payload = {
            "contents": [{"parts": [{"text": chunk_text}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": _build_speech_config(
                    voice=voice,
                    multi_speaker_voice_config=multi_speaker_voice_config,
                    speaker_voice_configs=speaker_voice_configs,
                ),
            },
        }
        payload.update({key: value for key, value in options.items() if value is not None})
        response = request_with_retries(
            "POST",
            API_URL_TEMPLATE.format(model=model),
            params={"key": api_key},
            json_body=payload,
            timeout=(15.0, float(timeout_seconds)),
        )
        payload_json = response_json(response)
        audio_bytes = _extract_audio_bytes(payload_json)
        chunk_record, chunk_alignment_cost = build_aligned_chunk_record(
            text=chunk_text,
            audio_bytes=audio_bytes,
            audio_format="wav",
            language=resolved_locale,
        )
        chunk_records.append(chunk_record)
        total_alignment_cost += chunk_alignment_cost
        total_tts_cost += _compute_google_tts_cost(payload_json, model_config)

    result = _finalize_synthesis_output(chunk_records, cost_usd=0.0)
    result["cost_usd"] = round_cost(total_tts_cost + total_alignment_cost) if documented_model else 0.0
    if not documented_model:
        result["warnings"] = f"No documented pricing metadata is available for Google model `{model}`."
    return result


def _build_speech_config(
    *,
    voice: str,
    multi_speaker_voice_config: Any = None,
    speaker_voice_configs: Any = None,
) -> dict[str, Any]:
    """Build the Gemini speechConfig request object."""
    if multi_speaker_voice_config is not None:
        if not isinstance(multi_speaker_voice_config, Mapping):
            raise TypeError("Google multi_speaker_voice_config must be a mapping.")
        return {"multiSpeakerVoiceConfig": dict(multi_speaker_voice_config)}

    if speaker_voice_configs is not None:
        configs = []
        for item in list(speaker_voice_configs or []):
            if not isinstance(item, Mapping):
                raise TypeError("Each Google speaker_voice_configs item must be a mapping.")
            speaker = str(item.get("speaker") or "").strip()
            speaker_voice = str(item.get("voice") or item.get("voiceName") or "").strip()
            if not speaker:
                raise ValueError("Each Google speaker voice config requires a non-empty speaker.")
            validate_choice(speaker_voice, VOICE_NAMES, parameter_name="speaker voice", provider="Google", model="multi-speaker")
            configs.append(
                {
                    "speaker": speaker,
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {
                            "voiceName": speaker_voice,
                        }
                    },
                }
            )
        if not 1 <= len(configs) <= 2:
            raise ValueError("Google Gemini TTS supports one or two speaker_voice_configs entries.")
        return {"multiSpeakerVoiceConfig": {"speakerVoiceConfigs": configs}}

    return {
        "voiceConfig": {
            "prebuiltVoiceConfig": {
                "voiceName": voice,
            }
        }
    }


def _extract_audio_bytes(payload: Mapping[str, Any]) -> bytes:
    """Extract Gemini inline audio and normalize it into WAV bytes."""
    candidates = list(payload.get("candidates") or [])
    if not candidates:
        raise ValueError("Gemini TTS response did not include candidates.")
    content = candidates[0].get("content") if isinstance(candidates[0], Mapping) else {}
    parts = list((content or {}).get("parts") or [])
    for part in parts:
        if not isinstance(part, Mapping):
            continue
        inline_data = part.get("inlineData") or part.get("inline_data") or {}
        if not isinstance(inline_data, Mapping):
            continue
        mime_type = str(inline_data.get("mimeType") or inline_data.get("mime_type") or "").strip().lower()
        encoded = str(inline_data.get("data") or "").strip()
        if not encoded:
            continue
        import base64

        pcm_bytes = base64.b64decode(encoded)
        sample_rate = _extract_sample_rate_from_mime_type(mime_type)
        return pcm_to_wav_bytes(pcm_bytes, sample_rate=sample_rate, sample_width=2, channels=1)
    raise ValueError("Gemini TTS response did not include inline audio data.")


def _extract_sample_rate_from_mime_type(mime_type: str) -> int:
    """Infer the PCM sample rate from Gemini's inline-audio MIME string."""
    for part in str(mime_type or "").split(";"):
        key, _, value = part.partition("=")
        if key.strip().lower() == "rate":
            try:
                parsed = int(value.strip())
            except ValueError:
                break
            if parsed > 0:
                return parsed
    return 24000


def _compute_google_tts_cost(payload: Mapping[str, Any], model_config: Mapping[str, Any]) -> float:
    """Compute exact Gemini TTS token cost from `usageMetadata`."""
    usage = payload.get("usageMetadata") or {}
    if not isinstance(usage, Mapping):
        raise ValueError("Gemini TTS response did not include usageMetadata.")

    prompt_tokens = int(usage.get("promptTokenCount") or 0)
    candidates_details = list(usage.get("candidatesTokensDetails") or [])
    audio_tokens = 0
    for item in candidates_details:
        if not isinstance(item, Mapping):
            continue
        if str(item.get("modality") or "").strip().upper() == "AUDIO":
            audio_tokens += int(item.get("tokenCount") or 0)

    return round_cost(
        (prompt_tokens / 1_000_000.0) * float(model_config["input_price_per_million_tokens"])
        + (audio_tokens / 1_000_000.0) * float(model_config["output_audio_price_per_million_tokens"])
    )


__all__ = [
    "API_URL_TEMPLATE",
    "GUIDE_URL",
    "MODELS_URL",
    "PRICING_URL",
    "DOCUMENTED_MODELS",
    "VOICE_NAMES",
    "generate",
]
