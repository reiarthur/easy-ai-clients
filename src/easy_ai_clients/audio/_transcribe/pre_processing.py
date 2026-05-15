"""Provides audio loading and chunking utilities for transcription pre-processing.

Last updated: 2026-04-21
"""

from __future__ import annotations

import base64
import io
import math
import os
import shutil
import subprocess
import warnings
from dataclasses import dataclass
from urllib.parse import urlparse

import requests

with warnings.catch_warnings():
    warnings.filterwarnings(
        "ignore",
        message="Couldn't find ffmpeg or avconv - defaulting to ffmpeg, but may not work",
        category=RuntimeWarning,
    )
    warnings.filterwarnings(
        "ignore",
        message="Couldn't find ffprobe or avprobe - defaulting to ffprobe, but may not work",
        category=RuntimeWarning,
    )
    try:
        from pydub import AudioSegment
    except Exception:
        AudioSegment = None

try:
    import imageio_ffmpeg
except Exception:
    imageio_ffmpeg = None


_DEFAULT_TARGET_CHUNK_SECONDS = 60.0
_DEFAULT_MAX_CHUNK_SECONDS = 75.0
_DEFAULT_MIN_CHUNK_SECONDS = 10.0
_MAX_REQUEST_BYTES = int(1.9 * (1024 ** 3))
_WAV_EXTENSIONS = {".wav", ".wave"}
_URL_SCHEMES = {"http", "https"}
_SUPPORTED_UPLOAD_FORMATS = {"flac", "mp3", "ogg", "opus", "wav"}
_EXPORT_FORMAT_ALIASES = {
    "wave": "wav",
}
_DATA_URL_FORMAT_MAP = {
    "audio/aac": "aac",
    "audio/flac": "flac",
    "audio/m4a": "m4a",
    "audio/mp3": "mp3",
    "audio/mp4": "mp4",
    "audio/mpeg": "mp3",
    "audio/ogg": "ogg",
    "audio/wav": "wav",
    "audio/wave": "wav",
    "audio/webm": "webm",
    "audio/x-m4a": "m4a",
    "audio/x-wav": "wav",
    "video/mp4": "mp4",
    "video/quicktime": "mov",
    "video/webm": "webm",
    "video/x-matroska": "mkv",
    "video/x-msvideo": "avi",
}
_AUDIO_CONTENT_TYPE_BY_FORMAT = {
    "aac": "audio/aac",
    "flac": "audio/flac",
    "m4a": "audio/mp4",
    "mp3": "audio/mpeg",
    "mp4": "audio/mp4",
    "ogg": "audio/ogg",
    "opus": "audio/opus",
    "wav": "audio/wav",
    "wave": "audio/wav",
    "webm": "audio/webm",
}
_AUDIO_EXTENSION_BY_FORMAT = {
    "flac": "flac",
    "mp3": "mp3",
    "ogg": "ogg",
    "opus": "opus",
    "wav": "wav",
}


@dataclass(frozen=True, slots=True)
class PreparedTranscriptionAudio:
    """Reusable transcription upload payload plus decoded audio metadata."""

    audio: AudioSegment | None
    audio_bytes: bytes
    content_type: str
    file_name: str
    audio_duration_seconds: float
    upload_format: str
    normalized: bool
    source_format: str | None
    codec: str | None = None
    bitrate: str | None = None


def _safe_float(value, default=0.0):
    """Converts a value to float and falls back when conversion fails."""
    try:
        return float(value)
    except Exception:
        return default


def _clean_text(text):
    """Normalizes repeated whitespace inside text."""
    return " ".join(str(text or "").strip().split())


def _clean_optional_text(text):
    """Returns a cleaned optional text value."""
    cleaned = _clean_text(text)
    return cleaned or None


def _get_ffmpeg_executable():
    """Returns the preferred ffmpeg executable path when available."""
    if imageio_ffmpeg is not None:
        try:
            ffmpeg_executable = imageio_ffmpeg.get_ffmpeg_exe()
            if ffmpeg_executable:
                return ffmpeg_executable
        except Exception:
            pass
    return shutil.which("ffmpeg")


def _ensure_audio_segment():
    """Raises a clear error when pydub is unavailable."""
    if AudioSegment is None:
        raise ModuleNotFoundError("pydub is required to load audio inputs.")
    ffmpeg_executable = _get_ffmpeg_executable()
    if ffmpeg_executable:
        AudioSegment.converter = ffmpeg_executable
        AudioSegment.ffmpeg = ffmpeg_executable


