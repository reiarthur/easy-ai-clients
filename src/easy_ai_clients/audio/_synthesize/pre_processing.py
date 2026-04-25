"""Shared input normalization helpers for speech-synthesis adapters.

Last updated: 2026-04-23
"""

from __future__ import annotations

import base64
import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

from .._transcribe.pre_processing import (
    audio_content_type as _audio_content_type,
)
from .._transcribe.pre_processing import (
    build_data_url as _build_data_url,
)
from .._transcribe.pre_processing import (
    export_segment as _export_segment,
)
from .._transcribe.pre_processing import (
    load_audio as _load_audio,
)

MIN_SPLIT_CHARS = 220
DEFAULT_REFERENCE_EXPORT_FORMAT = "mp3"
DEFAULT_REFERENCE_FILE_STEM = "reference_audio"
WORD_PATTERN = re.compile(r"\w+(?:[-'’]\w+)*(?:[^\w\s]+)*", re.UNICODE)
_URL_SCHEMES = {"http", "https"}
_EXTENSION_TO_FORMAT = {
    ".aac": "aac",
    ".flac": "flac",
    ".m4a": "m4a",
    ".mp3": "mp3",
    ".mp4": "mp4",
    ".ogg": "ogg",
    ".opus": "opus",
    ".pcm": "pcm",
    ".raw": "pcm",
    ".wav": "wav",
    ".webm": "webm",
}


def ensure_env_var(name: str) -> str:
    """Return one required environment variable, raising a clear error when absent."""
    value = str(os.getenv(name) or "").strip()
    if not value:
        raise OSError(f"Environment variable '{name}' is not set.")
    return value


def normalize_text(text: str) -> str:
    """Collapse repeated whitespace while preserving paragraph boundaries."""
    normalized = str(text or "").replace("\r\n", "\n")
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def chunk_text_for_provider(text: str, char_limit: int) -> list[str]:
    """Normalize provider input text and split it into request-sized chunks."""
    clean_text = normalize_text(text)
    if not clean_text:
        raise ValueError("Text is empty after normalization.")
    return split_text_balanced(clean_text, int(char_limit))


def resolve_language_code(language_code: str | None, default: str = "pt") -> str:
    """Reduce one locale-like string to its base language code."""
    value = str(language_code or "").strip().replace("_", "-").lower()
    if not value:
        return str(default or "pt").strip().lower() or "pt"
    base = next((part for part in value.split("-") if part), "")
    return base if len(base) >= 2 else (str(default or "pt").strip().lower() or "pt")


def resolve_locale(language_code: str | None, default: str = "pt-BR") -> str:
    """Return a normalized locale string suitable for provider requests."""
    value = str(language_code or "").strip().replace("_", "-")
    if not value:
        return str(default or "pt-BR").strip() or "pt-BR"

    parts = [part for part in value.split("-") if part]
    if not parts:
        return str(default or "pt-BR").strip() or "pt-BR"
    if len(parts) == 1:
        return parts[0].lower()
    return f"{parts[0].lower()}-{parts[1].upper()}"


def normalize_timestamp_value(value: Any, unit: str = "seconds") -> float:
    """Normalize one timestamp scalar into seconds."""
    numeric = float(value)
    normalized_unit = str(unit or "seconds").strip().lower()
    factors = {
        "s": 1.0,
        "sec": 1.0,
        "second": 1.0,
        "seconds": 1.0,
        "ms": 1e-3,
        "millisecond": 1e-3,
        "milliseconds": 1e-3,
        "us": 1e-6,
        "microsecond": 1e-6,
        "microseconds": 1e-6,
        "ns": 1e-9,
        "nanosecond": 1e-9,
        "nanoseconds": 1e-9,
    }
    if normalized_unit not in factors:
        raise ValueError(f"Unsupported timestamp unit '{unit}'.")
    return numeric * factors[normalized_unit]


