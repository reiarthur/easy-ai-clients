"""ElevenLabs voice-management adapter."""

from __future__ import annotations

from typing import Any

from ._shared import audio_file_tuple, normalize, request_json, require_key

BASE_URL = "https://api.elevenlabs.io/v1"


def _headers() -> dict[str, str]:
    return {"xi-api-key": require_key("ELEVENLABS_API_KEY")}


def list_voices(*, timeout_seconds: float | None = None, **kwargs: Any) -> dict[str, Any]:
    raw = request_json("GET", f"{BASE_URL}/voices", headers=_headers(), params=kwargs, timeout_seconds=timeout_seconds)
    return normalize("elevenlabs", "list_voices", raw)


def get_voice(voice_id: str, *, timeout_seconds: float | None = None, **kwargs: Any) -> dict[str, Any]:
    raw = request_json(
        "GET",
        f"{BASE_URL}/voices/{voice_id}",
        headers=_headers(),
        params=kwargs,
        timeout_seconds=timeout_seconds,
    )
    return normalize("elevenlabs", "get_voice", raw, voice_id=voice_id)


def design_voice(prompt: str, *, timeout_seconds: float | None = None, **kwargs: Any) -> dict[str, Any]:
    payload = {"voice_description": str(prompt or "").strip()}
    payload.update(kwargs)
    raw = request_json(
        "POST",
        f"{BASE_URL}/text-to-voice/design",
        headers={**_headers(), "Content-Type": "application/json"},
        payload=payload,
        timeout_seconds=timeout_seconds,
    )
    return normalize("elevenlabs", "design_voice", raw)


def clone_voice(
    *,
    audio_input: Any = None,
    voice_name: str | None = None,
    timeout_seconds: float | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    if audio_input is None:
        raise ValueError("audio_input is required.")
    data = {"name": voice_name or kwargs.pop("name", "cloned voice")}
    data.update({key: value for key, value in kwargs.items() if value is not None})
    raw = request_json(
        "POST",
        f"{BASE_URL}/voices/add",
        headers=_headers(),
        data=data,
        files={"files": audio_file_tuple(audio_input)},
        timeout_seconds=timeout_seconds,
    )
    return normalize("elevenlabs", "clone_voice", raw)


__all__ = ["BASE_URL", "clone_voice", "design_voice", "get_voice", "list_voices"]
