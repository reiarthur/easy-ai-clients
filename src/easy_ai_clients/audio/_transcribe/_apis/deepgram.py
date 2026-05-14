"""Provides Deepgram transcription with centralized pre/post-processing.

Last updated: 2026-04-22
"""

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import urlencode

import requests

from ..post_processing import (
    _build_transcription_bundle,
    _sanitize_cost_lookup_error,
    build_raw_transcription_payload,
)
from ..pre_processing import (
    _clean_text,
    _safe_float,
    build_balanced_spans,
    export_segment_as_wav,
    load_audio,
)
from ._shared import compute_cost_by_duration, round_cost

MAX_CONCURRENT_NOVA_PRERECORDED = 50
MAX_CONCURRENT_WHISPER_PRERECORDED = 3
DOCUMENTED_MODELS = {
    "nova-3",
    "nova-3-general",
    "nova-3-medical",
    "nova-2",
    "nova-2-general",
    "nova-2-meeting",
    "nova-2-phonecall",
    "nova-2-voicemail",
    "nova-2-finance",
    "nova-2-conversationalai",
    "nova-2-video",
    "nova-2-medical",
    "nova-2-drivethru",
    "nova-2-automotive",
    "nova-2-atc",
    "nova",
    "nova-general",
    "nova-phonecall",
    "enhanced",
    "enhanced-general",
    "enhanced-meeting",
    "enhanced-phonecall",
    "enhanced-finance",
    "base-meeting",
    "base-phonecall",
    "base-voicemail",
    "base-finance",
    "base-conversationalai",
    "base-video",
    "whisper",
    "whisper-small",
    "whisper-medium",
    "whisper-large",
}
DOCUMENTED_KWARGS = {
    "fallback_model",
    "concurrency",
    "language",
    "paragraphs",
    "filler_words",
    "numerals",
    "measurements",
    "detect_entities",
    "language_mkd",
    "smart_format",
    "utterances",
    "diarize",
    "punctuate",
    "detect_language",
    "callback",
    "callback_method",
    "extra",
    "sentiment",
    "summarize",
    "tag",
    "topics",
    "custom_topic",
    "custom_topic_mode",
    "intents",
    "custom_intent",
    "custom_intent_mode",
    "dictation",
    "encoding",
    "keyterm",
    "keywords",
    "multichannel",
    "profanity_filter",
    "redact",
    "replace",
    "search",
    "version",
    "mip_opt_out",
    "utt_split",
}

_MAX_RETRIES = 3
_REQUEST_TIMEOUT = (20, 1200)
_MANAGEMENT_TIMEOUT = (10, 60)
_NOVA_3_MONOLINGUAL_PRICE_PER_MINUTE = 0.0077
_NOVA_3_MULTILINGUAL_PRICE_PER_MINUTE = 0.0092
_NOVA_3_DIARIZATION_PRICE_PER_MINUTE = 0.0020