def _looks_like_wav_bytes(media_bytes):
    """Returns whether the bytes appear to be a RIFF/WAVE payload."""
    media_bytes = bytes(media_bytes or b"")
    return len(media_bytes) >= 12 and media_bytes[:4] == b"RIFF" and media_bytes[8:12] == b"WAVE"


def _is_audio_segment(value):
    """Returns whether value is a pydub AudioSegment without importing at module load failure."""
    return AudioSegment is not None and isinstance(value, AudioSegment)


def _looks_like_url(value):
    """Returns whether a string points to a supported remote URL."""
    try:
        parsed_url = urlparse(str(value or "").strip())
    except Exception:
        return False
    return parsed_url.scheme.lower() in _URL_SCHEMES and bool(parsed_url.netloc)


def _looks_like_file_path(value):
    """Returns whether a non-existing string was likely intended as a file path."""
    value = str(value or "").strip()
    if not value:
        return False
    if any(separator in value for separator in ("/", "\\")):
        return True
    return bool(os.path.splitext(value)[1])


def _source_format_from_path(path_value):
    """Infers a source format from a local or remote path extension."""
    extension = os.path.splitext(str(urlparse(str(path_value)).path or path_value))[1].lower()
    if not extension:
        return None
    return _EXPORT_FORMAT_ALIASES.get(extension.lstrip("."), extension.lstrip("."))


def _source_format_from_content_type(content_type):
    """Infers an audio/video format from a Content-Type value."""
    mime_type = str(content_type or "").split(";", 1)[0].strip().lower()
    return _DATA_URL_FORMAT_MAP.get(mime_type)


def _normalize_upload_format(upload_format):
    """Normalizes and validates a transcription upload/export format."""
    normalized_format = _clean_text(upload_format).lower().lstrip(".") or "wav"
    normalized_format = _EXPORT_FORMAT_ALIASES.get(normalized_format, normalized_format)
    if normalized_format not in _SUPPORTED_UPLOAD_FORMATS:
        supported = ", ".join(sorted(_SUPPORTED_UPLOAD_FORMATS))
        raise ValueError(
            f"Unsupported transcription upload_format '{upload_format}'. "
            f"Supported formats: {supported}."
        )
    return normalized_format


def _safe_file_stem(file_stem):
    """Returns a safe file stem for multipart upload names."""
    return _clean_text(file_stem).replace(" ", "_") or "audio"


def _file_name_for_format(file_stem, upload_format):
    """Builds a deterministic upload file name."""
    extension = _AUDIO_EXTENSION_BY_FORMAT.get(upload_format, upload_format)
    return f"{_safe_file_stem(file_stem)}.{extension}"


def _normalize_existing_path(path_value):
    """Returns an absolute path when the input points to an existing local file."""
    normalized_path = os.path.abspath(os.fspath(path_value))
    if not os.path.exists(normalized_path):
        raise FileNotFoundError(f"Audio or video file was not found: {normalized_path}")
    return normalized_path


def _resolve_string_input_kind(audio_input):
    """Classifies string input as a local path, remote URL, or base64 payload."""
    value = str(audio_input or "").strip()
    if not value:
        raise ValueError("audio_input is empty.")

    if value.startswith("data:"):
        return "base64"

    if _looks_like_url(value):
        return "url"

    try:
        if os.path.exists(value):
            return "path"
    except OSError:
        pass

    if _looks_like_file_path(value):
        raise FileNotFoundError(f"Audio or video file was not found: {os.path.abspath(value)}")

    return "base64"


def _extract_data_url_parts(encoded_input):
    """Returns the base64 payload and an optional hinted format from a data URL."""
    encoded_input = str(encoded_input or "").strip()
    if not encoded_input.startswith("data:") or "," not in encoded_input:
        return encoded_input, None

    header, payload = encoded_input.split(",", 1)
    mime_type = header[5:].split(";", 1)[0].strip().lower()
    return payload, _DATA_URL_FORMAT_MAP.get(mime_type)


def _decode_base64_media(encoded_input):
    """Decodes a plain base64 string or data URL into media bytes."""
    encoded_input, hinted_format = _extract_data_url_parts(encoded_input)
    normalized_input = "".join(str(encoded_input or "").split())
    if not normalized_input:
        raise ValueError("audio_input base64 payload is empty.")

    padding = (-len(normalized_input)) % 4
    if padding:
        normalized_input += "=" * padding

    try:
        media_bytes = base64.b64decode(normalized_input, validate=True)
    except Exception:
        try:
            media_bytes = base64.urlsafe_b64decode(normalized_input)
        except Exception as error:
            raise ValueError("audio_input is neither an existing path nor a decodable base64 payload.") from error

    if not media_bytes:
        raise ValueError("audio_input base64 payload decoded to empty bytes.")
    return media_bytes, hinted_format


