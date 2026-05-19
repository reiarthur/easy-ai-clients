"""DeepInfra voice catalog adapter."""

from __future__ import annotations

from typing import Any

from ._shared import normalize, request_json, require_key, unsupported

BASE_URL = "https://api.deepinfra.com/v1/openai/audio/voices"


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {require_key('DEEPINFRA_API_KEY')}"}


def list_voices(*, timeout_seconds: float | None = None, **kwargs: Any) -> dict[str, Any]:
    raw = request_json("GET", BASE_URL, headers=_headers(), params=kwargs, timeout_seconds=timeout_seconds)
    return normalize("deepinfra", "list_voices", raw)


def get_voice(voice_id: str, *, timeout_seconds: float | None = None, **kwargs: Any) -> dict[str, Any]:
    params = dict(kwargs)
    params["voice_id"] = voice_id
    raw = request_json("GET", BASE_URL, headers=_headers(), params=params, timeout_seconds=timeout_seconds)
    return normalize("deepinfra", "get_voice", raw, voice_id=voice_id)


def design_voice(prompt: str, **kwargs: Any) -> dict[str, Any]:
    return unsupported("deepinfra", "design_voice")


def clone_voice(*, audio_input: Any = None, voice_name: str | None = None, **kwargs: Any) -> dict[str, Any]:
    return unsupported("deepinfra", "clone_voice")


__all__ = ["BASE_URL", "clone_voice", "design_voice", "get_voice", "list_voices"]
