"""Rev AI batch speech transcription with centralized pre/post-processing.

Implemented and validated with `teste/elevenlabs/audio.mp3` on 2026-04-22:
  - `machine`

Current public Rev AI offerings referenced in docs/pricing:
  - `machine` / Reverb ASR (default async API path)
  - low-cost / Reverb Turbo
  - foreign-language Reverb SKU (selected implicitly by non-English jobs)
  - Whisper Fusion
  - Whisper Large
  - Human transcription

Only `machine` is exposed by this adapter because it was the only route that
validated successfully for this project's diarized Portuguese contract.

Official references:
  - Async transcription options: https://docs.rev.ai/api/asynchronous/transcribers
  - Async reference: https://docs.rev.ai/api/asynchronous/reference
  - Current pricing: https://www.rev.ai/pricing
"""

import time
from typing import Any

from .._apis._shared import (
    build_utterance_record,
    build_word_record,
    compute_cost_by_duration,
    get_required_api_key,
    reject_unknown_kwargs,
    request_with_retries,
    response_json,
    validate_choice,
)
from ..post_processing import _build_transcription_bundle, build_raw_transcription_payload
from ..pre_processing import build_request_audio

API_BASE_URL = "https://api.rev.ai/speechtotext/v1"
SUPPORTED_MODELS = {"machine", "low_cost", "fusion"}
BLOCKED_MODELS = {
    "human": "Human transcription has a different cost/turnaround profile and is not compatible with this repository's low-cost live validation contract.",
}
REVERB_PRICE_PER_HOUR = 0.20
REVERB_FOREIGN_LANGUAGE_PRICE_PER_HOUR = 0.30
SUPPORTED_KWARGS = {
    "language",
    "skip_diarization",
    "skip_punctuation",
    "skip_postprocessing",
    "remove_disfluencies",
    "filter_profanity",
    "speaker_channel_count",
    "speakers_count",
    "diarization_type",
    "custom_vocabulary_id",
    "delete_after_seconds",
    "metadata",
    "notification_config",
    "language_mkd",
    "timeout_seconds",
}
DIARIZATION_TYPES = {"standard", "premium"}


def transcribe(
    audio_input: Any,
    model: str = "machine",
    **kwargs: Any,
) -> dict[str, Any]:
    """Transcribe audio with Rev AI. See `transcribe/docs/revai.md`."""
    if model in BLOCKED_MODELS:
        raise ValueError(f"Unsupported Rev AI model '{model}'. {BLOCKED_MODELS[model]}")
    if model not in SUPPORTED_MODELS:
        supported_models = ", ".join(sorted(SUPPORTED_MODELS | set(BLOCKED_MODELS)))
        raise ValueError(f"Unsupported Rev AI model '{model}'. Supported models: {supported_models}.")

    options = reject_unknown_kwargs("Rev AI", model, kwargs, SUPPORTED_KWARGS)
    language = options.pop("language", "en")
    normalized_language = str(language or "").strip().lower()
    if model in {"low_cost", "fusion"} and normalized_language and not normalized_language.startswith("en"):
        raise ValueError(f"Rev AI transcriber '{model}' only supports English transcription requests.")
    skip_diarization = bool(options.pop("skip_diarization", False))
    language_mkd = options.pop("language_mkd", "en")
    timeout_seconds = float(options.pop("timeout_seconds", 300))
    diarization_type = options.get("diarization_type")
    if diarization_type is not None:
        validate_choice(str(diarization_type), DIARIZATION_TYPES, parameter_name="diarization_type", provider="Rev AI", model=model)

    request_audio = build_request_audio(audio_input)
    api_key = get_required_api_key("REVAI_API_KEY")

    job_options = {
        "skip_diarization": bool(skip_diarization),
    }
    for key, value in options.items():
        if value in (None, "", [], {}):
            continue
        job_options[key] = value
    if language:
        job_options["language"] = language
    if model:
        job_options["transcriber"] = model

    submit_response = request_with_retries(
        "POST",
        f"{API_BASE_URL}/jobs",
        headers={"Authorization": f"Bearer {api_key}"},
        files={"media": (request_audio["file_name"], request_audio["audio_bytes"], request_audio["content_type"])},
        data={"options": _json_dump(job_options)},
        timeout=(15.0, float(timeout_seconds)),
    )
    submit_payload = response_json(submit_response)
    job_id = str(submit_payload.get("id") or "").strip()
    if not job_id:
        raise ValueError("Rev AI submit response did not include a job id.")

    job_payload = _wait_for_revai_job(api_key, job_id)

    transcript_response = request_with_retries(
        "GET",
        f"{API_BASE_URL}/jobs/{job_id}/transcript",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/vnd.rev.transcript.v1.0+json",
        },
        timeout=(15.0, 120.0),
    )
    payload = response_json(transcript_response)

    words, utterances, transcript_text, atmospherics = _parse_revai_transcript(payload.get("monologues"))
    effective_language = str(job_payload.get("language") or language or "").strip()
    raw_payload = build_raw_transcription_payload(
        provider="revai",
        model=model,
        audio_duration_seconds=job_payload.get("duration_seconds") or request_audio["audio_duration_seconds"],
        language=effective_language,
        text=transcript_text,
        words=words,
        utterances=utterances,
        provider_metadata={
            "job": job_payload,
            "atmospherics": atmospherics,
            "transcriber": job_payload.get("transcriber") or submit_payload.get("transcriber") or model,
        },
    )
    cost_usd = compute_cost_by_duration(
        job_payload.get("duration_seconds") or request_audio["audio_duration_seconds"],
        unit_price=_resolve_rev_price_per_hour(effective_language),
        billing_unit="hour",
        minimum_seconds=15.0,
        round_seconds=True,
    )
    return _build_transcription_bundle(
        raw_payload,
        language_mkd=language_mkd,
        request_id=job_id,
        cost_usd=cost_usd,
    )


