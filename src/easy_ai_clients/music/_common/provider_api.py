import base64
import time
import uuid
from copy import deepcopy
from pathlib import Path

from . import env_utils, http_utils, media_utils, result_utils

POLL_INTERVAL = 5
MAX_POLL_ATTEMPTS = 60


def copy_kwargs(kwargs):
    """Return a mutable copy of provider keyword arguments.

    Args:
        kwargs: Required. Provider keyword arguments.

    Returns:
        A shallow dictionary copy.
    """
    return dict(kwargs or {})


def pop_value(payload, *names, default=None):
    """Pop the first present value from a payload.

    Args:
        payload: Required. Payload dictionary.
        *names: Required. Candidate keys to pop in order.
        default: Optional. Fallback value.

    Returns:
        The first non-missing value, or the default value.
    """
    for name in names:
        if name in payload:
            return payload.pop(name)
    return default


def add_optional(payload, **values):
    """Add non-None values to a payload dictionary.

    Args:
        payload: Required. Payload dictionary.
        **values: Optional values keyed by provider field name.

    Returns:
        The updated payload dictionary.
    """
    for key, value in values.items():
        if value is not None:
            payload[key] = value
    return payload


def merge_kwargs(payload, kwargs):
    """Merge remaining provider kwargs into a payload.

    Args:
        payload: Required. Payload dictionary.
        kwargs: Required. Remaining provider keyword arguments.

    Returns:
        The updated payload dictionary.
    """
    payload.update(kwargs)
    return payload


def reject_duplicates(kwargs, *names):
    """Reject provider-native duplicate inputs.

    Args:
        kwargs: Required. Provider keyword arguments.
        *names: Required. Duplicate field names that should not be sent.

    Raises:
        ValueError: If any duplicate field is present.
    """
    for name in names:
        if name in kwargs:
            raise ValueError(
                f"Use the public argument instead of provider-native duplicate '{name}'."
            )


def auth_headers(provider, env_name=None, scheme="bearer", extra=None):
    """Build provider authentication headers.

    Args:
        provider: Required. Provider identifier.
        env_name: Optional. Environment variable name. Defaults to provider
            configuration in `env_utils`.
        scheme: Optional. Header style. Accepted values:
            - "bearer": Use `Authorization: Bearer <key>`.
            - "authorization": Use `Authorization: <key>`.
            - "fal": Use `Authorization: Key <key>`.
            - "xi-api-key": Use `xi-api-key: <key>`.
            - "x-api-key": Use `x-api-key: <key>`.
        extra: Optional. Additional headers.

    Returns:
        A headers dictionary.
    """
    if env_name:
        value = env_utils.require_env_var(env_name)
    else:
        values = env_utils.require_env_vars(provider)
        value = next(iter(values.values()))

    headers = {}
    if scheme == "bearer":
        headers["Authorization"] = f"Bearer {value}"
    elif scheme == "authorization":
        headers["Authorization"] = value
    elif scheme == "fal":
        headers["Authorization"] = f"Key {value}"
    elif scheme in ("xi-api-key", "x-api-key"):
        headers[scheme] = value
    else:
        raise ValueError(f"Unknown auth scheme '{scheme}'.")

    headers.update(extra or {})
    return headers


def request_json(method, url, headers=None, payload=None, params=None, data=None,
                 timeout=60):
    """Send a JSON request and return parsed JSON.

    Args:
        method: Required. HTTP method.
        url: Required. Endpoint URL.
        headers: Optional. HTTP headers.
        payload: Optional. JSON request body.
        params: Optional. Query parameters.
        data: Optional. Form request body.
        timeout: Optional. Request timeout in seconds. Defaults to 60.

    Returns:
        Parsed JSON response.
    """
    return http_utils.request_json(
        method,
        url,
        headers=headers,
        params=params,
        json=payload,
        data=data,
        timeout=timeout,
    )


def request_binary(method, url, headers=None, payload=None, data=None, files=None,
                   timeout=60):
    """Send a request that can return binary content.

    Args:
        method: Required. HTTP method.
        url: Required. Endpoint URL.
        headers: Optional. HTTP headers.
        payload: Optional. JSON request body.
        data: Optional. Form fields.
        files: Optional. Multipart file mapping.
        timeout: Optional. Request timeout in seconds. Defaults to 60.

    Returns:
        The response content bytes.
    """
    response = http_utils.request(
        method,
        url,
        headers=headers,
        json=payload,
        data=data,
        files=files,
        timeout=timeout,
    )
    return response.content


def save_bytes(data, output_path):
    """Save bytes to a local path when requested.

    Args:
        data: Required. Bytes-like content.
        output_path: Optional. Destination path.

    Returns:
        The saved output path, or None.
    """
    if not output_path:
        return None

    path = Path(output_path)
    if path.parent:
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(data))
    return str(path)