def normalize_word_timestamps(
    words: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...],
    *,
    unit: str = "seconds",
    word_key: str = "word",
    start_key: str = "start",
    end_key: str = "end",
) -> list[dict[str, Any]]:
    """Normalize one list of per-word timing mappings into the internal format."""
    normalized_words: list[dict[str, Any]] = []
    for item in words or []:
        if not isinstance(item, Mapping):
            raise TypeError("Each word timestamp item must be a mapping.")
        word = str(item.get(word_key, "")).strip()
        if not word:
            continue
        normalized_words.append(
            {
                "word": word,
                "start": normalize_timestamp_value(item.get(start_key, 0.0), unit=unit),
                "end": normalize_timestamp_value(item.get(end_key, 0.0), unit=unit),
            }
        )
    return normalized_words


def audio_bytes_to_base64(audio_bytes: bytes | bytearray) -> str:
    """Encode raw audio bytes into a plain base64 string."""
    data = bytes(audio_bytes or b"")
    if not data:
        raise ValueError("audio_bytes is empty.")
    return base64.b64encode(data).decode("ascii")


def decode_base64_bytes(encoded: str | bytes | bytearray) -> bytes:
    """Decode one plain base64 string or data URL into raw bytes."""
    value = encoded.decode("utf-8", errors="ignore") if isinstance(encoded, (bytes, bytearray)) else str(encoded or "")
    value = value.strip()
    if value.startswith("data:") and "," in value:
        value = value.split(",", 1)[1]
    value = re.sub(r"\s+", "", value)
    if not value:
        raise ValueError("Base64 payload is empty.")

    padding = (-len(value)) % 4
    if padding:
        value += "=" * padding
    try:
        decoded = base64.b64decode(value, validate=True)
    except Exception:
        decoded = base64.urlsafe_b64decode(value)
    if not decoded:
        raise ValueError("Base64 payload decoded to empty bytes.")
    return decoded


def audio_content_type(audio_format: str) -> str:
    """Return the most reasonable MIME type for one audio export format."""
    return _audio_content_type(audio_format)


def build_data_url(media_bytes: bytes, content_type: str) -> str:
    """Build one data URL from in-memory bytes."""
    return _build_data_url(media_bytes, content_type)


def export_audio_segment(segment: Any, export_format: str = DEFAULT_REFERENCE_EXPORT_FORMAT) -> tuple[bytes, str]:
    """Export one AudioSegment into bytes and its content type."""
    return _export_segment(segment, export_format=export_format)


def load_audio_input(audio_input: Any) -> Any:
    """Load arbitrary audio input using the shared transcription pre-processing layer."""
    return _load_audio(audio_input)


def compute_operational_char_limit(model_char_limit: int) -> int:
    """Derive a safer per-request size to keep latency and timeouts under control."""
    if model_char_limit <= 6000:
        tier_ceiling = 2200
    elif model_char_limit <= 15000:
        tier_ceiling = 3200
    else:
        tier_ceiling = 5000

    operational = max(
        650,
        min(
            int(model_char_limit * 0.55),
            int(model_char_limit) - 800,
            tier_ceiling,
        ),
    )
    return min(int(model_char_limit), max(MIN_SPLIT_CHARS, operational))


def split_text_balanced(text: str, limit: int) -> list[str]:
    """Split text into chunks at the softest natural boundary that honors the limit."""
    base_text = str(text or "").strip()
    if len(base_text) <= limit:
        return [base_text] if base_text else []

    target = max(MIN_SPLIT_CHARS, min(int(limit * 0.9), int(limit) - 20))
    units = [base_text]
    strategies = (
        lambda value: [part.strip() for part in re.split(r"\n{2,}", value) if part and part.strip()],
        _split_sentences,
        _split_weak_punctuation,
        lambda value: _split_by_words(value, limit),
    )

    for strategy in strategies:
        next_units: list[str] = []
        split_happened = False
        for unit in units:
            if len(unit) <= limit:
                next_units.append(unit)
                continue
            parts = strategy(unit)
            if len(parts) <= 1:
                next_units.append(unit)
                continue
            split_happened = True
            next_units.extend(parts)
        units = [unit for unit in next_units if unit and unit.strip()]
        if split_happened and all(len(unit) <= limit for unit in units):
            break

    final_units: list[str] = []
    for unit in units:
        if len(unit) <= limit:
            final_units.append(unit.strip())
        else:
            final_units.extend(_hard_split(unit, limit))

    grouped = _group_units(final_units, limit=limit, target=target) or _hard_split(base_text, limit)
    result: list[str] = []
    for chunk in grouped:
        result.extend([chunk] if len(chunk) <= limit else _hard_split(chunk, limit))
    return [chunk for chunk in result if chunk]


