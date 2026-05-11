"""Speechmatics batch speech transcription with centralized pre/post-processing.

Implemented and validated with `teste/elevenlabs/audio.mp3` on 2026-04-22:
  - `standard`
  - `enhanced`

Official references:
  - Main docs: https://docs.speechmatics.com/
  - Pricing: https://www.speechmatics.com/pricing
  - Python SDK / batch examples: https://docs.speechmatics.com/sdk/python-sdk

Speechmatics exposes the accuracy variant through `operating_point`.
"""

import json
import time
from typing import Any

from .._apis._shared import (
    build_word_record,
    compute_cost_by_duration,
    get_required_api_key,
    reject_unknown_kwargs,
    request_with_retries,
    response_json,
)
from ..post_processing import _build_transcription_bundle, build_raw_transcription_payload
from ..pre_processing import build_request_audio

API_BASE_URL = "https://asr.api.speechmatics.com/v2"
SUPPORTED_MODELS = {
    "standard": {"price_per_hour": 0.45},
    "enhanced": {"price_per_hour": 0.75},
}
ADDON_PRICES_PER_HOUR = {
    "translation_config": 0.65,
    "summarization_config": 0.12,
    "auto_chapters_config": 0.40,
    "sentiment_analysis_config": 0.12,
    "topic_detection_config": 0.20,
}
SUPPORTED_KWARGS = {
    "language",
    "output_locale",
    "additional_vocab",
    "diarization",
    "channel_diarization_labels",
    "enable_entities",
    "audio_filtering_config",
    "transcript_filtering_config",
    "speaker_diarization_config",
    "speaker_sensitivity",
    "prefer_current_speaker",
    "speaker_identifiers",
    "notification_config",
    "tracking",
    "output_config",
    "translation_config",
    "language_identification_config",
    "summarization_config",
    "sentiment_analysis_config",
    "topic_detection_config",
    "auto_chapters_config",
    "audio_events_config",
    "language_mkd",
    "timeout_seconds",
}


def transcribe(
    audio_input: Any,
    model: str = "standard",
    **kwargs: Any,
) -> dict[str, Any]:
    """Transcribe audio with Speechmatics. See `transcribe/docs/speechmatics.md`."""
    if model not in SUPPORTED_MODELS:
        supported_models = ", ".join(sorted(SUPPORTED_MODELS))
        raise ValueError(f"Unsupported Speechmatics model '{model}'. Supported models: {supported_models}.")

    options = reject_unknown_kwargs("Speechmatics", model, kwargs, SUPPORTED_KWARGS)
    language = options.pop("language", "auto")
    diarization = options.pop("diarization", "speaker")
    enable_entities = bool(options.pop("enable_entities", False))
    speaker_sensitivity = options.pop("speaker_sensitivity", None)
    prefer_current_speaker = options.pop("prefer_current_speaker", None)
    language_mkd = options.pop("language_mkd", "en")
    timeout_seconds = float(options.pop("timeout_seconds", 300))

    request_audio = build_request_audio(audio_input)
    api_key = get_required_api_key("SPEECHMATICS_API_KEY")

    transcription_config = {
        "language": language,
        "operating_point": model,
        "diarization": diarization,
        "enable_entities": bool(enable_entities),
    }
    for key in (
        "output_locale",
        "additional_vocab",
        "channel_diarization_labels",
        "audio_filtering_config",
        "transcript_filtering_config",
        "speaker_diarization_config",
        "speaker_identifiers",
    ):
        value = options.pop(key, None)
        if value not in (None, "", [], {}):
            transcription_config[key] = value
    if speaker_sensitivity is not None or prefer_current_speaker is not None:
        speaker_diarization_config = dict(transcription_config.get("speaker_diarization_config") or {})
        if speaker_sensitivity is not None:
            speaker_diarization_config["speaker_sensitivity"] = float(speaker_sensitivity)
        if prefer_current_speaker is not None:
            speaker_diarization_config["prefer_current_speaker"] = bool(prefer_current_speaker)
        transcription_config["speaker_diarization_config"] = speaker_diarization_config

    config_payload = {"type": "transcription", "transcription_config": transcription_config}
    for key in (
        "notification_config",
        "tracking",
        "output_config",
        "translation_config",
        "language_identification_config",
        "summarization_config",
        "sentiment_analysis_config",
        "topic_detection_config",
        "auto_chapters_config",
        "audio_events_config",
    ):
        value = options.pop(key, None)
        if value not in (None, "", [], {}):
            config_payload[key] = value

    submit_response = request_with_retries(
        "POST",
        f"{API_BASE_URL}/jobs/",
        headers={"Authorization": f"Bearer {api_key}"},
        files={
            "data_file": (request_audio["file_name"], request_audio["audio_bytes"], request_audio["content_type"]),
            "config": (None, json.dumps(config_payload), "application/json"),
        },
        timeout=(15.0, float(timeout_seconds)),
    )
    submit_payload = response_json(submit_response)
    job_id = str(submit_payload.get("id") or "").strip()
    if not job_id:
        raise ValueError("Speechmatics submit response did not include a job id.")

    _wait_for_speechmatics_job(api_key, job_id)

    transcript_response = request_with_retries(
        "GET",
        f"{API_BASE_URL}/jobs/{job_id}/transcript",
        headers={"Authorization": f"Bearer {api_key}"},
        params={"format": "json-v2"},
        timeout=(15.0, 120.0),
    )
    payload = response_json(transcript_response)

    words, transcript_text, provider_entities, provider_events, provider_other_results = _parse_speechmatics_results(payload.get("results"))
    raw_payload = build_raw_transcription_payload(
        provider="speechmatics",
        model=model,
        audio_duration_seconds=((payload.get("job") or {}).get("duration") or request_audio["audio_duration_seconds"]),
        language=((payload.get("metadata") or {}).get("transcription_config") or {}).get("language") or language,
        text=transcript_text,
        words=words,
        provider_metadata={
            "job": payload.get("job"),
            "language_pack_info": (payload.get("metadata") or {}).get("language_pack_info"),
            "entities": provider_entities,
            "audio_events": provider_events,
            "other_results": provider_other_results,
        },
    )
    cost_usd = _compute_speechmatics_cost(
        ((payload.get("job") or {}).get("duration") or request_audio["audio_duration_seconds"]),
        model=model,
        config_payload=config_payload,
    )
    return _build_transcription_bundle(
        raw_payload,
        language_mkd=language_mkd,
        request_id=job_id,
        cost_usd=cost_usd,
        cost_source="official_pricing_table",
        cost_is_estimated=True,
    )