def save_audio_from_response(response, output_path=None, timeout=60):
    """Download or decode common provider audio fields.

    Args:
        response: Required. Provider response dictionary.
        output_path: Optional. Destination path.
        timeout: Optional. Download timeout in seconds. Defaults to 60.

    Returns:
        The updated response dictionary.
    """
    if not isinstance(response, dict) or not output_path:
        return response

    searchable_response = _without_non_output_metadata(response)
    audio_url = result_utils.extract_audio_url(searchable_response)
    if audio_url:
        response["output_path"] = media_utils.download_url(
            audio_url,
            output_path,
            timeout=timeout,
        )
        return response

    data = _extract_data_uri(searchable_response)
    if data:
        response["output_path"] = save_bytes(_decode_data_uri(data), output_path)
        return response

    data = _extract_base64_audio(searchable_response)
    if data:
        response["output_path"] = save_bytes(base64.b64decode(data), output_path)
        return response

    data = _extract_hex_audio(searchable_response)
    if data:
        response["output_path"] = save_bytes(bytes.fromhex(data), output_path)
        return response

    return response


def poll_result(status_function, request_id, output_path=None, result_function=None,
                completed_statuses=None, failed_statuses=None, poll_interval=None,
                max_poll_attempts=None):
    """Poll an asynchronous provider until it completes or exhausts attempts.

    Args:
        status_function: Required. Callable that accepts `request_id`.
        request_id: Required. Provider request ID.
        output_path: Optional. Destination path for final audio.
        result_function: Optional. Callable used after completion.
        completed_statuses: Optional. Provider statuses treated as complete.
        failed_statuses: Optional. Provider statuses treated as failed.
        poll_interval: Optional. Delay between polls. Defaults to 5 seconds.
        max_poll_attempts: Optional. Max polling attempts. Defaults to 60.

    Returns:
        A provider response dictionary.
    """
    completed = {status.lower() for status in (
        completed_statuses or ("completed", "succeeded", "success", "done")
    )}
    failed = {status.lower() for status in (
        failed_statuses or ("failed", "error", "cancelled", "canceled")
    )}
    delay = POLL_INTERVAL if poll_interval is None else poll_interval
    attempts = MAX_POLL_ATTEMPTS if max_poll_attempts is None else max_poll_attempts

    last_response = None
    for _attempt in range(attempts):
        last_response = status_function(request_id)
        status = result_utils.extract_status(last_response)
        normalized_status = str(status).lower() if status is not None else None

        if normalized_status in failed:
            if isinstance(last_response, dict):
                last_response.setdefault("error", RuntimeError(f"Provider job failed: {status}"))
            return last_response

        if normalized_status in completed or result_utils.extract_audio_url(last_response):
            if result_function is not None:
                last_response = result_function(request_id, output_path=output_path)
            return save_audio_from_response(last_response, output_path)

        time.sleep(delay)

    if isinstance(last_response, dict):
        last_response = deepcopy(last_response)
    else:
        last_response = {"request_id": request_id}
    last_response.setdefault("request_id", request_id)
    last_response.setdefault("status", "submitted")
    last_response.setdefault(
        "warnings",
        [f"Polling ended after {attempts} attempts without a completed result."],
    )
    return last_response


def generated_task_uuid():
    """Return a UUID string for providers that require client task IDs.

    Returns:
        A UUID string.
    """
    return str(uuid.uuid4())


def safe_media_metadata(media):
    """Return media metadata without embedding bytes or base64 content.

    Args:
        media: Required. Media reference.

    Returns:
        A metadata dictionary.
    """
    if _looks_like_base64(media):
        return {
            "kind": "base64",
            "filename": "media",
            "mime_type": "application/octet-stream",
        }

    metadata = media_utils.describe_media(media)
    if media_utils.is_remote_url(media):
        metadata["source_url"] = media
    elif media_utils.is_local_path(media):
        metadata["source_path"] = str(Path(media))
    return metadata


def media_as_data_uri(media, mime_type=None):
    """Return media as a data URI when it can be converted locally.

    Args:
        media: Required. Local path, bytes, base64 string, or data URI.
        mime_type: Optional. MIME type override.

    Returns:
        A data URI string.

    Raises:
        ValueError: If the media cannot be converted locally.
    """
    if media_utils.is_data_uri(media):
        return media
    if media_utils.is_local_path(media) or media_utils.is_bytes_like(media):
        return media_utils.to_data_uri(media, mime_type=mime_type)
    if _looks_like_base64(media):
        mime_type = mime_type or "application/octet-stream"
        return f"data:{mime_type};base64,{media}"
    raise ValueError("Media must be a local path, bytes, base64, or data URI.")