def _download_media_url(audio_url):
    """Downloads media bytes from a supported URL."""
    try:
        response = requests.get(str(audio_url), timeout=(10.0, 120.0))
        response.raise_for_status()
    except requests.RequestException as error:
        raise RuntimeError("audio_input URL could not be downloaded.") from error

    media_bytes = bytes(response.content or b"")
    if not media_bytes:
        raise ValueError("audio_input URL returned empty media bytes.")

    hinted_format = (
        _source_format_from_content_type(response.headers.get("Content-Type"))
        or _source_format_from_path(str(audio_url))
    )
    return media_bytes, hinted_format


def _normalize_audio(audio):
    """Normalizes audio to 16 kHz mono PCM16."""
    if audio.frame_rate != 16000:
        audio = audio.set_frame_rate(16000)
    if audio.channels != 1:
        audio = audio.set_channels(1)
    if audio.sample_width != 2:
        audio = audio.set_sample_width(2)
    return audio


def _decode_with_ffmpeg(*, input_path=None, input_bytes=None, hinted_format=None, normalize=True):
    """Decodes audio or video into WAV bytes using ffmpeg."""
    ffmpeg_executable = _get_ffmpeg_executable()
    if not ffmpeg_executable:
        raise RuntimeError(
            "A media decoder backend is required to read arbitrary audio/video inputs. "
            "Install 'imageio-ffmpeg' or make 'ffmpeg' available on PATH."
        )

    command = [ffmpeg_executable, "-v", "error", "-nostdin"]
    if hinted_format:
        command.extend(["-f", str(hinted_format)])
    if input_path is not None:
        command.extend(["-i", input_path])
    else:
        command.extend(["-i", "pipe:0"])
    command.append("-vn")
    if normalize:
        command.extend(["-ac", "1", "-ar", "16000"])
    command.extend(["-acodec", "pcm_s16le", "-f", "wav", "pipe:1"])

    completed_process = subprocess.run(
        command,
        input=input_bytes,
        capture_output=True,
        check=False,
    )
    if completed_process.returncode != 0 or not completed_process.stdout:
        stderr_text = completed_process.stderr.decode("utf-8", errors="ignore").strip()
        raise RuntimeError(
            "ffmpeg could not decode the provided audio_input."
            + (f" Details: {stderr_text}" if stderr_text else "")
        )

    return completed_process.stdout


def _load_audio_from_path(media_path, *, normalize_decoded=True):
    """Loads audio or video from a local file path."""
    _ensure_audio_segment()
    normalized_path = _normalize_existing_path(media_path)
    file_extension = os.path.splitext(normalized_path)[1].lower()

    if file_extension in _WAV_EXTENSIONS:
        return AudioSegment.from_wav(normalized_path)

    decoded_wav = _decode_with_ffmpeg(input_path=normalized_path, normalize=normalize_decoded)
    return AudioSegment.from_wav(io.BytesIO(decoded_wav))


def _load_audio_from_bytes(media_bytes, hinted_format=None, *, normalize_decoded=True):
    """Loads audio or video from bytes already present in memory."""
    _ensure_audio_segment()
    media_bytes = bytes(media_bytes or b"")
    if not media_bytes:
        raise ValueError("audio_input bytes are empty.")

    if hinted_format in {"wav", "wave"} or _looks_like_wav_bytes(media_bytes):
        return AudioSegment.from_wav(io.BytesIO(media_bytes))

    decoded_wav = _decode_with_ffmpeg(
        input_bytes=media_bytes,
        hinted_format=hinted_format,
        normalize=normalize_decoded,
    )
    return AudioSegment.from_wav(io.BytesIO(decoded_wav))


