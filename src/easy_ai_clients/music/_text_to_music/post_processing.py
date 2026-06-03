import base64
import time
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .._common import cost_utils, media_utils, result_utils

SENSITIVE_KEYS = {
    "api_key",
    "apikey",
    "authorization",
    "bearer_token",
    "client_secret",
    "credential",
    "key",
    "password",
    "secret",
    "signature",
    "token",
    "x-api-key",
    "xi-api-key",
}

SENSITIVE_MARKERS = (
    "api_key",
    "apikey",
    "authorization",
    "client_secret",
    "credential",
    "secret",
    "signature",
    "token",
)

ASYNC_REF_KEYS = (
    "status_url",
    "response_url",
    "result_url",
    "task_url",
    "operation_url",
    "webhook_url",
)

COMPLETED_STATUSES = {
    "complete",
    "completed",
    "done",
    "generated",
    "success",
    "succeeded",
}

FAILED_STATUSES = {
    "canceled",
    "cancelled",
    "error",
    "failed",
    "failure",
}

AUDIO_URL_KEYS = (
    "audio_url",
    "audioUrl",
    "audioURL",
    "music_url",
    "musicUrl",
    "download_url",
    "downloadUrl",
    "flacDownloadUrl",
    "result_url",
    "resultUrl",
    "stream_url",
    "streamUrl",
    "file_url",
    "fileUrl",
    "audio",
    "url",
)

AUDIO_DATA_KEYS = (
    "audioBase64Data",
    "audio_base64_data",
    "audioDataURI",
    "audio_data_uri",
    "audio_data",
    "audioData",
    "base64",
)


def build_result(provider, model=None, status=None, raw_response=None,
                 request_id=None, audio_url=None, output_path=None, audio=None,
                 cost=None, provider_metadata=None, warnings=None, **refs):
    """Build a normalized text-to-music result.

    Args:
        provider: Required. Provider identifier.
        model: Optional. Model name or identifier.
        status: Optional. Normalized status.
        raw_response: Optional. Provider response.
        request_id: Optional. Provider request ID.
        audio_url: Optional. Final audio URL.
        output_path: Optional. Saved output path.
        audio: Optional. Audio bytes.
        cost: Optional. Normalized cost dictionary.
        provider_metadata: Optional. Safe provider metadata.
        warnings: Optional. Warning strings.
        **refs: Optional. Safe async references.

    Returns:
        A normalized result dictionary.
    """
    safe_raw = sanitize_response(raw_response)
    safe_refs = _safe_refs(refs)
    metadata = dict(provider_metadata or {})
    metadata.update(safe_refs)

    request_id = request_id or result_utils.extract_request_id(raw_response)
    audio_url = audio_url or result_utils.extract_audio_url(raw_response)
    safe_audio_url = sanitize_response(audio_url) if audio_url else None
    status_is_explicit = status is not None
    status = status or result_utils.extract_status(raw_response)
    if (
        not status_is_explicit
        and (audio_url or output_path or audio is not None)
        and not _is_failed_status(status)
    ):
        status = "completed"
    if status is None:
        status = _infer_status(request_id, audio_url, output_path, audio)

    cost = cost or unavailable_cost()
    result = result_utils.normalized_result(
        provider=provider,
        operation="text_to_music",
        model=model,
        status=status,
        request_id=request_id,
        audio_url=safe_audio_url,
        output_path=output_path,
        audio=audio,
        cost_usd=cost["cost_usd"],
        cost_is_estimated=cost["cost_is_estimated"],
        cost_source=cost["cost_source"],
        cost_details=cost["cost_details"],
        provider_metadata=metadata or None,
        raw_response=safe_raw,
        warnings=warnings,
    )

    for key, value in safe_refs.items():
        result[key] = value
    return result


def failure_result(provider, model=None, exc=None, raw_response=None,
                   request_id=None, audio_url=None, output_path=None,
                   warnings=None):
    """Build a normalized text-to-music failure result.

    Args:
        provider: Required. Provider identifier.
        model: Optional. Model name or identifier.
        exc: Optional. Error object.
        raw_response: Optional. Provider response.
        request_id: Optional. Provider request ID.
        audio_url: Optional. Audio URL.
        output_path: Optional. Output path.
        warnings: Optional. Warning strings.

    Returns:
        A normalized failure result dictionary.
    """
    result = result_utils.failure_result(
        provider=provider,
        model=model,
        operation="text_to_music",
        exc=exc,
        request_id=request_id,
        audio_url=sanitize_response(audio_url) if audio_url else None,
        output_path=output_path,
        raw_response=sanitize_response(raw_response),
        warnings=warnings,
    )
    result.update(unavailable_cost())
    return result