def media_as_inline_data(media, mime_type=None):
    """Return a Gemini-style inline media part.

    Args:
        media: Required. Media input.
        mime_type: Optional. MIME type override.

    Returns:
        A dictionary with MIME type and base64 data.
    """
    data_uri = media_as_data_uri(media, mime_type=mime_type)
    header, data = data_uri.split(",", 1)
    mime = header[5:].split(";", 1)[0] or "application/octet-stream"
    return {"mimeType": mime, "data": data}


def multipart_file(media, field_name="file", filename=None, mime_type=None):
    """Build a requests-compatible multipart file mapping.

    Args:
        media: Required. Local path, bytes, base64 string, or data URI.
        field_name: Optional. Multipart field name. Defaults to "file".
        filename: Optional. Filename override.
        mime_type: Optional. MIME type override.

    Returns:
        A `(files, close)` tuple.
    """
    filename = filename or media_utils.infer_filename(media, default="media")
    mime_type = mime_type or media_utils.infer_mime_type(media)

    if media_utils.is_local_path(media):
        handle = Path(media).open("rb")
        return {field_name: (filename, handle, mime_type)}, handle.close

    data_uri = media_as_data_uri(media, mime_type=mime_type)
    data = _decode_data_uri(data_uri)
    return {field_name: (filename, data, mime_type)}, lambda: None


def _extract_data_uri(value):
    """Find a data URI audio value in a nested response.

    Args:
        value: Required. Response content.

    Returns:
        The first data URI string, or None.
    """
    if isinstance(value, str):
        return value if media_utils.is_data_uri(value) else None
    if isinstance(value, dict):
        for key in ("audioDataURI", "audio_data_uri", "data_uri", "audio"):
            item = value.get(key)
            if isinstance(item, str) and media_utils.is_data_uri(item):
                return item
        for item in value.values():
            found = _extract_data_uri(item)
            if found:
                return found
    elif isinstance(value, list | tuple):
        for item in value:
            found = _extract_data_uri(item)
            if found:
                return found
    return None


def _without_non_output_metadata(response):
    """Return response fields that can contain output media.

    Args:
        response: Required. Provider response dictionary.

    Returns:
        A response copy without metadata-only fields.
    """
    return {
        key: value
        for key, value in response.items()
        if key not in ("provider_metadata", "raw_response")
    }


def _extract_base64_audio(value):
    """Find a likely base64 audio payload in a nested response.

    Args:
        value: Required. Response content.

    Returns:
        The first likely base64 string, or None.
    """
    if isinstance(value, dict):
        for key in (
            "audioBase64Data",
            "audio_base64",
            "audioBase64",
            "base64_audio",
            "audio_data",
        ):
            item = value.get(key)
            if _looks_like_base64(item):
                return item
        for item in value.values():
            found = _extract_base64_audio(item)
            if found:
                return found
    elif isinstance(value, list | tuple):
        for item in value:
            found = _extract_base64_audio(item)
            if found:
                return found
    return None


def _extract_hex_audio(value):
    """Find a likely hexadecimal audio payload in a nested response.

    Args:
        value: Required. Response content.

    Returns:
        The first likely hexadecimal string, or None.
    """
    if isinstance(value, dict):
        for key in ("hex", "audio_hex", "audioHex"):
            item = value.get(key)
            if _looks_like_hex(item):
                return item
        for item in value.values():
            found = _extract_hex_audio(item)
            if found:
                return found
    elif isinstance(value, list | tuple):
        for item in value:
            found = _extract_hex_audio(item)
            if found:
                return found
    return None


def _decode_data_uri(value):
    """Decode a data URI to bytes.

    Args:
        value: Required. Data URI.

    Returns:
        Decoded bytes.
    """
    _header, data = value.split(",", 1)
    return base64.b64decode(data)


def _looks_like_base64(value):
    """Return whether a string decodes as base64.

    Args:
        value: Required. Candidate value.

    Returns:
        True when the value is a plausible base64 string.
    """
    if not isinstance(value, str) or len(value.strip()) < 16:
        return False
    text = value.strip()
    if media_utils.is_remote_url(text) or media_utils.is_data_uri(text):
        return False
    try:
        base64.b64decode(text, validate=True)
    except (ValueError, TypeError):
        return False
    return True


def _looks_like_hex(value):
    """Return whether a string looks like hexadecimal bytes.

    Args:
        value: Required. Candidate value.

    Returns:
        True when the value is a plausible hex string.
    """
    if not isinstance(value, str) or len(value) < 16 or len(value) % 2:
        return False
    try:
        bytes.fromhex(value)
    except ValueError:
        return False
    return True