def load_audio(audio_input, *, normalize=True):
    """Loads `audio_input` and optionally normalizes it to 16 kHz mono PCM."""
    _ensure_audio_segment()

    if isinstance(audio_input, PreparedTranscriptionAudio):
        if audio_input.audio is not None:
            if normalize and not audio_input.normalized:
                return _normalize_audio(audio_input.audio)
            return audio_input.audio
        audio = _load_audio_from_bytes(
            audio_input.audio_bytes,
            hinted_format=audio_input.source_format or audio_input.upload_format,
            normalize_decoded=normalize,
        )
        return _normalize_audio(audio) if normalize else audio

    if _is_audio_segment(audio_input):
        return _normalize_audio(audio_input) if normalize else audio_input

    if isinstance(audio_input, bytes | bytearray | memoryview):
        audio = _load_audio_from_bytes(bytes(audio_input), normalize_decoded=normalize)
        return _normalize_audio(audio) if normalize else audio

    if isinstance(audio_input, os.PathLike):
        audio = _load_audio_from_path(audio_input, normalize_decoded=normalize)
        return _normalize_audio(audio) if normalize else audio

    if isinstance(audio_input, str):
        input_kind = _resolve_string_input_kind(audio_input)
        if input_kind == "path":
            audio = _load_audio_from_path(audio_input, normalize_decoded=normalize)
            return _normalize_audio(audio) if normalize else audio
        if input_kind == "url":
            media_bytes, hinted_format = _download_media_url(audio_input)
            audio = _load_audio_from_bytes(
                media_bytes,
                hinted_format=hinted_format,
                normalize_decoded=normalize,
            )
            return _normalize_audio(audio) if normalize else audio
        media_bytes, hinted_format = _decode_base64_media(audio_input)
        audio = _load_audio_from_bytes(
            media_bytes,
            hinted_format=hinted_format,
            normalize_decoded=normalize,
        )
        return _normalize_audio(audio) if normalize else audio

    raise TypeError(
        "audio_input must be a local path, URL, base64 string/data URL, bytes, "
        "PreparedTranscriptionAudio, or a pydub.AudioSegment."
    )


def audio_content_type(audio_format):
    """Returns the most reasonable MIME type for one audio export format."""
    normalized_format = _clean_text(audio_format).lower().lstrip(".")
    normalized_format = _EXPORT_FORMAT_ALIASES.get(normalized_format, normalized_format)
    if not normalized_format:
        return "application/octet-stream"
    return _AUDIO_CONTENT_TYPE_BY_FORMAT.get(normalized_format, "application/octet-stream")


def export_segment(segment, export_format="wav", *, codec=None, bitrate=None):
    """Exports an audio segment to bytes, optionally selecting codec and bitrate."""
    _ensure_audio_segment()
    buffer = io.BytesIO()
    normalized_format = _clean_text(export_format).lower().lstrip(".") or "wav"
    normalized_codec = _clean_optional_text(codec)
    normalized_bitrate = _clean_optional_text(bitrate)
    export_kwargs = {}
    if normalized_codec:
        export_kwargs["codec"] = normalized_codec
    if normalized_bitrate:
        export_kwargs["bitrate"] = normalized_bitrate
    try:
        segment.export(buffer, format=normalized_format, **export_kwargs)
    except Exception as error:
        details = [f"format={normalized_format!r}"]
        if normalized_codec:
            details.append(f"codec={normalized_codec!r}")
        if normalized_bitrate:
            details.append(f"bitrate={normalized_bitrate!r}")
        raise ValueError(f"Could not export transcription audio ({', '.join(details)}).") from error
    return buffer.getvalue(), audio_content_type(normalized_format)


def export_segment_as_wav(segment):
    """Exports an audio segment as WAV bytes without requiring external ffmpeg."""
    return export_segment(segment, export_format="wav")


def _extract_source_media(audio_input):
    """Returns original media bytes and best-effort source format for pass-through exports."""
    if isinstance(audio_input, PreparedTranscriptionAudio):
        return audio_input.audio_bytes, audio_input.source_format or audio_input.upload_format, audio_input.content_type

    if isinstance(audio_input, bytes | bytearray | memoryview):
        media_bytes = bytes(audio_input)
        hinted_format = "wav" if _looks_like_wav_bytes(media_bytes) else None
        return media_bytes, hinted_format, audio_content_type(hinted_format)

    if isinstance(audio_input, os.PathLike):
        normalized_path = _normalize_existing_path(audio_input)
        source_format = _source_format_from_path(normalized_path)
        with open(normalized_path, "rb") as media_file:
            return media_file.read(), source_format, audio_content_type(source_format)

    if isinstance(audio_input, str):
        input_kind = _resolve_string_input_kind(audio_input)
        if input_kind == "path":
            normalized_path = _normalize_existing_path(audio_input)
            source_format = _source_format_from_path(normalized_path)
            with open(normalized_path, "rb") as media_file:
                return media_file.read(), source_format, audio_content_type(source_format)
        if input_kind == "url":
            media_bytes, hinted_format = _download_media_url(audio_input)
            return media_bytes, hinted_format, audio_content_type(hinted_format)
        media_bytes, hinted_format = _decode_base64_media(audio_input)
        return media_bytes, hinted_format, audio_content_type(hinted_format)

    return None, None, None


