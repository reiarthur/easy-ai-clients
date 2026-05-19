"""HeyGen v3 voice-management adapter."""

from __future__ import annotations

from typing import Any

from .... import _heygen


def list_voices(
    *,
    type: str = "public",
    engine: str | None = None,
    language: str | None = None,
    gender: str | None = None,
    limit: int | None = 20,
    token: str | None = None,
    timeout_seconds: float | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    params = {
        "type": type,
        "engine": engine,
        "language": language,
        "gender": gender,
        "limit": limit,
        "token": token,
        **kwargs,
    }
    raw = _heygen.request_json("GET", "/v3/voices", params=params, timeout_seconds=timeout_seconds)
    return {"provider": "heygen", "data": _heygen.data(raw), "raw_response": raw}


def get_voice(voice_id: str, *, timeout_seconds: float | None = None, **kwargs: Any) -> dict[str, Any]:
    if not voice_id:
        raise ValueError("voice_id is required.")
    raw = _heygen.request_json(
        "GET",
        f"/v3/voices/{_heygen.quote_path(voice_id)}",
        params=kwargs,
        timeout_seconds=timeout_seconds,
    )
    return {"provider": "heygen", "voice_id": voice_id, "data": _heygen.data(raw), "raw_response": raw}


def design_voice(prompt: str, *, timeout_seconds: float | None = None, **kwargs: Any) -> dict[str, Any]:
    prompt = str(prompt or "").strip()
    if not prompt:
        raise ValueError("prompt is required.")
    payload = {"prompt": prompt, **kwargs}
    raw = _heygen.request_json(
        "POST",
        "/v3/voices",
        payload=payload,
        timeout_seconds=timeout_seconds,
    )
    return {"provider": "heygen", "data": _heygen.data(raw), "raw_response": raw}


def clone_voice(
    *,
    audio_input: Any = None,
    voice_name: str | None = None,
    audio: Any = None,
    timeout_seconds: float | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    name = str(voice_name or kwargs.pop("voice_name", "") or "").strip()
    if not name:
        raise ValueError("voice_name is required.")
    source = audio if audio is not None else audio_input
    payload = {
        "voice_name": name,
        "audio": _heygen.asset_input(source, field_name="audio", allow_base64=True),
        **kwargs,
    }
    if payload["audio"] is None:
        raise ValueError("audio_input is required.")
    raw = _heygen.request_json(
        "POST",
        "/v3/voices/clone",
        payload=payload,
        timeout_seconds=timeout_seconds,
    )
    return {"provider": "heygen", "data": _heygen.data(raw), "raw_response": raw}

