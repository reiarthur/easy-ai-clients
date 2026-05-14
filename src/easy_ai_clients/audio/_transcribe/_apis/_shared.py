"""Shared helpers for transcription provider adapters.

Centralises HTTP retries, JSON decoding, kwargs validation, billing helpers and
normalised word/utterance record builders consumed by the transcription
provider modules.

Last updated: 2026-04-25
"""

from __future__ import annotations

import math
import os
import time
from collections.abc import Iterable, Mapping
from typing import Any

import requests

RETRY_STATUS_CODES = {408, 409, 425, 429, 500, 502, 503, 504}


def round_cost(value: Any) -> float:
    """Round one USD amount using the project precision."""
    try:
        return round(max(0.0, float(value)), 6)
    except Exception:
        return 0.0


def get_required_api_key(env_var: str) -> str:
    """Return one mandatory environment variable, raising on absence."""
    value = str(os.getenv(env_var) or "").strip()
    if not value:
        raise OSError(f"Environment variable '{env_var}' is not set.")
    return value


def reject_unknown_kwargs(
    provider: str,
    model: str,
    kwargs: Mapping[str, Any],
    allowed_names: Iterable[str],
) -> dict[str, Any]:
    """Return kwargs unchanged; documented names are no longer an acceptance gate."""

    return dict(kwargs or {})


def validate_choice(
    value: Any,
    allowed_values: Iterable[Any],
    *,
    parameter_name: str,
    provider: str,
    model: str,
) -> Any:
    """Return a provider-native choice without applying a local whitelist."""

    return value