def unavailable_cost(source="unavailable", details=None):
    """Return required unavailable cost metadata.

    Args:
        source: Optional. Cost source label.
        details: Optional. Extra cost details.

    Returns:
        Normalized cost metadata.
    """
    return {
        "cost_usd": 0.0,
        "cost_is_estimated": False,
        "cost_source": source,
        "cost_details": details,
    }


def estimated_cost(cost_usd, source, details=None):
    """Return estimated cost metadata.

    Args:
        cost_usd: Required. Estimated cost in USD.
        source: Required. Cost source label.
        details: Optional. Extra cost details.

    Returns:
        Normalized cost metadata.
    """
    return {
        "cost_usd": float(cost_usd),
        "cost_is_estimated": True,
        "cost_source": source,
        "cost_details": details,
    }


def save_audio_bytes(audio, output_path):
    """Save audio bytes to disk.

    Args:
        audio: Required. Audio bytes.
        output_path: Required. Destination path.

    Returns:
        The saved output path as a string.
    """
    if not output_path:
        return None
    path = Path(output_path)
    if path.parent:
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(audio)
    return str(path)


def decode_base64_audio(value):
    """Decode provider audio encoded as base64.

    Args:
        value: Required. Base64 audio value.

    Returns:
        Decoded audio bytes.
    """
    if "," in value and value.strip().startswith("data:"):
        value = value.split(",", 1)[1]
    return base64.b64decode(value)


def download_audio(audio_url, output_path, timeout=60):
    """Download a final audio URL when an output path is provided.

    Args:
        audio_url: Required. Final audio URL.
        output_path: Optional. Destination path.
        timeout: Optional. Download timeout.

    Returns:
        The saved path, or None when no output path is provided.
    """
    if audio_url and output_path:
        return media_utils.download_url(audio_url, output_path, timeout=timeout)
    return None


def first_audio_url(value):
    """Return the first likely audio URL from a provider response.

    Args:
        value: Required. Provider response.

    Returns:
        The first audio URL, or None.
    """
    return result_utils.extract_audio_url(value)


def normalize_response(provider, model, response, output_path=None, cost=None,
                       status=None, refs=None, request_id=None, audio=None,
                       warnings=None, download_timeout=60):
    """Normalize a provider response for text-to-music.

    Args:
        provider: Required. Provider identifier.
        model: Optional. Model identifier.
        response: Required. Provider response.
        output_path: Optional. Destination path for final audio.
        cost: Optional. Normalized cost metadata.
        status: Optional. Status override.
        refs: Optional. Safe provider reference URLs.
        request_id: Optional. Provider request ID override.
        audio: Optional. Audio bytes or base64 payload override.
        warnings: Optional. Warning strings.
        download_timeout: Optional. Download timeout in seconds.

    Returns:
        A normalized music result dictionary.
    """
    raw_status = status or result_utils.extract_status(response)
    if _is_failed_status(raw_status):
        return result_utils.failure_result(
            provider=provider,
            model=model,
            exc=_failure_message(response, raw_status),
            request_id=request_id or result_utils.extract_request_id(response),
            raw_response=sanitize_response(response),
            warnings=warnings,
        )

    candidates = collect_audio_candidates(response)
    audio_url = candidates[0]["url"] if candidates else None
    request_id = request_id or result_utils.extract_request_id(response)
    audio = audio if audio is not None else extract_audio_data(response)
    saved_path = None

    if output_path and audio_url:
        saved_path = media_utils.download_url(
            audio_url,
            output_path,
            timeout=download_timeout,
        )
    elif output_path and audio is not None:
        saved_path = save_audio_payload(audio, output_path)

    normalized_status = _normalized_status(
        raw_status,
        audio_url=audio_url,
        output_path=saved_path,
        audio=audio,
        request_id=request_id,
    )

    metadata = {
        "audio_candidates": sanitize_response(candidates),
        "refs": safe_refs(refs),
    }
    metadata = {
        key: value
        for key, value in metadata.items()
        if value
    }

    cost = cost or cost_utils.cost_from_response(response)
    result = result_utils.normalized_result(
        provider=provider,
        operation="text_to_music",
        model=model,
        status=normalized_status,
        request_id=request_id,
        audio_url=sanitize_response(audio_url) if audio_url else None,
        output_path=saved_path,
        audio=audio if not saved_path else None,
        cost_usd=cost.get("cost_usd"),
        cost_is_estimated=cost.get("cost_is_estimated", False),
        cost_source=cost.get("cost_source"),
        cost_details=cost.get("cost_details"),
        provider_metadata=metadata or None,
        raw_response=sanitize_response(response),
        warnings=warnings,
    )
    result.update(safe_refs(refs))
    return result


