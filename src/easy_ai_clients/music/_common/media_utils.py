import base64
import mimetypes
import os
from pathlib import Path
from urllib.parse import urlparse

AUDIO_SUFFIXES = {
    ".aac",
    ".flac",
    ".m4a",
    ".mp3",
    ".ogg",
    ".opus",
    ".wav",
}
DEFAULT_AUDIO_SUFFIX = ".mp3"


def is_remote_url(value):
    """Return whether a value is an HTTP or HTTPS URL.

    Args:
        value: Required. Value to inspect.

    Returns:
        True when the value is a remote URL.
    """
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def is_data_uri(value):
    """Return whether a value is a data URI.

    Args:
        value: Required. Value to inspect.

    Returns:
        True when the value looks like a data URI.
    """
    return isinstance(value, str) and value.startswith("data:")


def is_bytes_like(value):
    """Return whether a value is bytes-like media.

    Args:
        value: Required. Value to inspect.

    Returns:
        True when the value can be converted to bytes.
    """
    return isinstance(value, bytes | bytearray | memoryview)


def clean_required_text(value, name="value"):
    """Return stripped text for required string inputs.

    Args:
        value: Required. Text-like value.
        name: Optional. Input name used in error messages.

    Returns:
        The stripped text.

    Raises:
        ValueError: If the value is missing or empty.
    """
    if value is None:
        raise ValueError(f"{name} is required.")
    text = str(value).strip()
    if not text:
        raise ValueError(f"{name} must be a non-empty string.")
    return text


def normalize_output_path(output_path):
    """Return a normalized output path string.

    Args:
        output_path: Optional. Destination path.

    Returns:
        A string path, or None when not supplied.
    """
    if output_path is None:
        return None
    return str(Path(output_path))


def normalize_audio_output_path(output_path, audio_url=None):
    """Return an output path with an audio suffix when none was supplied.

    Args:
        output_path: Required. Destination path.
        audio_url: Optional. Source URL used to infer an audio suffix.

    Returns:
        A `Path` with an audio file suffix.
    """
    path = Path(output_path)
    if path.suffix:
        return path

    suffix = _audio_suffix_from_url(audio_url) or DEFAULT_AUDIO_SUFFIX
    return path.with_suffix(suffix)


def is_local_path(value):
    """Return whether a value points to an existing local file.

    Args:
        value: Required. Value to inspect.

    Returns:
        True when the value is an existing local file path.
    """
    if isinstance(value, os.PathLike):
        return Path(value).is_file()
    if not isinstance(value, str) or is_remote_url(value) or is_data_uri(value):
        return False
    return Path(value).is_file()


def infer_filename(value, default="audio"):
    """Infer a filename from a path, URL, or fallback value.

    Args:
        value: Required. Media reference.
        default: Optional. Fallback filename. Defaults to "audio".

    Returns:
        A filename string.
    """
    if isinstance(value, os.PathLike):
        name = Path(value).name
        return name or default
    if is_remote_url(value):
        name = Path(urlparse(value).path).name
        return name or default
    if isinstance(value, str) and not is_data_uri(value):
        name = Path(value).name
        return name or default
    return default


def infer_mime_type(value, default="application/octet-stream"):
    """Infer a MIME type from a filename, URL, path, or data URI.

    Args:
        value: Required. Media reference.
        default: Optional. Fallback MIME type.

    Returns:
        A MIME type string.
    """
    if is_data_uri(value):
        header = value.split(",", 1)[0]
        mime = header[5:].split(";", 1)[0]
        return mime or default

    filename = infer_filename(value, default="")
    mime, _encoding = mimetypes.guess_type(filename)
    return mime or default


def read_media_bytes(value):
    """Return media content as bytes.

    Args:
        value: Required. Bytes-like value or local file path.

    Returns:
        Media bytes.

    Raises:
        ValueError: If the value cannot be read locally.
    """
    if is_bytes_like(value):
        return bytes(value)
    if is_local_path(value):
        return Path(value).read_bytes()
    raise ValueError("Media value is not bytes-like or an existing local file path.")


def to_data_uri(value, mime_type=None):
    """Convert bytes-like media or a local file to a data URI.

    Args:
        value: Required. Bytes-like value, local file path, or data URI.
        mime_type: Optional. MIME type override.

    Returns:
        A data URI string.
    """
    if is_data_uri(value):
        return value
    data = read_media_bytes(value)
    mime_type = mime_type or infer_mime_type(value)
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def describe_media(value):
    """Describe a media input without reading remote content.

    Args:
        value: Required. Media reference.

    Returns:
        A dictionary with kind, filename, and MIME type.
    """
    if is_remote_url(value):
        kind = "url"
    elif is_data_uri(value):
        kind = "data_uri"
    elif is_local_path(value):
        kind = "path"
    elif is_bytes_like(value):
        kind = "bytes"
    else:
        kind = "unknown"

    return {
        "kind": kind,
        "filename": infer_filename(value),
        "mime_type": infer_mime_type(value),
    }


def download_url(audio_url, output_path, timeout=60):
    """Download a remote URL to an output path.

    Args:
        audio_url: Required. HTTP or HTTPS URL.
        output_path: Required. Destination file path.
        timeout: Optional. Request timeout in seconds. Defaults to 60.

    Returns:
        The output path as a string.
    """
    if not is_remote_url(audio_url):
        raise ValueError("audio_url must be an HTTP or HTTPS URL.")
    if not output_path:
        raise ValueError("output_path is required when downloading audio_url.")

    try:
        import requests
    except ImportError as exc:
        raise RuntimeError("The 'requests' package is required to download media.") from exc

    path = normalize_audio_output_path(output_path, audio_url)
    if path.parent:
        path.parent.mkdir(parents=True, exist_ok=True)

    with requests.get(audio_url, stream=True, timeout=timeout) as response:
        response.raise_for_status()
        with path.open("wb") as file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    file.write(chunk)

    return str(path)


def _audio_suffix_from_url(audio_url):
    """Infer a safe audio suffix from a source URL.

    Args:
        audio_url: Optional. Source URL.

    Returns:
        An audio suffix, or None when it cannot be inferred.
    """
    if not is_remote_url(audio_url):
        return None

    suffix = Path(urlparse(audio_url).path).suffix.lower()
    if suffix in AUDIO_SUFFIXES:
        return suffix
    return None
