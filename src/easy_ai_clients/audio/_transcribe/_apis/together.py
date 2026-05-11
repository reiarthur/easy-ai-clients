"""Together AI batch speech transcription with centralized pre/post-processing.

Implemented and validated with `teste/elevenlabs/audio.mp3` on 2026-04-22:
  - `openai/whisper-large-v3`

Current Together serverless STT reference:
  - `openai/whisper-large-v3`
  - `nvidia/parakeet-tdt-0.6b-v3`

Official references:
  - STT guide: https://docs.together.ai/docs/speech-to-text
  - Current serverless model catalog/pricing: https://docs.together.ai/docs/serverless-models

`nvidia/parakeet-tdt-0.6b-v3` is exposed without diarization by default because
Together currently rejects `diarize=true` for that model on the validated endpoint.
"""

from typing import Any

from .._apis._shared import (
    build_utterances_from_segments,
    build_utterances_from_speaker_segments,
    build_word_record,
    compute_cost_by_duration,
    get_required_api_key,
    reject_unknown_kwargs,
    request_with_retries,
    response_json,
    round_cost,
    validate_choice,
    validate_number_range,
)
from ..post_processing import _build_transcription_bundle, build_raw_transcription_payload
from ..pre_processing import build_request_audio

API_URL = "https://api.together.xyz/v1/audio/transcriptions"
MODELS_URL = "https://api.together.xyz/v1/models"
SUPPORTED_MODELS = {
    "openai/whisper-large-v3": {
        "price_per_minute": 0.0015,
        "supports_diarization": True,
    },
    "nvidia/parakeet-tdt-0.6b-v3": {
        "price_per_minute": 0.0015,
        "supports_diarization": False,
    },
}
RESPONSE_FORMATS = {"json", "verbose_json"}
TIMESTAMP_GRANULARITIES = {"segment", "word"}
SUPPORTED_KWARGS = {
    "language",
    "prompt",
    "response_format",
    "temperature",
    "timestamp_granularities",
    "diarize",
    "min_speakers",
    "max_speakers",
    "language_mkd",
    "timeout_seconds",
}


def transcribe(
    audio_input: Any,
    model: str = "openai/whisper-large-v3",
    **kwargs: Any,
) -> dict[str, Any]:
    """Transcribe audio with Together AI. See `transcribe/docs/together.md`."""
    if model not in SUPPORTED_MODELS:
        supported_models = ", ".join(sorted(SUPPORTED_MODELS))
        raise ValueError(f"Unsupported Together model '{model}'. Supported models: {supported_models}.")

    options = reject_unknown_kwargs("Together", model, kwargs, SUPPORTED_KWARGS)
    language = options.pop("language", "auto")
    prompt = options.pop("prompt", None)
    response_format = str(options.pop("response_format", "verbose_json")).strip()
    validate_choice(response_format, RESPONSE_FORMATS, parameter_name="response_format", provider="Together", model=model)
    if response_format != "verbose_json":
        raise ValueError("Together response_format must be 'verbose_json' to preserve the repository transcription contract.")
    temperature = options.pop("temperature", None)
    if temperature is not None:
        validate_number_range(temperature, parameter_name="temperature", provider="Together", model=model, minimum=0.0, maximum=1.0)
    timestamp_granularities = _normalize_timestamp_granularities(options.pop("timestamp_granularities", ["word", "segment"]))
    if "word" not in timestamp_granularities:
        raise ValueError("Together timestamp_granularities must include 'word' to preserve timed words.")
    diarize = bool(options.pop("diarize", SUPPORTED_MODELS[model]["supports_diarization"]))
    if diarize and not SUPPORTED_MODELS[model]["supports_diarization"]:
        raise ValueError(f"Together model '{model}' does not support diarize=True on the validated endpoint.")
    min_speakers = options.pop("min_speakers", None)
    max_speakers = options.pop("max_speakers", None)
    language_mkd = options.pop("language_mkd", "en")
    timeout_seconds = float(options.pop("timeout_seconds", 300))

    request_audio = build_request_audio(audio_input)
    api_key = get_required_api_key("TOGETHER_API_KEY")

    form_fields = [
        ("model", model),
        ("response_format", response_format),
    ]
    for granularity in timestamp_granularities:
        form_fields.append(("timestamp_granularities", granularity))
    if language:
        form_fields.append(("language", language))
    if prompt:
        form_fields.append(("prompt", prompt))
    if diarize:
        form_fields.append(("diarize", "true"))
    if temperature is not None:
        form_fields.append(("temperature", float(temperature)))
    if min_speakers is not None:
        form_fields.append(("min_speakers", int(min_speakers)))
    if max_speakers is not None:
        form_fields.append(("max_speakers", int(max_speakers)))

    response = request_with_retries(
        "POST",
        API_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        data=form_fields,
        files={"file": (request_audio["file_name"], request_audio["audio_bytes"], request_audio["content_type"])},
        timeout=(15.0, float(timeout_seconds)),
    )
    payload = response_json(response)

    words = []
    for word_payload in payload.get("words") or []:
        normalized_word = build_word_record(
            word_payload.get("word") or word_payload.get("text"),
            word_payload.get("start"),
            word_payload.get("end"),
            speaker=word_payload.get("speaker_id") or word_payload.get("speaker"),
        )
        if normalized_word:
            words.append(normalized_word)

    utterances = build_utterances_from_speaker_segments(payload.get("speaker_segments"), words)
    if not utterances:
        utterances = build_utterances_from_segments(payload.get("segments"), words)

    provider_segments = []
    for segment_payload in payload.get("segments") or []:
        provider_segments.append(
            {
                "id": segment_payload.get("id"),
                "start": segment_payload.get("start"),
                "end": segment_payload.get("end"),
                "text": segment_payload.get("text"),
                "speaker_id": segment_payload.get("speaker_id"),
            }
        )

    provider_speaker_segments = []
    for speaker_segment in payload.get("speaker_segments") or []:
        provider_speaker_segments.append(
            {
                "speaker_id": speaker_segment.get("speaker_id") or speaker_segment.get("speaker"),
                "start": speaker_segment.get("start"),
                "end": speaker_segment.get("end"),
                "text": speaker_segment.get("text"),
                "word_count": len(list(speaker_segment.get("words") or [])),
            }
        )

    raw_payload = build_raw_transcription_payload(
        provider="together",
        model=model,
        audio_duration_seconds=payload.get("duration") or request_audio["audio_duration_seconds"],
        language=payload.get("language") or language,
        text=payload.get("text"),
        words=words,
        utterances=utterances,
        provider_metadata={
            "task": payload.get("task"),
            "raw_segments": provider_segments,
            "speaker_segments": provider_speaker_segments,
        },
    )
    cost_metadata = _resolve_together_cost_metadata(
        api_key,
        model,
        payload.get("duration") or request_audio["audio_duration_seconds"],
    )
    return _build_transcription_bundle(
        raw_payload,
        language_mkd=language_mkd,
        request_id=payload.get("id"),
        **cost_metadata,
    )