def sanitize_response(value):
    """Redact secrets and credential-bearing URLs from response content.

    Args:
        value: Required. Provider response value.

    Returns:
        A sanitized value safe for normalized results.
    """
    if isinstance(value, dict):
        safe = {}
        for key, item in value.items():
            if _is_sensitive_key(key):
                safe[key] = "[redacted]"
            else:
                safe[key] = sanitize_response(item)
        return safe
    if isinstance(value, list):
        return [sanitize_response(item) for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize_response(item) for item in value)
    if isinstance(value, bytes | bytearray | memoryview):
        return {"binary_length": len(value)}
    if isinstance(value, str):
        return _sanitize_string(value)
    return value


def collect_audio_candidates(value):
    """Collect audio-like URL candidates from a provider response.

    Args:
        value: Required. Provider response.

    Returns:
        A list of dictionaries with `key` and `url`.
    """
    candidates = []
    _collect_audio_candidates(value, candidates)
    return _dedupe_candidates(candidates)


def extract_audio_data(value):
    """Extract inline audio data from common provider response shapes.

    Args:
        value: Required. Provider response.

    Returns:
        Audio bytes/base64/data URI when found, otherwise None.
    """
    if isinstance(value, bytes | bytearray | memoryview):
        return bytes(value)
    if isinstance(value, dict):
        for key in AUDIO_DATA_KEYS:
            candidate = value.get(key)
            if candidate and not media_utils.is_remote_url(candidate):
                return candidate
        for item in value.values():
            found = extract_audio_data(item)
            if found is not None:
                return found
    elif isinstance(value, list | tuple):
        for item in value:
            found = extract_audio_data(item)
            if found is not None:
                return found
    return None


def save_audio_payload(audio, output_path):
    """Save inline audio bytes, base64, or data URI content.

    Args:
        audio: Required. Audio payload.
        output_path: Required. Destination path.

    Returns:
        The saved output path as a string.
    """
    path = Path(output_path)
    if path.parent:
        path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(audio, bytes | bytearray | memoryview):
        data = bytes(audio)
    elif isinstance(audio, str) and media_utils.is_data_uri(audio):
        data = base64.b64decode(audio.split(",", 1)[1])
    elif isinstance(audio, str):
        data = base64.b64decode(audio)
    else:
        raise ValueError("Unsupported inline audio payload.")

    path.write_bytes(data)
    return str(path)


def safe_refs(refs):
    """Return provider reference URLs that do not expose credentials.

    Args:
        refs: Optional. Reference URL mapping.

    Returns:
        A filtered mapping.
    """
    safe = {}
    for key, value in dict(refs or {}).items():
        if value and _is_safe_ref(value):
            safe[key] = sanitize_response(value)
    return safe


def poll_until_ready(fetch, is_ready=None, poll_interval=5, max_polls=60):
    """Poll a provider result until it reaches a terminal status.

    Args:
        fetch: Required. Callable that returns the latest response.
        is_ready: Optional. Custom terminal-state callable.
        poll_interval: Optional. Delay between attempts.
        max_polls: Optional. Maximum polling attempts.

    Returns:
        The last provider response.
    """
    last_response = None
    for attempt in range(max_polls):
        last_response = fetch()
        if is_ready:
            if is_ready(last_response):
                return last_response
        elif is_terminal_response(last_response):
            return last_response
        if attempt < max_polls - 1:
            time.sleep(poll_interval)
    return last_response


def is_terminal_response(response):
    """Return whether a response has a terminal status or final audio.

    Args:
        response: Required. Provider response.

    Returns:
        True when polling can stop.
    """
    status = result_utils.extract_status(response)
    if _is_completed_status(status) or _is_failed_status(status):
        return True
    return bool(collect_audio_candidates(response) or extract_audio_data(response))


