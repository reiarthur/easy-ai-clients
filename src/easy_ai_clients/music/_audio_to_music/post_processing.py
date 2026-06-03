import base64
import time
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

from .._common import cost_utils, media_utils, result_utils

REFERENCE_AUDIO_WARNING = (
    "Reference audio was used. Verify usage rights, consent, and voice or "
    "musical identity permissions before production use."
)

_FINAL_URL_KEYS = (
    "audio_url",
    "music_url",
    "audioURL",
    "download_url",
    "downloadUrl",
    "flacDownloadUrl",
    "result_url",
    "resultUrl",
    "stream_url",
    "streamUrl",
    "file_url",
    "fileUrl",
    "output",
    "outputs",
    "song_paths",
    "url",
)

_SECRET_QUERY_NAMES = {
    "access_key",
    "access_token",
    "apikey",
    "api_key",
    "api-token",
    "authorization",
    "awsaccesskeyid",
    "client_secret",
    "expires",
    "key",
    "policy",
    "response-content-disposition",
    "secret",
    "security-token",
    "signature",
    "signed",
    "sig",
    "token",
    "x-amz-credential",
    "x-amz-security-token",
    "x-amz-signature",
}

_SECRET_QUERY_COMPACT_NAMES = {
    name.replace("_", "").replace("-", "")
    for name in _SECRET_QUERY_NAMES
}

_SECRET_VALUE_KEYS = {
    "access_token",
    "api_key",
    "api_token",
    "authorization",
    "bearer_token",
    "client_secret",
    "key",
    "password",
    "secret",
    "token",
}


def build_result(provider, model, response, output_path=None, status=None,
                 request_id=None, warnings=None, provider_metadata=None,
                 audio=None, include_reference_warning=True, cost=None):
    """Build a normalized provider result for audio-to-music.

    Args:
        provider: Required. Provider identifier.
        model: Optional. Provider model name or identifier.
        response: Required. Provider response.
        output_path: Optional. Destination path for bytes or URL download.
        status: Optional. Status override.
        request_id: Optional. Request ID override.
        warnings: Optional. Warning strings.
        provider_metadata: Optional. Extra metadata.
        audio: Optional. Audio bytes or decoded audio payload.
        include_reference_warning: Optional. Include reference-audio warning.
        cost: Optional. Cost metadata override.

    Returns:
        A normalized result dictionary.
    """
    urls = extract_final_urls(response)
    safe_urls = [url for url in urls if is_safe_url(url)]
    primary_url = safe_urls[0] if safe_urls else None
    saved_path = _save_output(response, audio, output_path, urls)

    metadata = dict(provider_metadata or {})
    if safe_urls:
        metadata["audio_urls"] = safe_urls
    redacted_count = len(urls) - len(safe_urls)
    if redacted_count:
        metadata["redacted_url_count"] = redacted_count

    result_warnings = list(warnings or [])
    if include_reference_warning and REFERENCE_AUDIO_WARNING not in result_warnings:
        result_warnings.append(REFERENCE_AUDIO_WARNING)

    sanitized_response = sanitize_for_output(response)
    cost = cost or cost_utils.cost_from_response(response)
    result_status = status or result_utils.extract_status(response)
    result_request_id = request_id or result_utils.extract_request_id(response)
    if result_status is None:
        if primary_url or saved_path or audio is not None:
            result_status = "completed"
        elif result_request_id:
            result_status = "submitted"

    return result_utils.normalized_result(
        provider=provider,
        operation="audio_to_music",
        model=model,
        status=result_status,
        request_id=result_request_id,
        audio_url=primary_url,
        output_path=saved_path,
        audio=audio,
        cost_usd=cost["cost_usd"],
        cost_is_estimated=cost["cost_is_estimated"],
        cost_source=cost["cost_source"],
        cost_details=cost["cost_details"],
        provider_metadata=metadata or None,
        raw_response=sanitized_response,
        warnings=result_warnings,
    )


def wait_for_result(fetch_result, max_wait_seconds=600, poll_interval=5,
                    completed_statuses=None, failed_statuses=None):
    """Poll a provider callback until it reaches a terminal status.

    Args:
        fetch_result: Required. Callable that returns the latest response.
        max_wait_seconds: Optional. Maximum wait. Defaults to 600.
        poll_interval: Optional. Poll interval. Defaults to 5.
        completed_statuses: Optional. Status strings considered complete.
        failed_statuses: Optional. Status strings considered failed.

    Returns:
        The latest response.
    """
    completed_statuses = {
        item.lower()
        for item in (completed_statuses or ("completed", "complete", "succeeded", "success"))
    }
    failed_statuses = {
        item.lower()
        for item in (failed_statuses or ("failed", "error", "canceled", "cancelled"))
    }
    deadline = time.time() + max_wait_seconds
    latest = None

    while time.time() <= deadline:
        latest = fetch_result()
        status = result_utils.extract_status(latest)
        normalized = str(status or "").lower()
        if normalized in completed_statuses or normalized in failed_statuses:
            return latest
        if result_utils.extract_audio_url(latest):
            return latest
        time.sleep(poll_interval)

    return latest


