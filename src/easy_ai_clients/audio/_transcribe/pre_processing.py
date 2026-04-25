"""Provides audio loading and chunking utilities for transcription pre-processing.

Last updated: 2026-04-21
"""

import base64
import io
import math
import os
import shutil
import subprocess
import warnings

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
    "wav": "audio/wav",
    "wave": "audio/wav",
    "webm": "audio/webm",
}


def _safe_float(value, default=0.0):
    """Converts a value to float and falls back when conversion fails."""
    try:
        return float(value)
    except Exception:
        return default


def _clean_text(text):
    """Normalizes repeated whitespace inside text."""
    return " ".join(str(text or "").strip().split())


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


def _looks_like_wav_bytes(media_bytes):
    """Returns whether the bytes appear to be a RIFF/WAVE payload."""
    media_bytes = bytes(media_bytes or b"")
    return len(media_bytes) >= 12 and media_bytes[:4] == b"RIFF" and media_bytes[8:12] == b"WAVE"


def _normalize_existing_path(path_value):
    """Returns an absolute path when the input points to an existing local file."""
    normalized_path = os.path.abspath(os.fspath(path_value))
    if not os.path.exists(normalized_path):
        raise FileNotFoundError(f"Audio or video file was not found: {normalized_path}")
    return normalized_path


def _resolve_string_input_kind(audio_input):
    """Classifies string input as a local path or base64 payload."""
    value = str(audio_input or "").strip()
    if not value:
        raise ValueError("audio_input is empty.")

    if value.startswith("data:"):
        return "base64"

    try:
        if os.path.exists(value):
            return "path"
    except OSError:
        pass

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


def _normalize_audio(audio):
    """Normalizes audio to 16 kHz mono PCM16."""
    if audio.frame_rate != 16000:
        audio = audio.set_frame_rate(16000)
    if audio.channels != 1:
        audio = audio.set_channels(1)
    if audio.sample_width != 2:
        audio = audio.set_sample_width(2)
    return audio


def _decode_with_ffmpeg(*, input_path=None, input_bytes=None, hinted_format=None):
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
    command.extend(
        [
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-acodec",
            "pcm_s16le",
            "-f",
            "wav",
            "pipe:1",
        ]
    )

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


def _load_audio_from_path(media_path):
    """Loads audio or video from a local file path."""
    _ensure_audio_segment()
    normalized_path = _normalize_existing_path(media_path)
    file_extension = os.path.splitext(normalized_path)[1].lower()

    if file_extension in _WAV_EXTENSIONS:
        return AudioSegment.from_wav(normalized_path)

    decoded_wav = _decode_with_ffmpeg(input_path=normalized_path)
    return AudioSegment.from_wav(io.BytesIO(decoded_wav))


def _load_audio_from_bytes(media_bytes, hinted_format=None):
    """Loads audio or video from bytes already present in memory."""
    _ensure_audio_segment()
    media_bytes = bytes(media_bytes or b"")
    if not media_bytes:
        raise ValueError("audio_input bytes are empty.")

    if hinted_format in {"wav", "wave"} or _looks_like_wav_bytes(media_bytes):
        return AudioSegment.from_wav(io.BytesIO(media_bytes))

    decoded_wav = _decode_with_ffmpeg(input_bytes=media_bytes, hinted_format=hinted_format)
    return AudioSegment.from_wav(io.BytesIO(decoded_wav))


def load_audio(audio_input):
    """Loads `audio_input` and normalizes it to 16 kHz mono PCM."""
    _ensure_audio_segment()

    if isinstance(audio_input, AudioSegment):
        return _normalize_audio(audio_input)

    if isinstance(audio_input, (bytes, bytearray, memoryview)):
        return _normalize_audio(_load_audio_from_bytes(bytes(audio_input)))

    if isinstance(audio_input, os.PathLike):
        return _normalize_audio(_load_audio_from_path(audio_input))

    if isinstance(audio_input, str):
        input_kind = _resolve_string_input_kind(audio_input)
        if input_kind == "path":
            return _normalize_audio(_load_audio_from_path(audio_input))
        media_bytes, hinted_format = _decode_base64_media(audio_input)
        return _normalize_audio(_load_audio_from_bytes(media_bytes, hinted_format=hinted_format))

    raise TypeError(
        "audio_input must be a local path, a base64 string/data URL, bytes, or a pydub.AudioSegment."
    )


def audio_content_type(audio_format):
    """Returns the most reasonable MIME type for one audio export format."""
    normalized_format = _clean_text(audio_format).lower().lstrip(".")
    if not normalized_format:
        return "application/octet-stream"
    return _AUDIO_CONTENT_TYPE_BY_FORMAT.get(normalized_format, "application/octet-stream")


def export_segment(segment, export_format="wav"):
    """Exports an audio segment to bytes without requiring external ffmpeg."""
    buffer = io.BytesIO()
    normalized_format = _clean_text(export_format).lower().lstrip(".") or "wav"
    segment.export(buffer, format=normalized_format)
    return buffer.getvalue(), audio_content_type(normalized_format)


def export_segment_as_wav(segment):
    """Exports an audio segment as WAV bytes without requiring external ffmpeg."""
    return export_segment(segment, export_format="wav")


def build_request_audio(audio_input, file_stem="audio", export_format="wav"):
    """Builds a normalized audio payload ready to be sent to external APIs."""
    audio = load_audio(audio_input)
    normalized_stem = _clean_text(file_stem).replace(" ", "_") or "audio"
    normalized_format = _clean_text(export_format).lower().lstrip(".") or "wav"
    audio_bytes, content_type = export_segment(audio, export_format=normalized_format)
    return {
        "audio": audio,
        "audio_bytes": audio_bytes,
        "audio_duration_seconds": round(max(0.0, len(audio) / 1000.0), 6),
        "content_type": content_type,
        "file_name": f"{normalized_stem}.{normalized_format}",
    }


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