def split_near_middle(text: str, min_chars: int = MIN_SPLIT_CHARS) -> tuple[str, str] | None:
    """Split one chunk near its midpoint at the softest natural boundary."""
    base_text = str(text or "").strip()
    if len(base_text) < int(min_chars) * 2:
        return None

    midpoint = len(base_text) // 2
    for pattern in (r"[\.\!\?\;…]\s+", r"[,\:]\s+", r"\s+"):
        boundaries = [
            match.end()
            for match in re.finditer(pattern, base_text)
            if min_chars <= match.end() <= len(base_text) - min_chars
        ]
        if boundaries:
            split_index = min(boundaries, key=lambda value: abs(value - midpoint))
            break
    else:
        split_index = max(min_chars, min(len(base_text) - min_chars, midpoint))

    left_text = base_text[:split_index].strip()
    right_text = base_text[split_index:].strip()
    return (left_text, right_text) if left_text and right_text else None


def tokenize_words(text: str) -> list[dict[str, Any]]:
    """Tokenize text into word-like units while preserving the display token."""
    tokens: list[dict[str, Any]] = []
    for match in WORD_PATTERN.finditer(str(text or "")):
        display = match.group()
        normalized = normalize_comparison_token(display)
        if not display.strip():
            continue
        tokens.append(
            {
                "word": display,
                "normalized": normalized,
                "start_index": match.start(),
                "end_index": match.end(),
            }
        )
    return tokens


def normalize_comparison_token(token: str) -> str:
    """Normalize one token for fuzzy timing projection between TTS and STT text."""
    value = str(token or "").strip().lower().replace("’", "'")
    value = re.sub(r"^[^\w]+|[^\w]+$", "", value, flags=re.UNICODE)
    value = re.sub(r"[_\W]+", "", value, flags=re.UNICODE)
    return value


def is_probable_url(value: str | None) -> bool:
    """Return whether a string looks like one downloadable URL."""
    candidate = str(value or "").strip()
    if not candidate:
        return False
    parsed = urlparse(candidate)
    return parsed.scheme.lower() in _URL_SCHEMES and bool(parsed.netloc)


def infer_audio_format_from_name(name: str | None, default: str = DEFAULT_REFERENCE_EXPORT_FORMAT) -> str:
    """Infer one audio format from a file path or URL."""
    value = str(name or "").strip()
    if not value:
        return str(default or DEFAULT_REFERENCE_EXPORT_FORMAT).strip().lower()
    path = urlparse(value).path if is_probable_url(value) else value
    suffix = Path(path).suffix.lower()
    return _EXTENSION_TO_FORMAT.get(suffix, str(default or DEFAULT_REFERENCE_EXPORT_FORMAT).strip().lower())


def resolve_reference_audio(
    *,
    voice_id: str | None = None,
    reference_audio: Any = None,
    reference_audio_path: str | None = None,
    reference_audio_base64: str | None = None,
    reference_audio_url: str | None = None,
    export_format: str = DEFAULT_REFERENCE_EXPORT_FORMAT,
    timeout_seconds: float = 60.0,
    file_stem: str = DEFAULT_REFERENCE_FILE_STEM,
) -> dict[str, Any] | None:
    """Resolve reference audio from local, in-memory, base64, or URL sources."""
    if voice_id:
        return None

    if reference_audio_base64:
        audio_bytes = decode_base64_bytes(reference_audio_base64)
        audio_format = infer_audio_format_from_name(file_stem, default=export_format)
        return _build_reference_audio_bundle(
            audio=load_audio_input(audio_bytes),
            audio_bytes=audio_bytes,
            audio_format=audio_format,
            file_stem=file_stem,
        )

    if reference_audio_url:
        response = requests.get(reference_audio_url, timeout=(10.0, float(timeout_seconds)))
        response.raise_for_status()
        downloaded_bytes = bytes(response.content or b"")
        if not downloaded_bytes:
            raise ValueError("reference_audio_url returned empty content.")
        audio_format = infer_audio_format_from_name(reference_audio_url, default=export_format)
        audio = load_audio_input(downloaded_bytes)
        exported_bytes, _ = export_audio_segment(audio, export_format=audio_format)
        return _build_reference_audio_bundle(
            audio=audio,
            audio_bytes=exported_bytes,
            audio_format=audio_format,
            file_stem=file_stem,
        )

    source = reference_audio if reference_audio is not None else reference_audio_path
    if source is None:
        return None

    audio = load_audio_input(source)
    exported_bytes, _ = export_audio_segment(audio, export_format=export_format)
    return _build_reference_audio_bundle(
        audio=audio,
        audio_bytes=exported_bytes,
        audio_format=export_format,
        file_stem=file_stem,
    )