def transcribe(
    audio_input: Any,
    model: str = "nova-2",
    **kwargs: Any,
) -> dict[str, Any]:
    """Transcribe audio with Deepgram. See `transcribe/docs/deepgram.md`."""
    options = _reject_unknown_kwargs(model, kwargs)
    primary_model = _clean_text(model) or "nova-2"
    _validate_model(primary_model)
    fallback_model = options.pop("fallback_model", None)
    resolved_fallback_model = _clean_text(fallback_model) if fallback_model is not None else None
    if resolved_fallback_model:
        _validate_model(resolved_fallback_model)
    concurrency = options.pop("concurrency", MAX_CONCURRENT_NOVA_PRERECORDED)
    resolved_language = _clean_text(options.pop("language", None))
    paragraphs = bool(options.pop("paragraphs", True))
    filler_words = bool(options.pop("filler_words", True))
    numerals = bool(options.pop("numerals", True))
    measurements = bool(options.pop("measurements", True))
    detect_entities = options.pop("detect_entities", None)
    language_mkd = options.pop("language_mkd", "en")
    provider_params = _normalize_extra_request_params(options)
    diarize_enabled = _request_flag(provider_params.get("diarize"), default=True)
    should_detect_entities = bool(detect_entities)
    if detect_entities is None:
        should_detect_entities = resolved_language.lower().startswith("en") and not _is_whisper_model(primary_model)

    audio = load_audio(audio_input)
    spans = build_balanced_spans(audio)
    audio_duration_seconds = len(audio) / 1000.0
    request_ids = []
    successful_model = primary_model

    if not spans:
        merged_result = _merge_chunk_results([])
    else:
        merged_result, primary_request_ids, primary_error = _transcribe_with_model(
            audio,
            spans,
            primary_model,
            concurrency,
            language=resolved_language,
            paragraphs=paragraphs,
            filler_words=filler_words,
            numerals=numerals,
            measurements=measurements,
            detect_entities=should_detect_entities,
            extra_request_params=provider_params,
        )
        request_ids.extend(primary_request_ids)

        if primary_error is not None:
            if not resolved_fallback_model or resolved_fallback_model == primary_model:
                raise primary_error
            successful_model = resolved_fallback_model
            merged_result, fallback_request_ids, fallback_error = _transcribe_with_model(
                audio,
                spans,
                resolved_fallback_model,
                concurrency,
                language=resolved_language,
                paragraphs=paragraphs,
                filler_words=filler_words,
                numerals=numerals,
                measurements=measurements,
                detect_entities=should_detect_entities,
                extra_request_params=provider_params,
            )
            request_ids.extend(fallback_request_ids)
            if fallback_error is not None:
                raise fallback_error from primary_error

    raw_payload = _build_raw_transcription_payload(
        merged_result,
        audio_duration_seconds=audio_duration_seconds,
        model_name=successful_model,
        requested_language=resolved_language,
        requested_model=primary_model,
        fallback_model=resolved_fallback_model,
        diarize=diarize_enabled,
    )
    cost_metadata = _resolve_deepgram_cost_metadata(
        request_ids=request_ids,
        model_name=successful_model,
        audio_duration_seconds=audio_duration_seconds,
        diarize=diarize_enabled,
    )
    return _build_transcription_bundle(
        raw_payload,
        language_mkd=language_mkd,
        request_id=request_ids,
        **cost_metadata,
    )


def update_cost(result):
    """Refresh Deepgram transcription cost metadata through Management/Usage lookup."""
    if not isinstance(result, dict):
        raise TypeError("audio.update_cost result must be a transcription result dictionary.")

    cost_metadata = _resolve_deepgram_cost_metadata(
        request_ids=result.get("request_id"),
        model_name=result.get("model"),
        audio_duration_seconds=_safe_float(result.get("duration"), 0.0) / 1000.0,
        diarize=_request_flag(
            ((result.get("provider_metadata") or {}).get("request_parameters") or {}).get("diarize"),
            default=True,
        ),
    )
    result["cost_usd"] = cost_metadata["cost_usd"]
    result["cost_source"] = cost_metadata["cost_source"]
    result["cost_is_estimated"] = cost_metadata["cost_is_estimated"]
    result["cost_lookup_error"] = _sanitize_cost_lookup_error(cost_metadata["cost_lookup_error"])
    return result

def _get_api_key():
    """Returns the Deepgram API key from the environment."""
    api_key = str(os.getenv("DEEPGRAM_API_KEY") or "").strip()
    if not api_key:
        raise ValueError("DEEPGRAM_API_KEY is not defined in the environment.")
    return api_key


def _to_decimal(value, default=None):
    """Converts a scalar to Decimal when possible."""
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return default


def _normalize_model_name(model_name):
    """Normalizes model names for comparisons."""
    return _clean_text(model_name).lower()


def _is_whisper_model(model_name):
    """Returns whether a model belongs to Whisper Cloud."""
    return _normalize_model_name(model_name).startswith("whisper")


def _get_model_concurrency_limit(model_name):
    """Returns the documented concurrency limit for the requested model."""
    if _is_whisper_model(model_name):
        return MAX_CONCURRENT_WHISPER_PRERECORDED
    return MAX_CONCURRENT_NOVA_PRERECORDED


