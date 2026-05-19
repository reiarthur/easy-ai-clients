"""Shared helpers for audio voice-management adapters."""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

import requests

from ..._transcribe.pre_processing import build_request_audio


def require_key(env_var: str) -> str:
    value = str(os.getenv(env_var) or "").strip()
    if not value:
        raise OSError(f"Environment variable '{env_var}' is not set.")
    return value


def request_json(
    method: str,
    url: str,
    *,
    headers: Mapping[str, str] | None = None,
    params: Mapping[str, Any] | None = None,
    payload: Mapping[str, Any] | None = None,
    files: Any = None,
    data: Any = None,
    timeout_seconds: float | None = None,
) -> dict[str, Any]:
    response = requests.request(
        method,
        url,
        headers=dict(headers or {}),
        params=dict(params or {}),
        json=dict(payload or {}) if payload is not None else None,
        files=files,
        data=data,
        timeout=float(timeout_seconds or 120),
    )
    if response.status_code >= 400:
        raise RuntimeError(f"HTTP {response.status_code} from {url}: {response.text[:1000]}")
    if not response.content:
        return {}
    parsed = response.json()
    return parsed if isinstance(parsed, dict) else {"data": parsed}


def normalize(provider: str, operation: str, raw: Mapping[str, Any], **extra: Any) -> dict[str, Any]:
    payload = {"provider": provider, "operation": operation, "data": raw.get("data", raw), "raw_response": dict(raw)}
    payload.update({key: value for key, value in extra.items() if value is not None})
    return payload


def unsupported(provider: str, operation: str) -> dict[str, Any]:
    return {
        "provider": provider,
        "operation": operation,
        "data": None,
        "raw_response": {},
        "warnings": f"{provider} does not support audio.{operation}.",
        "error": {
            "type": "unsupported_operation",
            "provider": provider,
            "operation": operation,
        },
    }


def audio_file_tuple(audio_input: Any):
    request_audio = build_request_audio(audio_input)
    return (
        request_audio["file_name"],
        request_audio["audio_bytes"],
        request_audio["content_type"],
    )


__all__ = ["audio_file_tuple", "normalize", "request_json", "require_key", "unsupported"]