def _compute_speechmatics_cost(duration_seconds, *, model, config_payload):
    """Computes Speechmatics batch cost from the official hourly table."""
    total = compute_cost_by_duration(
        duration_seconds,
        unit_price=SUPPORTED_MODELS[model]["price_per_hour"],
        billing_unit="hour",
    )
    for config_key, addon_price in ADDON_PRICES_PER_HOUR.items():
        if config_payload.get(config_key) not in (None, "", [], {}):
            total += compute_cost_by_duration(
                duration_seconds,
                unit_price=addon_price,
                billing_unit="hour",
            )
    return round(total, 6)


def _parse_speechmatics_results(results):
    """Parses Speechmatics JSON-V2 results into normalized words and extra metadata."""
    words = []
    text_parts = []
    provider_entities = []
    provider_events = []
    provider_other_results = []

    for result_payload in list(results or []):
        item_type = str(result_payload.get("type") or "").strip().lower()
        alternatives = list(result_payload.get("alternatives") or [])
        alternative = alternatives[0] if alternatives else {}
        content = str(alternative.get("content") or "").strip()
        attaches_to = str(result_payload.get("attaches_to") or "").strip().lower()

        if content:
            if text_parts and attaches_to == "previous":
                text_parts[-1] = f"{text_parts[-1]}{content}"
            else:
                text_parts.append(content)

        if item_type == "word":
            normalized_word = build_word_record(
                content,
                result_payload.get("start_time"),
                result_payload.get("end_time"),
                speaker=alternative.get("speaker"),
            )
            if normalized_word:
                words.append(normalized_word)
            continue

        if item_type == "entity":
            provider_entities.append(
                {
                    "text": content,
                    "start": result_payload.get("start_time"),
                    "end": result_payload.get("end_time"),
                    "entity_class": alternative.get("entity_class"),
                    "spoken_form": alternative.get("spoken_form"),
                    "written_form": alternative.get("written_form"),
                    "speaker": alternative.get("speaker"),
                }
            )
            continue

        if item_type == "audio_event":
            provider_events.append(
                {
                    "text": content,
                    "start": result_payload.get("start_time"),
                    "end": result_payload.get("end_time"),
                    "speaker": alternative.get("speaker"),
                }
            )
            continue

        if item_type not in {"punctuation", ""}:
            provider_other_results.append(
                {
                    "type": item_type,
                    "start": result_payload.get("start_time"),
                    "end": result_payload.get("end_time"),
                    "content": content,
                    "speaker": alternative.get("speaker"),
                }
            )

    transcript_text = " ".join(text_parts).strip()
    return words, transcript_text, provider_entities, provider_events, provider_other_results


def _wait_for_speechmatics_job(api_key, job_id, max_polls=80, poll_interval_seconds=1.5):
    """Polls one Speechmatics batch job until it completes or fails."""
    last_payload = {}
    for _ in range(int(max_polls)):
        status_response = request_with_retries(
            "GET",
            f"{API_BASE_URL}/jobs/{job_id}",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=(15.0, 120.0),
        )
        last_payload = response_json(status_response)
        normalized_status = str((last_payload.get("job") or {}).get("status") or "").strip().lower()
        if normalized_status == "done":
            return last_payload
        if normalized_status in {"rejected", "failed"}:
            raise RuntimeError(f"Speechmatics job '{job_id}' failed with status '{normalized_status}': {last_payload}")
        time.sleep(float(poll_interval_seconds))

    raise TimeoutError(f"Speechmatics job '{job_id}' did not complete within the polling window: {last_payload}")
