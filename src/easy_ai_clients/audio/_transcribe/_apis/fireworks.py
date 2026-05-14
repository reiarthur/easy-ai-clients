"""Fireworks AI batch speech transcription with centralized pre/post-processing.

Implemented and validated with `teste/elevenlabs/audio.mp3` on 2026-04-22:
  - `whisper-v3`
  - `whisper-v3-turbo`

Official references:
  - STT endpoint: https://docs.fireworks.ai/api-reference/audio-transcriptions
  - Current pricing: https://fireworks.ai/pricing
"""

from typing import Any

from .._apis._shared import (
    build_utterances_from_segments,
    build_word_record,
    compute_cost_by_duration,
    get_required_api_key,
    reject_unknown_kwargs,
    request_with_retries,
    response_json,
    validate_choice,
    validate_number_range,
)
from ..post_processing import _build_transcription_bundle, build_raw_transcription_payload
from ..pre_processing import build_request_audio

DOCUMENTED_MODELS = {
    "whisper-v3": {
        "endpoint": "https://audio-prod.api.fireworks.ai/v1/audio/transcriptions",
        "price_per_minute": 0.0015,
    },
    "whisper-v3-turbo": {
        "endpoint": "https://audio-turbo.api.fireworks.ai/v1/audio/transcriptions",
        "price_per_minute": 0.0009,
    },
}
_UNKNOWN_MODEL_METADATA = {
    "endpoint": "https://audio-prod.api.fireworks.ai/v1/audio/transcriptions",
    "price_per_minute": 0.0,
}
VAD_MODELS = {"silero", "whisperx-pyannet"}
ALIGNMENT_MODELS = {"mms_fa", "tdnn_ffn"}
RESPONSE_FORMATS = {"json", "text", "srt", "verbose_json", "vtt"}
TIMESTAMP_GRANULARITIES = {"word", "segment"}
PREPROCESSING_MODES = {"none", "dynamic", "soft_dynamic", "bass_dynamic"}
DOCUMENTED_KWARGS = {
    "vad_model",
    "alignment_model",
    "language",
    "prompt",
    "temperature",
    "response_format",
    "timestamp_granularities",
    "diarize",
    "min_speakers",
    "max_speakers",
    "preprocessing",
    "language_mkd",
    "timeout_seconds",
}


def transcribe(
    audio_input: Any,
    model: str = "whisper-v3-turbo",
    **kwargs: Any,
) -> dict[str, Any]:
    """Transcribe audio with Fireworks AI. See `transcribe/docs/fireworks.md`."""
    model_config = DOCUMENTED_MODELS.get(model, _UNKNOWN_MODEL_METADATA)
    documented_model = model in DOCUMENTED_MODELS
    options = reject_unknown_kwargs("Fireworks", model, kwargs, DOCUMENTED_KWARGS)
    language = options.pop("language", None)
    prompt = options.pop("prompt", None)
    diarize = bool(options.pop("diarize", True))
    language_mkd = options.pop("language_mkd", "en")
    timeout_seconds = float(options.pop("timeout_seconds", 300))
    response_format = str(options.pop("response_format", "verbose_json")).strip()
    validate_choice(response_format, RESPONSE_FORMATS, parameter_name="response_format", provider="Fireworks", model=model)
    timestamp_granularities = _normalize_timestamp_granularities(options.pop("timestamp_granularities", ["word", "segment"]))
    vad_model = options.pop("vad_model", None)
    if vad_model is not None:
        validate_choice(str(vad_model), VAD_MODELS, parameter_name="vad_model", provider="Fireworks", model=model)
    alignment_model = options.pop("alignment_model", None)
    if alignment_model is not None:
        validate_choice(str(alignment_model), ALIGNMENT_MODELS, parameter_name="alignment_model", provider="Fireworks", model=model)
    temperature = options.pop("temperature", None)
    if temperature is not None:
        validate_number_range(temperature, parameter_name="temperature", provider="Fireworks", model=model, minimum=0.0)
    min_speakers = options.pop("min_speakers", None)
    max_speakers = options.pop("max_speakers", None)
    preprocessing = options.pop("preprocessing", None)
    if preprocessing is not None:
        validate_choice(str(preprocessing), PREPROCESSING_MODES, parameter_name="preprocessing", provider="Fireworks", model=model)

    request_audio = build_request_audio(audio_input)
    api_key = get_required_api_key("FIREWORKS_API_KEY")

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
    if vad_model is not None:
        form_fields.append(("vad_model", str(vad_model)))
    if alignment_model is not None:
        form_fields.append(("alignment_model", str(alignment_model)))
    if temperature is not None:
        form_fields.append(("temperature", float(temperature)))
    if min_speakers is not None:
        form_fields.append(("min_speakers", int(min_speakers)))
    if max_speakers is not None:
        form_fields.append(("max_speakers", int(max_speakers)))
    if preprocessing is not None:
        form_fields.append(("preprocessing", str(preprocessing)))
    for key, value in options.items():
        if value not in (None, "", [], {}):
            form_fields.append((key, value))

    response = request_with_retries(
        "POST",
        model_config["endpoint"],
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

    utterances = build_utterances_from_segments(payload.get("segments"), words)
    provider_segments = []
    for segment_payload in payload.get("segments") or []:
        provider_segments.append(
            {
                "id": segment_payload.get("id"),
                "start": segment_payload.get("start"),
                "end": segment_payload.get("end"),
                "speaker_id": segment_payload.get("speaker_id"),
                "avg_logprob": segment_payload.get("avg_logprob"),
                "compression_ratio": segment_payload.get("compression_ratio"),
                "no_speech_prob": segment_payload.get("no_speech_prob"),
                "retry_count": segment_payload.get("retry_count"),
            }
        )

    raw_payload = build_raw_transcription_payload(
        provider="fireworks",
        model=model,
        audio_duration_seconds=payload.get("duration") or request_audio["audio_duration_seconds"],
        language=payload.get("language") or language,
        text=payload.get("text"),
        words=words,
        utterances=utterances,
        provider_metadata={
            "task": payload.get("task"),
            "raw_segments": provider_segments,
        },
    )
    cost_usd = compute_cost_by_duration(
        payload.get("duration") or request_audio["audio_duration_seconds"],
        unit_price=model_config["price_per_minute"],
        billing_unit="minute",
    )
    return _build_transcription_bundle(
        raw_payload,
        language_mkd=language_mkd,
        request_id=payload.get("request_id"),
        cost_usd=cost_usd,
        cost_source="official_pricing_table" if documented_model else "unavailable",
        cost_is_estimated=True,
        cost_lookup_error=None
        if documented_model
        else f"No documented pricing metadata is available for Fireworks model `{model}`.",
    )


def _normalize_timestamp_granularities(value):
    """Normalize Fireworks timestamp granularity input into ordered form fields."""
    if isinstance(value, str):
        values = [item.strip() for item in value.split(",") if item.strip()]
    else:
        values = [str(item).strip() for item in list(value or []) if str(item).strip()]
    if not values:
        values = ["segment"]
    for item in values:
        validate_choice(item, TIMESTAMP_GRANULARITIES, parameter_name="timestamp_granularities", provider="Fireworks", model="transcription")
    return values