def _resolve_together_cost_metadata(api_key, model, duration_seconds):
    """Resolves Together transcription cost from the model catalog when available."""
    price_per_minute, lookup_error = _lookup_model_price_per_minute(api_key, model)
    if price_per_minute is not None:
        return {
            "cost_usd": compute_cost_by_duration(
                duration_seconds,
                unit_price=price_per_minute,
                billing_unit="minute",
            ),
            "cost_source": "pricing_api",
            "cost_is_estimated": True,
            "cost_lookup_error": None,
        }

    return {
        "cost_usd": compute_cost_by_duration(
            duration_seconds,
            unit_price=SUPPORTED_MODELS[model]["price_per_minute"],
            billing_unit="minute",
        ),
        "cost_source": "official_pricing_table",
        "cost_is_estimated": True,
        "cost_lookup_error": lookup_error,
    }


def _lookup_model_price_per_minute(api_key, model):
    """Fetches Together model transcribe pricing from the authenticated catalog."""
    try:
        response = request_with_retries(
            "GET",
            MODELS_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=(15.0, 60.0),
        )
        payload = response.json()
    except Exception as error:
        return None, f"Together model pricing lookup failed: {error}"

    if isinstance(payload, dict):
        items = payload.get("data") or payload.get("models") or []
    else:
        items = payload
    if isinstance(items, dict):
        items = list(items.values())
    for item in list(items or []):
        if not isinstance(item, dict):
            continue
        if item.get("id") != model and item.get("name") != model:
            continue
        pricing = item.get("pricing") or {}
        transcribe_pricing = pricing.get("transcribe") or pricing.get("audio_transcription") or {}
        for key in ("price_per_minute", "price_per_audio_minute", "per_minute"):
            value = transcribe_pricing.get(key)
            if value is not None:
                return round_cost(value), None
    return None, f"Together model pricing lookup did not include transcribe pricing for '{model}'."


def _normalize_timestamp_granularities(value):
    """Normalize Together timestamp granularity input into ordered form fields."""
    if isinstance(value, str):
        values = [item.strip() for item in value.split(",") if item.strip()]
    else:
        values = [str(item).strip() for item in list(value or []) if str(item).strip()]
    if not values:
        values = ["segment"]
    for item in values:
        validate_choice(item, TIMESTAMP_GRANULARITIES, parameter_name="timestamp_granularities", provider="Together", model="transcription")
    return values