def _resolve_rev_price_per_hour(language):
    """Returns the public Rev AI hourly rate for the effective language SKU."""
    normalized_language = str(language or "").strip().lower()
    if normalized_language.startswith("en"):
        return REVERB_PRICE_PER_HOUR
    return REVERB_FOREIGN_LANGUAGE_PRICE_PER_HOUR


def _parse_revai_transcript(monologues):
    """Parses Rev AI monologues into normalized words, utterances, and extras."""
    words = []
    utterances = []
    transcript_parts = []
    atmospherics = []

    for monologue in list(monologues or []):
        speaker = monologue.get("speaker", 0)
        utterance_words = []
        utterance_text_parts = []

        for element in list(monologue.get("elements") or []):
            element_type = str(element.get("type") or "").strip().lower()
            element_value = str(element.get("value") or "")

            if element_value:
                transcript_parts.append(element_value)
                utterance_text_parts.append(element_value)

            if element_type != "text":
                continue

            if element_value.startswith("<") and element_value.endswith(">"):
                atmospherics.append(
                    {
                        "text": element_value,
                        "start": element.get("ts"),
                        "end": element.get("end_ts"),
                        "speaker": speaker,
                    }
                )
                continue

            normalized_word = build_word_record(
                element_value,
                element.get("ts"),
                element.get("end_ts"),
                speaker=speaker,
            )
            if normalized_word:
                words.append(normalized_word)
                utterance_words.append(normalized_word)

        if utterance_words:
            utterance_record = build_utterance_record(
                utterance_words[0].get("start"),
                utterance_words[-1].get("end"),
                text="".join(utterance_text_parts),
                speaker=speaker,
                words=utterance_words,
            )
            if utterance_record:
                utterances.append(utterance_record)

    return words, utterances, "".join(transcript_parts).strip(), atmospherics


def _json_dump(payload):
    import json

    return json.dumps(payload, ensure_ascii=True)


def _wait_for_revai_job(api_key, job_id, max_polls=80, poll_interval_seconds=1.5):
    """Polls one Rev AI async job until it completes or fails."""
    last_payload = {}
    for _ in range(int(max_polls)):
        status_response = request_with_retries(
            "GET",
            f"{API_BASE_URL}/jobs/{job_id}",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=(15.0, 120.0),
        )
        last_payload = response_json(status_response)
        normalized_status = str(last_payload.get("status") or "").strip().lower()
        if normalized_status == "transcribed":
            return last_payload
        if normalized_status == "failed":
            raise RuntimeError(f"Rev AI job '{job_id}' failed: {last_payload}")
        time.sleep(float(poll_interval_seconds))

    raise TimeoutError(f"Rev AI job '{job_id}' did not complete within the polling window: {last_payload}")