def _coerce_concurrency(requested_concurrency, model_name, spans_count):
    """Applies the model-specific concurrency cap."""
    spans_count = max(1, int(spans_count or 1))
    try:
        requested_value = int(requested_concurrency)
    except (TypeError, ValueError):
        requested_value = _get_model_concurrency_limit(model_name)
    return max(1, min(requested_value, _get_model_concurrency_limit(model_name), spans_count))


def _normalize_request_id_list(request_id):
    """Returns a deduplicated request-id list preserving input order."""
    if isinstance(request_id, str):
        request_items = [request_id]
    elif isinstance(request_id, list | tuple | set):
        request_items = list(request_id)
    else:
        request_items = []

    normalized_request_ids = []
    for item in request_items:
        cleaned_item = _clean_text(item)
        if cleaned_item and cleaned_item not in normalized_request_ids:
            normalized_request_ids.append(cleaned_item)
    return normalized_request_ids


def _post_audio(session, audio_bytes, content_type, request_params, api_key):
    """Sends audio to Deepgram with retries and returns the JSON response."""
    request_url = f"https://api.deepgram.com/v1/listen?{urlencode(request_params, doseq=True)}"
    request_headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": content_type,
    }

    last_error = None
    for attempt_number in range(1, _MAX_RETRIES + 1):
        try:
            response = session.post(
                request_url,
                headers=request_headers,
                data=audio_bytes,
                timeout=_REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            last_error = error
            if attempt_number < _MAX_RETRIES:
                time.sleep(2 ** attempt_number)

    response = getattr(last_error, "response", None)
    if response is not None:
        try:
            error_payload = response.json()
        except Exception:
            error_payload = response.text
        raise RuntimeError(
            f"Deepgram audio upload failed with status {response.status_code}: {error_payload}"
        ) from last_error

    raise RuntimeError("Deepgram audio upload failed after multiple retries.") from last_error


def _shift_timestamps(result_payload, offset_seconds):
    """Offsets word and utterance timestamps after chunk merging."""
    response_root = (result_payload.get("results") or {}) if isinstance(result_payload, dict) else {}
    utterances = response_root.get("utterances", []) or []
    for utterance in utterances:
        if utterance.get("start") is not None:
            utterance["start"] = _safe_float(utterance["start"], 0.0) + offset_seconds
        if utterance.get("end") is not None:
            utterance["end"] = _safe_float(utterance["end"], 0.0) + offset_seconds
        for word in utterance.get("words", []) or []:
            if word.get("start") is not None:
                word["start"] = _safe_float(word["start"], 0.0) + offset_seconds
            if word.get("end") is not None:
                word["end"] = _safe_float(word["end"], 0.0) + offset_seconds

    channels = response_root.get("channels", []) or []
    for channel in channels:
        for alternative in channel.get("alternatives", []) or []:
            for word in alternative.get("words", []) or []:
                if word.get("start") is not None:
                    word["start"] = _safe_float(word["start"], 0.0) + offset_seconds
                if word.get("end") is not None:
                    word["end"] = _safe_float(word["end"], 0.0) + offset_seconds


def _max_speaker_id(result_payload):
    """Returns the highest speaker identifier present in a Deepgram response."""
    highest_speaker_id = -1
    utterances = ((result_payload.get("results") or {}).get("utterances") or []) if isinstance(result_payload, dict) else []

    for utterance in utterances:
        if utterance.get("speaker") is not None:
            try:
                highest_speaker_id = max(highest_speaker_id, int(utterance.get("speaker")))
            except Exception:
                pass
        for word in utterance.get("words", []) or []:
            if word.get("speaker") is not None:
                try:
                    highest_speaker_id = max(highest_speaker_id, int(word.get("speaker")))
                except Exception:
                    pass
    return highest_speaker_id


def _shift_speaker_ids(result_payload, speaker_offset):
    """Offsets chunk-local speaker identifiers to avoid collisions after merging."""
    if speaker_offset <= 0:
        return

    response_root = (result_payload.get("results") or {}) if isinstance(result_payload, dict) else {}
    utterances = response_root.get("utterances", []) or []
    for utterance in utterances:
        if utterance.get("speaker") is not None:
            try:
                utterance["speaker"] = int(utterance["speaker"]) + speaker_offset
            except Exception:
                pass
        for word in utterance.get("words", []) or []:
            if word.get("speaker") is not None:
                try:
                    word["speaker"] = int(word["speaker"]) + speaker_offset
                except Exception:
                    pass

    channels = response_root.get("channels", []) or []
    for channel in channels:
        for alternative in channel.get("alternatives", []) or []:
            for word in alternative.get("words", []) or []:
                if word.get("speaker") is not None:
                    try:
                        word["speaker"] = int(word["speaker"]) + speaker_offset
                    except Exception:
                        pass


def _merge_chunk_results(chunk_results):
    """Merges multiple ordered chunk responses into a single Deepgram-like payload."""
    if not chunk_results:
        return {
            "metadata": {"duration": 0.0},
            "results": {
                "channels": [{"alternatives": [{"transcript": "", "words": []}]}],
                "utterances": [],
            },
        }

    ordered_payloads = [payload for _, payload in sorted(chunk_results, key=lambda item: item[0])]
    metadata = dict(ordered_payloads[0].get("metadata", {}) or {})
    metadata["duration"] = sum(_safe_float((payload.get("metadata") or {}).get("duration"), 0.0) for payload in ordered_payloads)
    metadata["warnings"] = []

    transcripts = []
    merged_words = []
    utterances = []
    detected_language = None

    for payload in ordered_payloads:
        payload_metadata = payload.get("metadata", {}) or {}
        metadata["warnings"].extend(payload_metadata.get("warnings", []) or [])

        channels = payload.get("results", {}).get("channels", []) or [{}]
        channel = channels[0]
        alternative = (channel.get("alternatives", []) or [{}])[0]
        transcripts.append(alternative.get("transcript", "") or "")
        merged_words.extend(alternative.get("words", []) or [])
        utterances.extend(payload.get("results", {}).get("utterances", []) or [])
        if detected_language is None:
            detected_language = channel.get("detected_language")

    return {
        "metadata": metadata,
        "results": {
            "channels": [
                {
                    "detected_language": detected_language,
                    "alternatives": [
                        {
                            "transcript": _clean_text(" ".join(transcripts)),
                            "words": merged_words,
                        }
                    ],
                }
            ],
            "utterances": utterances,
        },
    }


def _transcribe_chunk(audio, span, request_params, api_key):
    """Uploads one audio chunk and returns the raw Deepgram response."""
    chunk_start, chunk_end = span
    audio_bytes, content_type = export_segment_as_wav(audio[chunk_start:chunk_end])
    with requests.Session() as session:
        return _post_audio(session, audio_bytes, content_type, request_params, api_key)


def _normalize_request_params(
    model_name,
    *,
    language=None,
    paragraphs=True,
    filler_words=True,
    numerals=True,
    measurements=True,
    detect_entities=False,
    extra_request_params=None,
):
    """Returns the Deepgram listen parameters used by this integration."""
    request_params = {
        "model": model_name,
        "smart_format": "true",
        "utterances": "true",
        "diarize": "true",
        "punctuate": "true",
    }
    if language:
        request_params["language"] = language
    else:
        request_params["detect_language"] = "true"
    if paragraphs:
        request_params["paragraphs"] = "true"
    if filler_words:
        request_params["filler_words"] = "true"
    if numerals:
        request_params["numerals"] = "true"
    if measurements:
        request_params["measurements"] = "true"
    if detect_entities:
        request_params["detect_entities"] = "true"
    for key, value in dict(extra_request_params or {}).items():
        if value in (None, "", [], {}):
            continue
        request_params[key] = _stringify_query_value(value)
    return request_params


def _should_retry_without_language(error):
    """Returns whether the model should be retried with automatic language detection."""
    error_message = str(error or "").lower()
    return (
        "model/language/tier combination" in error_message
        or "project does not have access to the requested model" in error_message
    )


def _execute_model_transcription(audio, spans, request_params, api_key, actual_concurrency):
    """Runs one Deepgram request-parameter variant across all chunks."""
    results_by_index = [None] * len(spans)
    request_ids = []

    remaining_indices = list(range(len(spans)))
    if remaining_indices:
        parallel_concurrency = max(1, min(actual_concurrency, len(remaining_indices)))

        if parallel_concurrency == 1:
            with requests.Session() as session:
                for chunk_index in remaining_indices:
                    chunk_start, chunk_end = spans[chunk_index]
                    chunk_audio = audio[chunk_start:chunk_end]
                    chunk_result = _post_audio(
                        session,
                        *export_segment_as_wav(chunk_audio),
                        request_params,
                        api_key,
                    )
                    results_by_index[chunk_index] = chunk_result
                    request_id = _clean_text((chunk_result.get("metadata") or {}).get("request_id"))
                    if request_id:
                        request_ids.append(request_id)
        else:
            with ThreadPoolExecutor(max_workers=parallel_concurrency) as executor:
                future_map = {
                    executor.submit(_transcribe_chunk, audio, spans[chunk_index], request_params, api_key): chunk_index
                    for chunk_index in remaining_indices
                }
                for future in as_completed(future_map):
                    chunk_index = future_map[future]
                    chunk_result = future.result()
                    results_by_index[chunk_index] = chunk_result
                    request_id = _clean_text((chunk_result.get("metadata") or {}).get("request_id"))
                    if request_id:
                        request_ids.append(request_id)

    ordered_chunk_results = []
    speaker_offset = 0
    for chunk_index, chunk_result in enumerate(results_by_index):
        if chunk_result is None:
            continue
        _shift_speaker_ids(chunk_result, speaker_offset)
        highest_speaker_id = _max_speaker_id(chunk_result)
        if highest_speaker_id >= 0:
            speaker_offset = highest_speaker_id + 1
        _shift_timestamps(chunk_result, spans[chunk_index][0] / 1000.0)
        ordered_chunk_results.append((chunk_index, chunk_result))

    return _merge_chunk_results(ordered_chunk_results), request_ids


def _transcribe_with_model(
    audio,
    spans,
    model_name,
    concurrency,
    *,
    language=None,
    paragraphs=True,
    filler_words=True,
    numerals=True,
    measurements=True,
    detect_entities=False,
    extra_request_params=None,
):
    """Transcribes all spans with one model."""
    if not spans:
        return _merge_chunk_results([]), [], None

    api_key = _get_api_key()
    actual_concurrency = _coerce_concurrency(concurrency, model_name, len(spans))
    request_variants = [
        _normalize_request_params(
            model_name,
            language=language,
            paragraphs=paragraphs,
            filler_words=filler_words,
            numerals=numerals,
            measurements=measurements,
            detect_entities=detect_entities,
            extra_request_params=extra_request_params,
        )
    ]
    if language:
        request_variants.append(
            _normalize_request_params(
                model_name,
                language=None,
                paragraphs=paragraphs,
                filler_words=filler_words,
                numerals=numerals,
                measurements=measurements,
                detect_entities=detect_entities,
                extra_request_params=extra_request_params,
            )
        )

    request_ids = []
    last_error = None
    for request_params in request_variants:
        try:
            merged_result, variant_request_ids = _execute_model_transcription(
                audio,
                spans,
                request_params,
                api_key,
                actual_concurrency,
            )
            request_ids.extend(variant_request_ids)
            return merged_result, request_ids, None
        except Exception as error:
            last_error = error
            if not language or request_params.get("language") is None or not _should_retry_without_language(error):
                break

    runtime_error = RuntimeError(f"Transcription with model '{model_name}' failed.")
    runtime_error.__cause__ = last_error
    return None, request_ids, runtime_error


def _build_raw_transcription_payload(
    merged_result,
    audio_duration_seconds,
    model_name,
    requested_language=None,
    requested_model=None,
    fallback_model=None,
    diarize=True,
):
    """Builds the raw payload consumed by transcription post-processing."""
    result_root = (merged_result.get("results") or {}) if isinstance(merged_result, dict) else {}
    channels = result_root.get("channels", []) or [{}]
    channel = channels[0]
    alternative = (channel.get("alternatives", []) or [{}])[0]
    metadata = (merged_result.get("metadata") or {}) if isinstance(merged_result, dict) else {}
    return build_raw_transcription_payload(
        provider="deepgram",
        model=model_name,
        audio_duration_seconds=audio_duration_seconds,
        language=channel.get("detected_language") or requested_language,
        language_confidence=channel.get("language_confidence"),
        text=alternative.get("transcript"),
        provider_metadata={
            "warnings": metadata.get("warnings"),
            "model_info": metadata.get("model_info"),
            "models": metadata.get("models"),
            "transaction_key": metadata.get("transaction_key"),
            "created": metadata.get("created"),
            "sha256": metadata.get("sha256"),
            "paragraphs": alternative.get("paragraphs"),
            "summary": result_root.get("summary"),
            "entities": alternative.get("entities"),
            "requested_model": requested_model or model_name,
            "actual_model": model_name,
            "fallback_model": fallback_model,
            "request_parameters": {"diarize": bool(diarize)},
        },
        result=merged_result,
    )


def _list_project_ids(session):
    """Lists available Deepgram project IDs for the active API key."""
    response = session.get("https://api.deepgram.com/v1/projects", timeout=_MANAGEMENT_TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    project_ids = []
    for project in payload.get("projects", []) or []:
        project_id = _clean_text(project.get("project_id"))
        if project_id and project_id not in project_ids:
            project_ids.append(project_id)
    return project_ids


def _format_lookup_error(error):
    """Builds a sanitized Deepgram lookup error string."""
    response = getattr(error, "response", None)
    if response is None:
        return str(error or "Deepgram usage lookup failed.")

    message = ""
    try:
        payload = response.json()
        if isinstance(payload, dict):
            message = (
                payload.get("err_msg")
                or payload.get("message")
                or payload.get("detail")
                or str(payload.get("error") or "")
            )
    except ValueError:
        message = str(response.text or "")
    message = _clean_text(message)[:300]
    if message:
        return f"Deepgram usage lookup failed with HTTP {response.status_code}: {message}"
    return f"Deepgram usage lookup failed with HTTP {response.status_code}."


def _resolve_candidate_project_ids(session):
    """Returns project IDs to try when looking up exact request cost."""
    env_project_id = _clean_text(os.getenv("DEEPGRAM_PROJECT_ID"))
    if env_project_id:
        return [env_project_id], None

    try:
        return _list_project_ids(session), None
    except requests.RequestException as error:
        return [], _format_lookup_error(error)


def _extract_exact_cost_from_lookup(lookup_payload):
    """Extracts the exact USD cost from a management lookup payload."""
    lookup_payload = lookup_payload or {}
    request_payload = lookup_payload.get("request") or {}
    response_payload = request_payload.get("response") or {}
    top_level_response_payload = lookup_payload.get("response") or {}
    candidate_values = [
        ((response_payload.get("details") or {}).get("usd")),
        (((response_payload.get("details") or {}).get("cost") or {}).get("usd")),
        ((response_payload.get("cost") or {}).get("usd")),
        request_payload.get("usd"),
        ((top_level_response_payload.get("details") or {}).get("usd")),
        (((top_level_response_payload.get("details") or {}).get("cost") or {}).get("usd")),
        ((top_level_response_payload.get("cost") or {}).get("usd")),
        lookup_payload.get("usd"),
    ]

    for value in candidate_values:
        decimal_value = _to_decimal(value)
        if decimal_value is not None:
            return decimal_value
    return None


def _lookup_exact_request_cost(session, candidate_project_ids, request_id):
    """Looks up the exact request cost for one request ID."""
    if not request_id or not candidate_project_ids:
        return None, "Deepgram usage lookup needs a project id and request id."

    last_error = None
    for project_id in candidate_project_ids:
        url = f"https://api.deepgram.com/v1/projects/{project_id}/requests/{request_id}"
        try:
            response = session.get(url, timeout=_MANAGEMENT_TIMEOUT)
        except requests.RequestException as error:
            last_error = _format_lookup_error(error)
            continue

        if response.status_code == 404:
            last_error = f"Deepgram request_id '{request_id}' was not found in the selected project."
            continue
        if response.status_code >= 400:
            return None, _format_lookup_error(requests.HTTPError(response=response))

        try:
            lookup_payload = response.json()
        except ValueError:
            last_error = f"Deepgram usage lookup for request_id '{request_id}' returned invalid JSON."
            continue

        exact_cost = _extract_exact_cost_from_lookup(lookup_payload)
        if exact_cost is not None:
            return exact_cost, None
        last_error = f"Deepgram usage lookup for request_id '{request_id}' did not include USD cost."

    return None, last_error or f"Deepgram usage lookup did not find request_id '{request_id}'."


def _lookup_total_exact_cost(request_ids):
    """Returns the exact total Deepgram cost when every request lookup succeeds."""
    normalized_request_ids = _normalize_request_id_list(request_ids)
    if not normalized_request_ids:
        return None, "No Deepgram request_id is available for cost lookup."

    try:
        api_key = _get_api_key()
    except ValueError as error:
        return None, str(error)

    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json",
        }
    )

    try:
        candidate_project_ids, lookup_error = _resolve_candidate_project_ids(session)
        if not candidate_project_ids:
            return None, lookup_error or "Deepgram usage lookup could not resolve a project id."

        exact_costs = {}
        for request_id in normalized_request_ids:
            exact_cost, lookup_error = _lookup_exact_request_cost(
                session,
                candidate_project_ids,
                request_id,
            )
            if exact_cost is None:
                return None, lookup_error
            exact_costs[request_id] = exact_cost

        return round_cost(float(sum(exact_costs.values(), Decimal("0")))), None
    finally:
        session.close()


