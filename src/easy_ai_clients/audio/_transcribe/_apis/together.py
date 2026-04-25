"""Together AI batch speech transcription with centralized pre/post-processing.

Implemented and validated with `teste/elevenlabs/audio.mp3` on 2026-04-22:
  - `openai/whisper-large-v3`

Current Together serverless STT reference:
  - `openai/whisper-large-v3`
  - `nvidia/parakeet-tdt-0.6b-v3`

Official references:
  - STT guide: https://docs.together.ai/docs/speech-to-text
  - Current serverless model catalog/pricing: https://docs.together.ai/docs/serverless-models

`nvidia/parakeet-tdt-0.6b-v3` is intentionally not exposed by this adapter because
Together currently rejects `diarize=true` for that model, and this project's public
contract requires speaker attribution compatible with `words[].speaker_id`.
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
    validate_choice,
    validate_number_range,
)
from ..post_processing import _build_transcription_bundle, build_raw_transcription_payload
from ..pre_processing import build_request_audio

API_URL = "https://api.together.xyz/v1/audio/transcriptions"
SUPPORTED_MODELS = {
    "openai/whisper-large-v3": {
        "price_per_minute": 0.0015,
        "supports_diarization": True,
    },
    "nvidia/parakeet-tdt-0.6b-v3": {
        "price_per_minute": 0.0015,
        "supports_diarization": False,
    },
    "deepgram/flux": {
        "price_per_minute": 0.0015,
        "supports_diarization": True,
    },
    "deepgram/nova-3-en": {
        "price_per_minute": 0.0015,
        "supports_diarization": True,
    },
    "deepgram/nova-3-multi": {
        "price_per_minute": 0.0015,
        "supports_diarization": True,
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
    language = options.pop("language", None)
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
    cost_usd = compute_cost_by_duration(
        payload.get("duration") or request_audio["audio_duration_seconds"],
        unit_price=SUPPORTED_MODELS[model]["price_per_minute"],
        billing_unit="minute",
    )
    return _build_transcription_bundle(
        raw_payload,
        language_mkd=language_mkd,
        request_id=payload.get("id"),
        cost_usd=cost_usd,
    )


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
