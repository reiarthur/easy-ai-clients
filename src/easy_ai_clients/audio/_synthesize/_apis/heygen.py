"""HeyGen v3 speech synthesis adapter."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any

from .... import _heygen
from ..post_processing import _finalize_synthesis_output, build_chunk_record
from ..pre_processing import infer_audio_format_from_name

DEFAULT_MODEL = "starfish"
DEFAULT_VOICE = None


def generate(
    text: str,
    model: str = DEFAULT_MODEL,
    voice: str | None = DEFAULT_VOICE,
    language_code: str = "en",
    **kwargs: Any,
) -> dict[str, Any]:
    """Generate speech through HeyGen Starfish voices."""

    input_text = str(text or "").strip()
    if not input_text:
        raise ValueError("text is required.")

    timeout_seconds = kwargs.pop("timeout_seconds", None)
    voice_id = voice or kwargs.pop("voice_id", None) or _default_starfish_voice(timeout_seconds)
    payload = {
        "text": input_text,
        "voice_id": voice_id,
        "input_type": kwargs.pop("input_type", "text"),
        "language": kwargs.pop("language", language_code or None),
        "locale": kwargs.pop("locale", None),
        "speed": kwargs.pop("speed", 1),
        **kwargs,
    }
    raw = _heygen.request_json(
        "POST",
        "/v3/voices/speech",
        payload=payload,
        timeout_seconds=timeout_seconds,
    )
    item = _heygen.data(raw)
    if not isinstance(item, dict) or not item.get("audio_url"):
        raise RuntimeError("HeyGen speech generation did not return audio_url.")

    audio_url = str(item["audio_url"])
    audio_bytes = _heygen.download_url(audio_url, timeout_seconds=timeout_seconds)
    chunk = build_chunk_record(
        text=input_text,
        audio_bytes=audio_bytes,
        audio_format=_audio_format_from_url(audio_url),
        observed_words=item.get("word_timestamps") or [],
    )
    result = _finalize_synthesis_output([chunk], cost_usd=0.0)
    result.update(
        {
            "request_id": item.get("request_id"),
            "cost_source": "unavailable",
            "cost_is_estimated": False,
            "provider_metadata": {"provider": "heygen", "model": model, "voice_id": voice_id},
            "raw_response": raw,
        }
    )
    return result


def _default_starfish_voice(timeout_seconds: float | None) -> str:
    raw = _heygen.request_json(
        "GET",
        "/v3/voices",
        params={"type": "public", "engine": "starfish", "limit": 1},
        timeout_seconds=timeout_seconds,
    )
    voices = _heygen.data(raw)
    if isinstance(voices, dict):
        voices = voices.get("data")
    if isinstance(voices, list) and voices and isinstance(voices[0], dict) and voices[0].get("voice_id"):
        return str(voices[0]["voice_id"])
    raise ValueError("voice or voice_id is required; HeyGen returned no default starfish voice.")


def _audio_format_from_url(url: str) -> str:
    suffix = PurePosixPath(str(url).split("?", 1)[0]).suffix.lower().lstrip(".")
    return infer_audio_format_from_name(suffix or "mp3") or "mp3"


__all__ = ["DEFAULT_MODEL", "DEFAULT_VOICE", "generate"]
