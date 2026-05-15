"""ElevenLabs batch speech transcription with centralized pre/post-processing.

Implemented and validated with `teste/elevenlabs/audio.mp3` on 2026-04-22:
  - `scribe_v1`
  - `scribe_v2`

Official references:
  - STT endpoint/models/params: https://elevenlabs.io/docs/api-reference/speech-to-text/convert
  - STT capability overview: https://elevenlabs.io/docs/capabilities/speech-to-text
  - Current API pricing: https://elevenlabs.io/pricing/api/
"""

import json
from typing import Any

from .._apis._shared import (
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

API_URL = "https://api.elevenlabs.io/v1/speech-to-text"
DOCUMENTED_MODELS = {
    "scribe_v1": {"price_per_hour": 0.22},
    "scribe_v2": {"price_per_hour": 0.22},
}
_UNKNOWN_MODEL_METADATA = {"price_per_hour": 0.0}
ENTITY_DETECTION_PRICE_PER_HOUR = 0.070
KEYTERM_PROMPTING_PRICE_PER_HOUR = 0.050
TIMESTAMP_GRANULARITIES = {"word", "character", "none"}
ENTITY_REDACTION_MODES = {"redacted", "entity_type", "enumerated_entity_type"}
DOCUMENTED_KWARGS = {
    "language_code",
    "diarize",
    "num_speakers",
    "diarization_threshold",
    "timestamps_granularity",
    "tag_audio_events",
    "entity_detection",
    "entity_redaction",
    "entity_redaction_mode",
    "keyterms",
    "no_verbatim",
    "detect_speaker_roles",
    "enable_logging",
    "language_mkd",
    "timeout_seconds",
}


def transcribe(
    audio_input: Any,
    model: str = "scribe_v2",
    **kwargs: Any,
) -> dict[str, Any]:
    """Transcribe audio with ElevenLabs. See `transcribe/docs/elevenlabs.md`."""
    documented_model = model in DOCUMENTED_MODELS
    options = reject_unknown_kwargs("ElevenLabs", model, kwargs, DOCUMENTED_KWARGS)
    language_code = options.pop("language_code", None)
    diarize = bool(options.pop("diarize", True))
    num_speakers = options.pop("num_speakers", None)
    diarization_threshold = options.pop("diarization_threshold", None)
    timestamps_granularity = str(options.pop("timestamps_granularity", "word")).strip()
    validate_choice(timestamps_granularity, TIMESTAMP_GRANULARITIES, parameter_name="timestamps_granularity", provider="ElevenLabs", model=model)
    tag_audio_events = bool(options.pop("tag_audio_events", True))
    entity_detection = options.pop("entity_detection", None)
    entity_redaction = options.pop("entity_redaction", None)
    entity_redaction_mode = options.pop("entity_redaction_mode", None)
    keyterms = options.pop("keyterms", None)
    no_verbatim = bool(options.pop("no_verbatim", False))
    detect_speaker_roles = bool(options.pop("detect_speaker_roles", False))
    enable_logging = bool(options.pop("enable_logging", True))
    language_mkd = options.pop("language_mkd", "en")
    timeout_seconds = float(options.pop("timeout_seconds", 300))
    if diarization_threshold is not None:
        validate_number_range(diarization_threshold, parameter_name="diarization_threshold", provider="ElevenLabs", model=model, minimum=0.1, maximum=0.4)
    if entity_redaction_mode is not None:
        validate_choice(entity_redaction_mode, ENTITY_REDACTION_MODES, parameter_name="entity_redaction_mode", provider="ElevenLabs", model=model)

    request_audio = build_request_audio(audio_input)
    api_key = get_required_api_key("ELEVENLABS_API_KEY")

    form_fields = [
        ("model_id", model),
        ("file_format", _elevenlabs_file_format(request_audio)),
        ("timestamps_granularity", timestamps_granularity),
        ("diarize", "true" if diarize else "false"),
        ("tag_audio_events", "true" if tag_audio_events else "false"),
    ]
    if language_code:
        form_fields.append(("language_code", language_code))
    if num_speakers is not None:
        form_fields.append(("num_speakers", int(num_speakers)))
    if diarization_threshold is not None:
        form_fields.append(("diarization_threshold", float(diarization_threshold)))
    if no_verbatim:
        form_fields.append(("no_verbatim", "true"))
    if detect_speaker_roles:
        form_fields.append(("detect_speaker_roles", "true"))
    if entity_detection not in (None, False, "", []):
        entity_detection_value = entity_detection
        if isinstance(entity_detection, list | tuple | set):
            entity_detection_value = json.dumps(list(entity_detection), ensure_ascii=True)
        form_fields.append(("entity_detection", entity_detection_value))
    if entity_redaction not in (None, False, "", []):
        entity_redaction_value = entity_redaction
        if isinstance(entity_redaction, list | tuple | set):
            entity_redaction_value = json.dumps(list(entity_redaction), ensure_ascii=True)
        form_fields.append(("entity_redaction", entity_redaction_value))
    if entity_redaction_mode:
        form_fields.append(("entity_redaction_mode", entity_redaction_mode))
    for keyterm in list(keyterms or []):
        keyterm_text = str(keyterm or "").strip()
        if keyterm_text:
            form_fields.append(("keyterms", keyterm_text))
    for key, value in options.items():
        if value not in (None, "", [], {}):
            form_fields.append((key, value))

    response = request_with_retries(
        "POST",
        API_URL,
        headers={"xi-api-key": api_key},
        params={"enable_logging": "true" if enable_logging else "false"},
        data=form_fields,
        files={"file": (request_audio["file_name"], request_audio["audio_bytes"], request_audio["content_type"])},
        timeout=(15.0, float(timeout_seconds)),
    )
    payload = response_json(response)

    words = []
    audio_events = []
    for word_payload in payload.get("words") or []:
        item_type = str(word_payload.get("type") or "word").strip().lower()
        if item_type == "spacing":
            continue
        if item_type == "audio_event":
            audio_events.append(
                {
                    "text": str(word_payload.get("text") or "").strip(),
                    "start": word_payload.get("start"),
                    "end": word_payload.get("end"),
                }
            )
            continue

        normalized_word = build_word_record(
            word_payload.get("text"),
            word_payload.get("start"),
            word_payload.get("end"),
            speaker=word_payload.get("speaker_id") or word_payload.get("speaker"),
        )
        if normalized_word:
            words.append(normalized_word)

    raw_payload = build_raw_transcription_payload(
        provider="elevenlabs",
        model=model,
        audio_duration_seconds=payload.get("audio_duration_secs") or request_audio["audio_duration_seconds"],
        language=language_code or payload.get("language_code"),
        language_confidence=payload.get("language_probability"),
        text=payload.get("text"),
        words=words,
        provider_metadata={
            "audio_events": audio_events,
            "entities": payload.get("entities"),
            "language_probability": payload.get("language_probability"),
            "provider_language_code": payload.get("language_code"),
        },
    )
    cost_usd = _compute_elevenlabs_cost(
        payload.get("audio_duration_secs") or request_audio["audio_duration_seconds"],
        model=model,
        entity_detection=entity_detection,
        keyterms=keyterms,
    ) if documented_model else 0.0
    return _build_transcription_bundle(
        raw_payload,
        language_mkd=language_mkd,
        request_id=payload.get("transcription_id"),
        cost_usd=cost_usd,
        cost_source="official_pricing_table" if documented_model else "unavailable",
        cost_is_estimated=True,
        cost_lookup_error=None
        if documented_model
        else f"No documented pricing metadata is available for ElevenLabs model `{model}`.",
    )


def _elevenlabs_file_format(request_audio):
    """Returns the ElevenLabs file_format value that matches the prepared payload."""
    upload_format = str(request_audio.get("upload_format") or "").strip().lower()
    if not upload_format:
        file_name = str(request_audio.get("file_name") or "").strip().lower()
        if "." in file_name:
            upload_format = file_name.rsplit(".", 1)[-1]
    if not upload_format:
        content_type = str(request_audio.get("content_type") or "").strip().lower()
        if content_type in {"audio/wav", "audio/wave", "audio/x-wav"}:
            upload_format = "wav"

    if request_audio.get("normalized", True) and upload_format in {"wav", "wave"}:
        return "pcm_s16le_16"
    return "other"


def _compute_elevenlabs_cost(duration_seconds, *, model, entity_detection=None, keyterms=None):
    """Computes ElevenLabs Scribe cost from the official hourly table."""
    minimum_seconds = 20.0 if len(list(keyterms or [])) > 100 else 0.0
    base_cost = compute_cost_by_duration(
        duration_seconds,
        unit_price=DOCUMENTED_MODELS.get(model, _UNKNOWN_MODEL_METADATA)["price_per_hour"],
        billing_unit="hour",
        minimum_seconds=minimum_seconds,
    )
    addon_cost = 0.0
    if entity_detection not in (None, False, "", []):
        addon_cost += compute_cost_by_duration(
            duration_seconds,
            unit_price=ENTITY_DETECTION_PRICE_PER_HOUR,
            billing_unit="hour",
            minimum_seconds=minimum_seconds,
        )
    if keyterms:
        addon_cost += compute_cost_by_duration(
            duration_seconds,
            unit_price=KEYTERM_PROMPTING_PRICE_PER_HOUR,
            billing_unit="hour",
            minimum_seconds=minimum_seconds,
        )
    return round(base_cost + addon_cost, 6)