def _audio_duration_seconds(audio):
    """Returns audio duration in seconds using the project precision."""
    return round(max(0.0, len(audio) / 1000.0), 6)


def _request_audio_dict(prepared_audio):
    """Converts a PreparedTranscriptionAudio object into adapter request metadata."""
    return {
        "audio": prepared_audio.audio,
        "audio_bytes": prepared_audio.audio_bytes,
        "audio_duration_seconds": prepared_audio.audio_duration_seconds,
        "content_type": prepared_audio.content_type,
        "file_name": prepared_audio.file_name,
        "upload_format": prepared_audio.upload_format,
        "normalized": prepared_audio.normalized,
        "source_format": prepared_audio.source_format,
        "codec": prepared_audio.codec,
        "bitrate": prepared_audio.bitrate,
    }


def _prepared_matches_request(prepared_audio, *, normalize, upload_format, codec, bitrate):
    """Returns whether a prepared object already satisfies requested export settings."""
    return (
        prepared_audio.normalized == bool(normalize)
        and prepared_audio.upload_format == upload_format
        and _clean_optional_text(prepared_audio.codec) == _clean_optional_text(codec)
        and _clean_optional_text(prepared_audio.bitrate) == _clean_optional_text(bitrate)
    )


def _prepare_from_existing(
    prepared_audio,
    *,
    normalize,
    upload_format,
    file_stem,
    codec,
    bitrate,
):
    """Reuses or re-exports an existing prepared transcription object."""
    if _prepared_matches_request(
        prepared_audio,
        normalize=normalize,
        upload_format=upload_format,
        codec=codec,
        bitrate=bitrate,
    ):
        return prepared_audio

    if prepared_audio.audio is None:
        raise ValueError(
            "PreparedTranscriptionAudio cannot be re-exported because it does not include "
            "a decoded audio segment."
        )
    if not normalize and prepared_audio.normalized:
        raise ValueError(
            "PreparedTranscriptionAudio was already normalized; it cannot be converted back "
            "to a non-normalized representation."
        )

    audio = _normalize_audio(prepared_audio.audio) if normalize else prepared_audio.audio
    audio_bytes, content_type = export_segment(
        audio,
        export_format=upload_format,
        codec=codec,
        bitrate=bitrate,
    )
    return PreparedTranscriptionAudio(
        audio=audio,
        audio_bytes=audio_bytes,
        content_type=content_type,
        file_name=_file_name_for_format(file_stem, upload_format),
        audio_duration_seconds=_audio_duration_seconds(audio),
        upload_format=upload_format,
        normalized=bool(normalize),
        source_format=prepared_audio.source_format,
        codec=_clean_optional_text(codec),
        bitrate=_clean_optional_text(bitrate),
    )


def prepare_transcription_audio(
    audio_input,
    *,
    normalize: bool = True,
    upload_format: str = "wav",
    file_stem: str = "audio",
    codec: str | None = None,
    bitrate: str | None = None,
) -> PreparedTranscriptionAudio:
    """Prepare reusable transcription audio bytes for provider uploads."""
    normalized_format = _normalize_upload_format(upload_format)
    normalized_codec = _clean_optional_text(codec)
    normalized_bitrate = _clean_optional_text(bitrate)

    if isinstance(audio_input, PreparedTranscriptionAudio):
        return _prepare_from_existing(
            audio_input,
            normalize=bool(normalize),
            upload_format=normalized_format,
            file_stem=file_stem,
            codec=normalized_codec,
            bitrate=normalized_bitrate,
        )

    source_bytes, source_format, source_content_type = _extract_source_media(audio_input)
    source_format = _EXPORT_FORMAT_ALIASES.get(source_format or "", source_format)
    audio = load_audio(audio_input, normalize=bool(normalize))

    can_reuse_source_bytes = (
        not normalize
        and source_bytes
        and source_format == normalized_format
        and not normalized_codec
        and not normalized_bitrate
    )
    if can_reuse_source_bytes:
        audio_bytes = bytes(source_bytes)
        content_type = source_content_type or audio_content_type(source_format)
    else:
        audio_bytes, content_type = export_segment(
            audio,
            export_format=normalized_format,
            codec=normalized_codec,
            bitrate=normalized_bitrate,
        )

    return PreparedTranscriptionAudio(
        audio=audio,
        audio_bytes=audio_bytes,
        content_type=content_type,
        file_name=_file_name_for_format(file_stem, normalized_format),
        audio_duration_seconds=_audio_duration_seconds(audio),
        upload_format=normalized_format,
        normalized=bool(normalize),
        source_format=source_format,
        codec=normalized_codec,
        bitrate=normalized_bitrate,
    )