def _request_flag(value, *, default=False):
    """Coerces provider-style truthy/falsey parameter values."""
    if value is None:
        return bool(default)
    if isinstance(value, bool):
        return value
    normalized = _clean_text(value).lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return bool(value)


def _estimate_nova_3_cost(model_name, audio_duration_seconds, *, diarize=True):
    """Calculates deterministic Nova-3 prerecorded cost from public pricing."""
    normalized_model = _normalize_model_name(model_name)
    if not normalized_model.startswith("nova-3"):
        return None

    price_per_minute = _NOVA_3_MULTILINGUAL_PRICE_PER_MINUTE
    if normalized_model == "nova-3-medical":
        price_per_minute = _NOVA_3_MONOLINGUAL_PRICE_PER_MINUTE
    if diarize:
        price_per_minute += _NOVA_3_DIARIZATION_PRICE_PER_MINUTE
    return compute_cost_by_duration(
        audio_duration_seconds,
        unit_price=price_per_minute,
        billing_unit="minute",
    )


def _resolve_deepgram_cost_metadata(
    *,
    request_ids,
    model_name,
    audio_duration_seconds,
    diarize=True,
):
    """Resolves the public Deepgram transcription cost metadata contract."""
    exact_cost, lookup_error = _lookup_total_exact_cost(request_ids)
    if exact_cost is not None:
        return {
            "cost_usd": exact_cost,
            "cost_source": "usage_lookup",
            "cost_is_estimated": False,
            "cost_lookup_error": None,
        }

    estimated_cost = _estimate_nova_3_cost(
        model_name,
        audio_duration_seconds,
        diarize=diarize,
    )
    if estimated_cost is not None:
        return {
            "cost_usd": estimated_cost,
            "cost_source": "official_pricing_table",
            "cost_is_estimated": True,
            "cost_lookup_error": lookup_error,
        }

    return {
        "cost_usd": 0.0,
        "cost_source": "unavailable",
        "cost_is_estimated": False,
        "cost_lookup_error": lookup_error or "Deepgram exact usage lookup is required for this model family.",
    }


def _validate_model(model_name):
    """Keep documented Deepgram model aliases as metadata, not an acceptance gate."""

    return None


def _reject_unknown_kwargs(model, kwargs):
    """Return kwargs unchanged so new Deepgram query parameters can pass through."""

    return dict(kwargs or {})


def _normalize_extra_request_params(options):
    """Return official Deepgram Listen parameters not handled by shared defaults."""
    params = {}
    for key, value in dict(options or {}).items():
        params[key] = value
    return params


def _stringify_query_value(value):
    """Serialize booleans into Deepgram query-style lowercase values."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list | tuple | set):
        return [_stringify_query_value(item) for item in value]
    return value