def _infer_status(request_id, audio_url, output_path, audio):
    """Infer a normalized status from available output fields.

    Args:
        request_id: Optional. Provider request ID.
        audio_url: Optional. Audio URL.
        output_path: Optional. Output path.
        audio: Optional. Audio bytes.

    Returns:
        A normalized status value.
    """
    if audio_url or output_path or audio is not None:
        return "completed"
    if request_id:
        return "submitted"
    return None


def _safe_refs(refs):
    """Return sanitized async references.

    Args:
        refs: Required. Candidate reference dictionary.

    Returns:
        A dictionary with known async reference keys.
    """
    safe = {}
    for key in ASYNC_REF_KEYS:
        value = refs.get(key)
        if value and _is_safe_ref(value):
            safe[key] = sanitize_response(value)
    return safe


def _collect_audio_candidates(value, candidates):
    if isinstance(value, str):
        if media_utils.is_remote_url(value):
            candidates.append({"key": "url", "url": value})
        return

    if isinstance(value, dict):
        for key in AUDIO_URL_KEYS:
            candidate = value.get(key)
            if isinstance(candidate, str) and media_utils.is_remote_url(candidate):
                candidates.append({"key": key, "url": candidate})
            elif isinstance(candidate, dict | list | tuple):
                _collect_audio_candidates(candidate, candidates)

        for key, item in value.items():
            if key in AUDIO_URL_KEYS:
                continue
            if isinstance(item, dict | list | tuple):
                _collect_audio_candidates(item, candidates)
        return

    if isinstance(value, list | tuple):
        for item in value:
            _collect_audio_candidates(item, candidates)


def _dedupe_candidates(candidates):
    seen = set()
    deduped = []
    for candidate in candidates:
        url = candidate["url"]
        if url not in seen:
            seen.add(url)
            deduped.append(candidate)
    return deduped


def _normalized_status(raw_status, audio_url=None, output_path=None, audio=None,
                       request_id=None):
    if audio_url or output_path or audio is not None:
        return "completed"
    if _is_completed_status(raw_status):
        return "completed"
    if request_id:
        return "submitted"
    return raw_status


def _is_completed_status(status):
    return _normalized_provider_status(status) in COMPLETED_STATUSES


def _is_failed_status(status):
    return _normalized_provider_status(status) in FAILED_STATUSES


def _normalized_provider_status(status):
    if status is None:
        return None
    return str(status).strip().lower()


def _failure_message(response, status):
    if isinstance(response, dict):
        for key in ("error", "message", "detail"):
            if response.get(key):
                return RuntimeError(str(response[key]))
    return RuntimeError(f"Provider returned terminal failure status: {status}.")


def _is_safe_ref(value):
    if not isinstance(value, str) or not media_utils.is_remote_url(value):
        return False
    lowered = value.lower()
    blocked = ("api_key", "apikey", "token", "secret", "password", "signature")
    return not any(item in lowered for item in blocked)


def _is_sensitive_key(key):
    """Return whether a response key should be redacted.

    Args:
        key: Required. Response key.

    Returns:
        True when the key looks sensitive.
    """
    normalized = str(key).strip().lower().replace("_", "-")
    compact = normalized.replace("-", "")
    sensitive_compact = {item.replace("-", "") for item in SENSITIVE_KEYS}
    if normalized in SENSITIVE_KEYS or compact in sensitive_compact:
        return True
    return any(marker.replace("_", "-") in normalized for marker in SENSITIVE_MARKERS)


def _sanitize_string(value):
    """Sanitize a string response value.

    Args:
        value: Required. String value.

    Returns:
        Sanitized string value.
    """
    if not media_utils.is_remote_url(value):
        return value
    return _redact_credential_query(value)


def _redact_credential_query(url):
    """Remove credential-bearing query strings from URLs.

    Args:
        url: Required. URL.

    Returns:
        Sanitized URL.
    """
    parsed = urlsplit(url)
    if not parsed.query:
        return url

    query = parse_qsl(parsed.query, keep_blank_values=True)
    if not any(_is_sensitive_key(key) for key, _value in query):
        return url

    redacted = urlencode({"redacted": "true"})
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, redacted, ""))