def build_request_audio(audio_input, file_stem="audio", export_format="wav", *, codec=None, bitrate=None):
    """Builds a normalized audio payload ready to be sent to external APIs."""
    if isinstance(audio_input, PreparedTranscriptionAudio):
        return _request_audio_dict(audio_input)

    prepared_audio = prepare_transcription_audio(
        audio_input,
        normalize=True,
        upload_format=export_format,
        file_stem=file_stem,
        codec=codec,
        bitrate=bitrate,
    )
    return _request_audio_dict(prepared_audio)


def build_data_url(media_bytes, content_type):
    """Builds a `data:` URL from in-memory media bytes."""
    encoded_media = base64.b64encode(bytes(media_bytes or b"")).decode("ascii")
    normalized_content_type = _clean_text(content_type) or "application/octet-stream"
    return f"data:{normalized_content_type};base64,{encoded_media}"


def _estimate_wav_bytes(audio):
    """Estimates the uncompressed WAV payload size for the loaded audio."""
    duration_seconds = max(0.0, len(audio) / 1000.0)
    frame_rate = int(getattr(audio, "frame_rate", 16000) or 16000)
    channels = int(getattr(audio, "channels", 1) or 1)
    sample_width = int(getattr(audio, "sample_width", 2) or 2)
    return int(duration_seconds * frame_rate * channels * sample_width) + 44


def build_balanced_spans(
    audio,
    target_chunk_seconds=_DEFAULT_TARGET_CHUNK_SECONDS,
    max_chunk_seconds=_DEFAULT_MAX_CHUNK_SECONDS,
    min_chunk_seconds=_DEFAULT_MIN_CHUNK_SECONDS,
):
    """Builds balanced chunk spans in milliseconds for faster parallel uploads."""
    total_milliseconds = len(audio)
    if total_milliseconds <= 0:
        return []

    target_chunk_seconds = max(1.0, _safe_float(target_chunk_seconds, _DEFAULT_TARGET_CHUNK_SECONDS))
    max_chunk_seconds = max(target_chunk_seconds, _safe_float(max_chunk_seconds, _DEFAULT_MAX_CHUNK_SECONDS))
    min_chunk_seconds = max(1.0, min(_safe_float(min_chunk_seconds, _DEFAULT_MIN_CHUNK_SECONDS), target_chunk_seconds))

    estimated_bytes = _estimate_wav_bytes(audio)
    minimum_chunk_count = 1
    if estimated_bytes > _MAX_REQUEST_BYTES:
        minimum_chunk_count = int(math.ceil(estimated_bytes / float(_MAX_REQUEST_BYTES)))

    target_chunk_count = max(minimum_chunk_count, int(math.ceil((total_milliseconds / 1000.0) / target_chunk_seconds)))
    chunk_duration_milliseconds = int(math.ceil(total_milliseconds / float(max(1, target_chunk_count))))
    max_chunk_milliseconds = int(max_chunk_seconds * 1000)
    min_chunk_milliseconds = int(min_chunk_seconds * 1000)

    spans = []
    start_milliseconds = 0
    while start_milliseconds < total_milliseconds:
        end_milliseconds = min(total_milliseconds, start_milliseconds + chunk_duration_milliseconds)

        if spans and (total_milliseconds - start_milliseconds) < min_chunk_milliseconds:
            previous_start, previous_end = spans[-1]
            spans[-1] = (previous_start, total_milliseconds)
            break

        if (end_milliseconds - start_milliseconds) > max_chunk_milliseconds:
            end_milliseconds = min(total_milliseconds, start_milliseconds + max_chunk_milliseconds)

        spans.append((start_milliseconds, end_milliseconds))
        start_milliseconds = end_milliseconds

    if not spans:
        spans.append((0, total_milliseconds))
    return spans