def validate_number_range(
    value: Any,
    *,
    parameter_name: str,
    provider: str,
    model: str,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    """Coerce a numeric parameter when possible without enforcing provider ranges."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def build_http_error(response: requests.Response) -> requests.HTTPError:
    """Build an HTTPError containing the first part of the response body."""
    body = str(response.text or "").strip()
    message = f"HTTP {response.status_code} during API request."
    if body:
        message = f"{message} body={body[:1000]}"
    return requests.HTTPError(message, response=response, request=response.request)


def request_with_retries(
    method: str,
    url: str,
    *,
    headers: Mapping[str, str] | None = None,
    params: Mapping[str, Any] | None = None,
    json_body: Mapping[str, Any] | None = None,
    data: Any = None,
    files: Any = None,
    timeout: tuple[float, float] = (10.0, 180.0),
    stream: bool = False,
    max_attempts: int = 2,
) -> requests.Response:
    """Execute one HTTP request with retry on transient failures."""
    for attempt in range(1, int(max_attempts) + 1):
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=dict(headers or {}),
                params=dict(params or {}),
                json=dict(json_body or {}) if json_body is not None else None,
                data=data,
                files=files,
                timeout=timeout,
                stream=stream,
            )
        except (requests.Timeout, requests.ConnectionError):
            if attempt >= max_attempts:
                raise
            time.sleep(1.2 * (2 ** (attempt - 1)))
            continue

        if response.status_code in RETRY_STATUS_CODES and attempt < max_attempts:
            response.close()
            time.sleep(1.2 * (2 ** (attempt - 1)))
            continue

        if response.status_code >= 400:
            raise build_http_error(response)
        return response

    raise RuntimeError("HTTP request stopped unexpectedly before a final response.")


def response_json(response: requests.Response) -> dict[str, Any]:
    """Decode one JSON response body into a dictionary."""
    if not response.content:
        raise ValueError("API response body is empty.")
    try:
        payload = response.json()
    except ValueError as error:
        raise ValueError("API response did not contain valid JSON.") from error
    if not isinstance(payload, Mapping):
        raise ValueError("API JSON response must be a mapping.")
    return dict(payload)


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Coerce value to float and return default on failure."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clean_text(value: Any) -> str:
    """Collapse whitespace inside a textual fragment."""
    return " ".join(str(value or "").strip().split())


def compute_cost_by_duration(
    duration_seconds: Any,
    *,
    unit_price: float,
    billing_unit: str = "minute",
    minimum_seconds: float = 0.0,
    multiplier: float = 1.0,
    round_seconds: bool = False,
) -> float:
    """Compute one transcription cost billed proportionally by audio time.

    ### Parameters:
    - duration_seconds (Any): Observed or reported audio duration in seconds.
    - unit_price (float): USD price per `billing_unit`.
    - billing_unit (str): Either `'minute'` or `'hour'`.
    - minimum_seconds (float): Minimum chargeable seconds; provider may bill
      every job for at least this duration.
    - multiplier (float): Optional multiplier applied to the base cost (used by
      providers that charge add-ons such as entity detection).
    - round_seconds (bool): When `True`, round duration up to the next whole
      second before applying the price.

    ### Returns:
    - float: Cost in USD rounded with the project precision.
    """

    seconds = max(_safe_float(duration_seconds, 0.0), float(minimum_seconds or 0.0))
    if seconds <= 0.0 or unit_price in (None, 0):
        return 0.0
    if round_seconds:
        seconds = math.ceil(seconds)
    unit = (billing_unit or "minute").strip().lower()
    if unit.startswith("hour"):
        units = seconds / 3600.0
    else:
        units = seconds / 60.0
    return round_cost(units * float(unit_price) * float(multiplier or 1.0))


def build_word_record(
    text: Any,
    start: Any,
    end: Any,
    *,
    speaker: Any = None,
) -> dict[str, Any] | None:
    """Build the normalized word record used by transcription post-processing."""
    cleaned = _clean_text(text)
    if not cleaned:
        return None
    start_seconds = _safe_float(start, 0.0)
    end_seconds = _safe_float(end, start_seconds)
    if end_seconds < start_seconds:
        end_seconds = start_seconds
    record: dict[str, Any] = {
        "text": cleaned,
        "start": round(start_seconds, 6),
        "end": round(end_seconds, 6),
    }
    if speaker is not None:
        record["speaker"] = speaker
    return record


def build_utterance_record(
    start: Any,
    end: Any,
    *,
    text: Any = "",
    speaker: Any = 0,
    words: Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any] | None:
    """Build a normalized utterance/segment payload."""
    word_list = [dict(word) for word in (words or []) if isinstance(word, Mapping)]
    cleaned_text = _clean_text(text) or _clean_text(" ".join(str(item.get("text") or "") for item in word_list))
    if not cleaned_text and not word_list:
        return None
    start_seconds = _safe_float(start, 0.0)
    end_seconds = _safe_float(end, start_seconds)
    if word_list:
        first = _safe_float(word_list[0].get("start"), start_seconds)
        last = _safe_float(word_list[-1].get("end"), end_seconds)
        start_seconds = min(start_seconds, first)
        end_seconds = max(end_seconds, last)
    if end_seconds < start_seconds:
        end_seconds = start_seconds
    return {
        "start": round(start_seconds, 6),
        "end": round(end_seconds, 6),
        "text": cleaned_text,
        "speaker": speaker if speaker is not None else 0,
        "words": word_list,
    }


def _words_in_window(
    words: Iterable[Mapping[str, Any]],
    *,
    start_seconds: float,
    end_seconds: float,
) -> list[dict[str, Any]]:
    """Return word records that overlap with the given utterance window."""
    selected: list[dict[str, Any]] = []
    for word in words or []:
        if not isinstance(word, Mapping):
            continue
        word_start = _safe_float(word.get("start"), 0.0)
        word_end = _safe_float(word.get("end"), word_start)
        if word_end < start_seconds or word_start > end_seconds:
            continue
        selected.append(dict(word))
    return selected


def build_utterances_from_segments(
    segments: Iterable[Mapping[str, Any]] | None,
    words: Iterable[Mapping[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Build utterance records from generic provider segment lists."""
    word_list = [dict(item) for item in (words or []) if isinstance(item, Mapping)]
    utterances: list[dict[str, Any]] = []
    for segment in segments or []:
        if not isinstance(segment, Mapping):
            continue
        start_seconds = _safe_float(segment.get("start"), 0.0)
        end_seconds = _safe_float(segment.get("end"), start_seconds)
        speaker = segment.get("speaker")
        if speaker is None:
            speaker = segment.get("speaker_id")
        if speaker is None:
            speaker = 0
        segment_words = _words_in_window(word_list, start_seconds=start_seconds, end_seconds=end_seconds)
        text_value = segment.get("text") or segment.get("transcript")
        record = build_utterance_record(
            start_seconds,
            end_seconds,
            text=text_value,
            speaker=speaker,
            words=segment_words,
        )
        if record:
            utterances.append(record)
    return utterances


def build_utterances_from_speaker_segments(
    segments: Iterable[Mapping[str, Any]] | None,
    words: Iterable[Mapping[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Build utterance records from diarization speaker segments."""
    word_list = [dict(item) for item in (words or []) if isinstance(item, Mapping)]
    utterances: list[dict[str, Any]] = []
    for segment in segments or []:
        if not isinstance(segment, Mapping):
            continue
        start_seconds = _safe_float(segment.get("start"), 0.0)
        end_seconds = _safe_float(segment.get("end"), start_seconds)
        speaker = segment.get("speaker")
        if speaker is None:
            speaker = segment.get("speaker_id")
        if speaker is None:
            speaker = 0
        segment_words = _words_in_window(word_list, start_seconds=start_seconds, end_seconds=end_seconds)
        text_value = segment.get("text") or segment.get("transcript") or " ".join(
            str(word.get("text") or "") for word in segment_words
        )
        record = build_utterance_record(
            start_seconds,
            end_seconds,
            text=text_value,
            speaker=speaker,
            words=segment_words,
        )
        if record:
            utterances.append(record)
    return utterances


__all__ = [
    "RETRY_STATUS_CODES",
    "build_http_error",
    "build_utterance_record",
    "build_utterances_from_segments",
    "build_utterances_from_speaker_segments",
    "build_word_record",
    "compute_cost_by_duration",
    "get_required_api_key",
    "reject_unknown_kwargs",
    "request_with_retries",
    "response_json",
    "round_cost",
    "validate_choice",
    "validate_number_range",
]