def _build_reference_audio_bundle(
    *,
    audio: Any,
    audio_bytes: bytes,
    audio_format: str,
    file_stem: str,
) -> dict[str, Any]:
    """Build one normalized reference-audio bundle for adapters."""
    content_type = audio_content_type(audio_format)
    file_name = f"{file_stem}.{audio_format}"
    payload = bytes(audio_bytes or b"")
    if not payload:
        raise ValueError("Reference audio payload is empty.")
    return {
        "audio": audio,
        "audio_bytes": payload,
        "audio_base64": audio_bytes_to_base64(payload),
        "audio_format": audio_format,
        "content_type": content_type,
        "data_url": build_data_url(payload, content_type),
        "file_name": file_name,
    }


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[\.\!\?\;…])\s+", str(text or "").strip())
    return [part.strip() for part in parts if part and part.strip()]


def _split_weak_punctuation(text: str) -> list[str]:
    parts = re.split(r"(?<=[,\:])\s+", str(text or "").strip())
    return [part.strip() for part in parts if part and part.strip()]


def _hard_split(text: str, limit: int) -> list[str]:
    base_text = str(text or "").strip()
    if not base_text:
        return []
    if len(base_text) <= limit:
        return [base_text]
    return [
        base_text[index : index + limit].strip()
        for index in range(0, len(base_text), limit)
        if base_text[index : index + limit].strip()
    ]


def _split_by_words(text: str, limit: int) -> list[str]:
    base_text = str(text or "").strip()
    if len(base_text) <= limit:
        return [base_text] if base_text else []

    words = base_text.split()
    if not words:
        return _hard_split(base_text, limit)

    chunks: list[str] = []
    current_chunk = ""
    for word in words:
        if len(word) > limit:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            chunks.extend(_hard_split(word, limit))
            continue

        candidate = word if not current_chunk else f"{current_chunk} {word}"
        if len(candidate) <= limit:
            current_chunk = candidate
        else:
            chunks.append(current_chunk)
            current_chunk = word

    if current_chunk:
        chunks.append(current_chunk)
    return chunks


def _group_units(units: list[str], limit: int, target: int) -> list[str]:
    """Pack split units into similarly-sized chunks without exceeding the limit."""
    chunks: list[str] = []
    current_chunk = ""
    for unit in units:
        text_unit = str(unit or "").strip()
        if not text_unit:
            continue

        candidate = text_unit if not current_chunk else f"{current_chunk} {text_unit}"
        if len(candidate) <= limit and len(candidate) <= max(target, len(current_chunk)):
            current_chunk = candidate
            continue

        if current_chunk:
            chunks.append(current_chunk.strip())
        current_chunk = text_unit

    if current_chunk:
        chunks.append(current_chunk.strip())
    return [chunk for chunk in chunks if chunk]


__all__ = [
    "DEFAULT_REFERENCE_EXPORT_FORMAT",
    "DEFAULT_REFERENCE_FILE_STEM",
    "MIN_SPLIT_CHARS",
    "WORD_PATTERN",
    "audio_bytes_to_base64",
    "audio_content_type",
    "build_data_url",
    "chunk_text_for_provider",
    "compute_operational_char_limit",
    "decode_base64_bytes",
    "ensure_env_var",
    "export_audio_segment",
    "infer_audio_format_from_name",
    "is_probable_url",
    "load_audio_input",
    "normalize_comparison_token",
    "normalize_text",
    "normalize_timestamp_value",
    "normalize_word_timestamps",
    "resolve_language_code",
    "resolve_locale",
    "resolve_reference_audio",
    "split_near_middle",
    "split_text_balanced",
    "tokenize_words",
]