def sanitize_for_output(value):
    """Remove credential-like values and secret-bearing URLs from a response.

    Args:
        value: Required. Response value to sanitize.

    Returns:
        A sanitized copy of the response value.
    """
    if isinstance(value, dict):
        sanitized = {}
        for key, item in value.items():
            if _is_secret_value_key(key):
                sanitized[key] = "***"
            else:
                sanitized[key] = sanitize_for_output(item)
        return sanitized
    if isinstance(value, list):
        return [sanitize_for_output(item) for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize_for_output(item) for item in value)
    if isinstance(value, str) and media_utils.is_remote_url(value) and not is_safe_url(value):
        return "[redacted_url]"
    return value


def extract_final_urls(value):
    """Extract safe-candidate final audio URLs from nested provider responses.

    Args:
        value: Required. Provider response.

    Returns:
        A list of unique remote URLs.
    """
    urls = []
    _collect_final_urls(value, urls, parent_key=None)
    unique = []
    for url in urls:
        if url not in unique:
            unique.append(url)
    return unique


def is_safe_url(url):
    """Return whether a URL can be exposed without obvious secrets.

    Args:
        url: Required. URL string.

    Returns:
        True when the URL is an HTTP URL without credential-like parts.
    """
    if not media_utils.is_remote_url(url):
        return False
    parsed = urlparse(url)
    if parsed.username or parsed.password:
        return False
    for key, _value in parse_qsl(parsed.query, keep_blank_values=True):
        normalized = key.strip().lower()
        dashed = normalized.replace("_", "-")
        compact = normalized.replace("_", "").replace("-", "")
        if (
            normalized in _SECRET_QUERY_NAMES
            or dashed in _SECRET_QUERY_NAMES
            or compact in _SECRET_QUERY_COMPACT_NAMES
        ):
            return False
    return True


def audio_from_hex(value):
    """Decode hexadecimal audio content when present.

    Args:
        value: Required. Hex string.

    Returns:
        Audio bytes.
    """
    return bytes.fromhex(value)


def audio_from_base64(value):
    """Decode base64 or data URI audio content.

    Args:
        value: Required. Base64 or data URI text.

    Returns:
        Audio bytes.
    """
    text = value.split(",", 1)[1] if isinstance(value, str) and value.startswith("data:") else value
    padding = "=" * (-len(text) % 4)
    return base64.b64decode(text + padding)


def _save_output(response, audio, output_path, urls):
    if not output_path:
        return None

    path = Path(output_path)
    if path.parent:
        path.parent.mkdir(parents=True, exist_ok=True)

    audio = audio if audio is not None else _extract_audio_payload(response)
    if isinstance(audio, bytes | bytearray | memoryview):
        path.write_bytes(bytes(audio))
        return str(path)

    if urls:
        media_utils.download_url(urls[0], output_path)
        return str(path)

    return None


def _extract_audio_payload(value):
    if isinstance(value, dict):
        for key in ("audioBase64Data", "audio_data", "audioData", "audio"):
            item = value.get(key)
            if isinstance(item, str):
                if item.startswith("data:"):
                    return audio_from_base64(item)
                try:
                    return audio_from_base64(item)
                except Exception:
                    pass
        for key in ("hex", "audio_hex", "audioHex"):
            item = value.get(key)
            if isinstance(item, str):
                try:
                    return audio_from_hex(item)
                except ValueError:
                    pass
        for item in value.values():
            found = _extract_audio_payload(item)
            if found is not None:
                return found
    elif isinstance(value, list):
        for item in value:
            found = _extract_audio_payload(item)
            if found is not None:
                return found
    return None


def _collect_final_urls(value, urls, parent_key=None):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in _FINAL_URL_KEYS:
                _collect_final_urls(item, urls, parent_key=key)
            else:
                _collect_final_urls(item, urls, parent_key=key)
    elif isinstance(value, list | tuple):
        for item in value:
            _collect_final_urls(item, urls, parent_key=parent_key)
    elif isinstance(value, str) and media_utils.is_remote_url(value):
        if parent_key in _FINAL_URL_KEYS or _looks_like_final_audio_url(value):
            urls.append(value)


def _looks_like_final_audio_url(value):
    path = urlparse(value).path.lower()
    return path.endswith((".aac", ".flac", ".m4a", ".mp3", ".ogg", ".opus", ".wav"))


def _is_secret_value_key(key):
    normalized = str(key).strip().lower().replace("-", "_")
    return normalized in _SECRET_VALUE_KEYS or normalized.endswith(
        ("_api_key", "_api_token", "_secret", "_token")
    )
