"""Shared HTTP, billing, streaming, and catalog helpers for TTS adapters.

Last updated: 2026-04-23
"""

from __future__ import annotations

import json
import time
import wave
from collections.abc import Iterable, Mapping
from io import BytesIO
from typing import Any

import requests

from ..pre_processing import decode_base64_bytes

RETRY_STATUS_CODES = {408, 409, 425, 429, 500, 502, 503, 504}


def round_cost(value: Any) -> float:
    """Round one USD amount using the project precision."""
    try:
        return round(max(0.0, float(value)), 6)
    except Exception:
        return 0.0


def compute_cost_by_characters(char_count: int, usd_per_million: float) -> float:
    """Compute one TTS cost billed by input characters."""
    return round_cost((max(0, int(char_count)) / 1_000_000.0) * float(usd_per_million))


def compute_cost_by_minutes(duration_seconds: float, usd_per_minute: float) -> float:
    """Compute one cost billed proportionally by audio minutes."""
    return round_cost((max(0.0, float(duration_seconds)) / 60.0) * float(usd_per_minute))


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


def normalize_language_code(language_code: Any, default: str = "en") -> str:
    """Return a non-empty public language code."""
    normalized = str(language_code or "").strip()
    return normalized or default


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
    """Decode one JSON response into a dictionary."""
    if not response.content:
        raise ValueError("API response body is empty.")
    try:
        payload = response.json()
    except ValueError as error:
        raise ValueError("API response did not contain valid JSON.") from error
    if not isinstance(payload, Mapping):
        raise ValueError("API JSON response must be a mapping.")
    return dict(payload)


def collect_sse_events(response: requests.Response) -> list[dict[str, Any]]:
    """Collect JSON events from one server-sent-events response."""
    events: list[dict[str, Any]] = []
    data_lines: list[str] = []
    event_name = ""

    for raw_line in response.iter_lines(decode_unicode=True):
        line = str(raw_line or "")
        if not line:
            if not data_lines:
                event_name = ""
                continue
            payload = "\n".join(data_lines).strip()
            data_lines = []
            if payload == "[DONE]":
                break
            try:
                event_payload = json.loads(payload)
            except Exception:
                event_payload = {"type": event_name or "message", "data": payload}
            if event_name and "type" not in event_payload:
                event_payload["type"] = event_name
            events.append(event_payload)
            event_name = ""
            continue

        if line.startswith("event:"):
            event_name = line.split(":", 1)[1].strip()
            continue
        if line.startswith("data:"):
            data_lines.append(line.split(":", 1)[1].lstrip())
    return events


def pcm_to_wav_bytes(
    pcm_bytes: bytes,
    *,
    sample_rate: int,
    sample_width: int = 2,
    channels: int = 1,
) -> bytes:
    """Wrap raw PCM bytes into a WAV container for downstream decoding/alignment."""
    payload = bytes(pcm_bytes or b"")
    if not payload:
        raise ValueError("PCM payload is empty.")

    wav_buffer = BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(int(channels))
        wav_file.setsampwidth(int(sample_width))
        wav_file.setframerate(int(sample_rate))
        wav_file.writeframes(payload)
    return wav_buffer.getvalue()


def synthesize_json_base64_tts(
    *,
    url: str,
    headers: Mapping[str, str],
    payload: Mapping[str, Any],
    audio_field: str = "audio_data",
    timeout_seconds: float = 180.0,
) -> tuple[bytes, dict[str, Any], Mapping[str, Any]]:
    """Call one JSON TTS endpoint that returns audio as base64 inside the payload."""
    response = request_with_retries(
        "POST",
        url,
        headers=headers,
        json_body=dict(payload),
        timeout=(10.0, float(timeout_seconds)),
    )
    payload_json = response_json(response)
    encoded = str(payload_json.get(audio_field, "")).strip()
    if not encoded:
        raise ValueError("TTS response did not include audio base64.")
    return decode_base64_bytes(encoded), payload_json, response.headers


def discover_deepinfra_tts_models(api_key: str) -> list[dict[str, Any]]:
    """Return the current DeepInfra text-to-speech catalog entries."""
    response = request_with_retries(
        "GET",
        "https://api.deepinfra.com/models/list",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=(10.0, 60.0),
    )
    if not response.content:
        raise ValueError("DeepInfra catalog response was empty.")
    try:
        payload = response.json()
    except ValueError as error:
        raise ValueError("DeepInfra catalog response did not contain valid JSON.") from error
    if not isinstance(payload, list):
        raise ValueError("DeepInfra catalog response must be a list.")
    return [dict(item) for item in payload if isinstance(item, Mapping) and str(item.get("type") or "").lower() == "text-to-speech"]


__all__ = [
    "RETRY_STATUS_CODES",
    "build_http_error",
    "collect_sse_events",
    "compute_cost_by_characters",
    "compute_cost_by_minutes",
    "discover_deepinfra_tts_models",
    "normalize_language_code",
    "pcm_to_wav_bytes",
    "request_with_retries",
    "reject_unknown_kwargs",
    "response_json",
    "round_cost",
    "synthesize_json_base64_tts",
    "validate_choice",
    "validate_number_range",
]
