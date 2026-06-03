import base64
import binascii

from .._common import http_utils, media_utils, provider_utils


def prepare_audio_to_music(audio, prompt=None):
    """Prepare common audio-to-music input metadata.

    Args:
        audio: Required. Audio input as URL, data URI, local path, bytes,
            base64 text, or provider-native identifier.
        prompt: Optional. Text prompt or musical instruction.

    Returns:
        A dictionary with prompt, original audio, and media metadata.
    """
    return {
        "audio": audio,
        "prompt": prompt,
        "media": describe_audio(audio),
    }


def describe_audio(audio):
    """Describe an audio input without reading local or remote data.

    Args:
        audio: Required. Audio input to describe.

    Returns:
        A dictionary with kind, filename, and MIME type.
    """
    description = media_utils.describe_media(audio)
    if description["kind"] == "unknown" and _looks_base64(audio):
        description["kind"] = "base64"
    elif description["kind"] == "unknown" and isinstance(audio, str):
        description["kind"] = "file_id"
    return description


def apply_audio_reference(payload, audio, url_field=None, base64_field=None,
                          data_uri_field=None, file_id_field=None,
                          prefer=None, mime_type=None):
    """Add an audio reference to a provider payload.

    Args:
        payload: Required. Payload dictionary to update.
        audio: Required. Audio input.
        url_field: Optional. Field for HTTP URLs.
        base64_field: Optional. Field for plain base64 audio.
        data_uri_field: Optional. Field for data URI audio.
        file_id_field: Optional. Field for provider-native file IDs.
        prefer: Optional. Preferred representation: "url", "base64",
            "data_uri", or "file_id".
        mime_type: Optional. MIME type for generated data URIs.

    Returns:
        The field name that was populated.
    """
    kind = describe_audio(audio)["kind"]
    order = _reference_order(kind, prefer)

    for item in order:
        if item == "url" and url_field and media_utils.is_remote_url(audio):
            payload[url_field] = audio
            return url_field
        if item == "data_uri" and data_uri_field:
            payload[data_uri_field] = audio_to_data_uri(audio, mime_type=mime_type)
            return data_uri_field
        if item == "base64" and base64_field:
            payload[base64_field] = audio_to_base64(audio)
            return base64_field
        if item == "file_id" and file_id_field and kind == "file_id":
            payload[file_id_field] = audio
            return file_id_field

    raise ValueError("Audio input cannot be represented by the configured provider fields.")


def audio_to_multipart_file(audio, field_name="audio", filename=None,
                            mime_type=None, timeout=60):
    """Build a requests-compatible multipart file mapping.

    Args:
        audio: Required. Audio input to read.
        field_name: Optional. Multipart field name. Defaults to "audio".
        filename: Optional. Uploaded filename.
        mime_type: Optional. Uploaded MIME type.
        timeout: Optional. Remote URL download timeout. Defaults to 60.

    Returns:
        A files dictionary accepted by requests.
    """
    filename = filename or media_utils.infer_filename(audio)
    mime_type = mime_type or media_utils.infer_mime_type(audio, default="audio/mpeg")
    return {
        field_name: (
            filename,
            audio_to_bytes(audio, timeout=timeout),
            mime_type,
        )
    }


def audio_to_bytes(audio, timeout=60):
    """Read audio input into bytes.

    Args:
        audio: Required. Audio input as bytes, path, URL, data URI, or base64.
        timeout: Optional. Remote URL timeout. Defaults to 60.

    Returns:
        Audio bytes.
    """
    if media_utils.is_bytes_like(audio) or media_utils.is_local_path(audio):
        return media_utils.read_media_bytes(audio)
    if media_utils.is_data_uri(audio):
        return _decode_data_uri(audio)
    if media_utils.is_remote_url(audio):
        return http_utils.request("GET", audio, timeout=timeout).content
    if _looks_base64(audio):
        return _decode_base64(audio)
    raise ValueError("Audio input is not readable as bytes.")


def audio_to_base64(audio, timeout=60):
    """Convert audio input to plain base64.

    Args:
        audio: Required. Audio input.
        timeout: Optional. Remote URL timeout. Defaults to 60.

    Returns:
        Plain base64 text without a data URI prefix.
    """
    if media_utils.is_data_uri(audio):
        return audio.split(",", 1)[1]
    if _looks_base64(audio):
        return _clean_base64(audio)
    return base64.b64encode(audio_to_bytes(audio, timeout=timeout)).decode("ascii")


def audio_to_data_uri(audio, mime_type=None, timeout=60):
    """Convert audio input to a data URI.

    Args:
        audio: Required. Audio input.
        mime_type: Optional. MIME type override.
        timeout: Optional. Remote URL timeout. Defaults to 60.

    Returns:
        A data URI string.
    """
    if media_utils.is_data_uri(audio):
        return audio
    mime_type = mime_type or media_utils.infer_mime_type(audio, default="audio/mpeg")
    encoded = audio_to_base64(audio, timeout=timeout)
    return f"data:{mime_type};base64,{encoded}"


def add_prompt(payload, prompt, field_name="prompt"):
    """Add a prompt to a payload when one was supplied.

    Args:
        payload: Required. Payload dictionary to update.
        prompt: Optional. Prompt text.
        field_name: Optional. Provider field name. Defaults to "prompt".

    Returns:
        The updated payload dictionary.
    """
    return provider_utils.add_optional(payload, **{field_name: prompt})


def without_internal_kwargs(kwargs):
    """Remove local transport kwargs from a provider-native payload.

    Args:
        kwargs: Required. Provider keyword arguments.

    Returns:
        A copy without local-only options.
    """
    blocked = {
        "audio_field",
        "audio_format",
        "audio_type",
        "base_url",
        "base64_field",
        "data_uri_field",
        "endpoint",
        "fal_no_retry",
        "fal_request_timeout",
        "file_field",
        "file_id_field",
        "filename",
        "headers",
        "max_wait_seconds",
        "mime_type",
        "mode",
        "poll_interval",
        "prompt_field",
        "purpose",
        "reference_file_id",
        "reference_type",
        "retries",
        "result_endpoint",
        "status_endpoint",
        "sync",
        "timeout",
        "upload_endpoint",
        "url_field",
        "vocal_file_id",
        "melody_file_id",
    }
    return {
        key: value
        for key, value in dict(kwargs or {}).items()
        if key not in blocked and value is not None
    }


def _reference_order(kind, prefer):
    if prefer:
        first = [prefer]
    elif kind == "url":
        first = ["url"]
    elif kind == "file_id":
        first = ["file_id"]
    elif kind == "data_uri":
        first = ["data_uri", "base64"]
    else:
        first = ["base64", "data_uri"]

    rest = ["url", "base64", "data_uri", "file_id"]
    return first + [item for item in rest if item not in first]


def _looks_base64(value):
    if not isinstance(value, str):
        return False
    text = _clean_base64(value)
    if len(text) < 8:
        return False
    try:
        _decode_base64(text)
    except ValueError:
        return False
    return True


def _clean_base64(value):
    return "".join(str(value).strip().split())


def _decode_data_uri(value):
    try:
        _header, encoded = value.split(",", 1)
    except ValueError as exc:
        raise ValueError("Data URI is missing base64 content.") from exc
    return _decode_base64(encoded)


def _decode_base64(value):
    text = _clean_base64(value)
    padding = "=" * (-len(text) % 4)
    try:
        return base64.b64decode(text + padding, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Audio input is not valid base64.") from exc
