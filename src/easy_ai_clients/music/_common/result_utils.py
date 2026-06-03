from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from ..._error_utils import attach_error, error_message
from . import cost_utils, media_utils

RESULT_KEYS = (
    "provider",
    "operation",
    "model",
    "status",
    "request_id",
    "audio_url",
    "music_url",
    "output_path",
    "audio",
    "stems",
    "cost_usd",
    "cost_currency",
    "cost_is_estimated",
    "cost_source",
    "cost_details",
    "provider_metadata",
    "raw_response",
    "warnings",
    "status_url",
    "response_url",
    "result_url",
    "task_url",
    "operation_url",
    "poll_url",
    "download_url",
    "webhook_url",
)

SECRET_QUERY_NAMES = {
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

SECRET_QUERY_COMPACT_NAMES = {
    name.replace("_", "").replace("-", "")
    for name in SECRET_QUERY_NAMES
}

ASYNC_REF_KEY_MAP = {
    "status_url": ("status_url", "statusUrl", "statusURL"),
    "response_url": ("response_url", "responseUrl", "responseURL"),
    "result_url": ("result_url", "resultUrl", "resultURL"),
    "task_url": ("task_url", "taskUrl", "taskURL"),
    "operation_url": ("operation_url", "operationUrl", "operationURL"),
    "poll_url": ("poll_url", "pollUrl", "pollURL"),
    "download_url": ("download_url", "downloadUrl", "downloadURL"),
    "webhook_url": ("webhook_url", "webhookUrl", "webhookURL"),
}


def normalized_result(provider=None, operation=None, model=None, status=None, request_id=None,
                      audio_url=None, output_path=None, audio=None, stems=None,
                      cost_usd=None, cost_is_estimated=False, cost_source=None,
                      cost_details=None, provider_metadata=None,
                      raw_response=None, warnings=None):
    """Build a normalized music result dictionary.

    Args:
        provider: Optional. Provider identifier.
        operation: Optional. Public operation name.
        model: Optional. Model name or identifier.
        status: Optional. Provider or normalized status.
        request_id: Optional. Provider request ID.
        audio_url: Optional. Generated audio URL.
        output_path: Optional. Saved output path.
        audio: Optional. Audio bytes or provider audio payload.
        stems: Optional. Stem separation output.
        cost_usd: Optional. Cost in USD.
        cost_is_estimated: Optional. Whether cost is estimated.
        cost_source: Optional. Cost metadata source.
        cost_details: Optional. Provider-specific cost details.
        provider_metadata: Optional. Provider-specific metadata.
        raw_response: Optional. Original provider response.
        warnings: Optional. Warning strings.

    Returns:
        A normalized result dictionary.
    """
    safe_audio_url = sanitize_response(audio_url) if audio_url else None

    return {
        "provider": provider,
        "operation": operation,
        "model": model,
        "status": status,
        "request_id": request_id,
        "audio_url": safe_audio_url,
        "music_url": safe_audio_url,
        "output_path": output_path,
        "audio": audio,
        "stems": stems,
        "cost_usd": 0.0 if cost_usd is None else cost_usd,
        "cost_currency": "USD",
        "cost_is_estimated": bool(cost_is_estimated),
        "cost_source": cost_source or "unavailable",
        "cost_details": cost_details or {},
        "provider_metadata": sanitize_response(provider_metadata),
        "raw_response": sanitize_response(raw_response),
        "warnings": sanitize_response(list(warnings or [])),
    }


def failure_result(provider=None, model=None, operation=None, exc=None,
                   request_id=None, audio_url=None, output_path=None,
                   raw_response=None, warnings=None):
    """Build a normalized failure result.

    Args:
        provider: Optional. Provider identifier.
        model: Optional. Model name or identifier.
        operation: Optional. Public operation name.
        exc: Optional. Exception or error value.
        request_id: Optional. Provider request ID.
        audio_url: Optional. Related audio URL.
        output_path: Optional. Related output path.
        raw_response: Optional. Original provider response.
        warnings: Optional. Warning strings.

    Returns:
        A normalized result dictionary with an error object.
    """
    result = normalized_result(
        provider=provider,
        operation=operation,
        model=model,
        status="failed",
        request_id=request_id,
        audio_url=audio_url,
        output_path=output_path,
        raw_response=raw_response,
        warnings=warnings,
    )
    if exc is not None:
        result = attach_error(result, exc, provider=provider, operation=operation, model=model)
    return result


def normalize_provider_result(provider, model, raw_response, operation=None,
                              output_path=None, status=None, stems=False):
    """Normalize common provider response shapes.

    Args:
        provider: Required. Provider identifier.
        model: Optional. Model name or identifier.
        raw_response: Required. Provider response value.
        operation: Optional. Public operation name. Used only for failures.
        output_path: Optional. Saved output path.
        status: Optional. Status override.
        stems: Optional. Whether the main output should be stems.

    Returns:
        A normalized result dictionary.
    """
    provider_raw_response = _provider_raw_response(raw_response)

    if isinstance(raw_response, dict) and raw_response.get("error"):
        result = failure_result(
            provider=provider,
            model=model or raw_response.get("model"),
            operation=operation,
            exc=raw_response.get("error"),
            request_id=extract_request_id(raw_response),
            audio_url=extract_audio_url(raw_response),
            output_path=raw_response.get("output_path") or output_path,
            raw_response=provider_raw_response,
            warnings=raw_response.get("warnings"),
        )
        return result

    metadata = None
    warnings = None
    audio = None
    stem_output = None
    result_output_path = output_path

    if isinstance(raw_response, dict):
        metadata = raw_response.get("provider_metadata")
        warnings = raw_response.get("warnings")
        audio = raw_response.get("audio")
        stem_output = raw_response.get("stems")
        result_output_path = raw_response.get("output_path") or output_path
        model = model or raw_response.get("model")
    elif isinstance(raw_response, bytes | bytearray | memoryview):
        audio = bytes(raw_response)
    elif isinstance(raw_response, str) and not media_utils.is_remote_url(raw_response):
        result_output_path = result_output_path or raw_response

    audio_url = extract_audio_url(raw_response)
    request_id = extract_request_id(raw_response)
    result_status = status or extract_status(raw_response)
    if result_status is None:
        result_status = _infer_status(audio_url, result_output_path, audio, stem_output, request_id)

    cost = cost_utils.cost_from_response(raw_response)
    if stems and stem_output is None:
        stem_output = extract_stems(raw_response)

    result = normalized_result(
        provider=provider,
        operation=operation,
        model=model,
        status=result_status,
        request_id=request_id,
        audio_url=audio_url,
        output_path=result_output_path,
        audio=audio,
        stems=stem_output,
        cost_usd=cost["cost_usd"],
        cost_is_estimated=cost["cost_is_estimated"],
        cost_source=cost["cost_source"],
        cost_details=cost["cost_details"],
        provider_metadata=metadata,
        raw_response=provider_raw_response,
        warnings=warnings,
    )
    result.update(extract_async_refs(raw_response))
    return result


def extract_audio_url(value):
    """Extract a URL from common provider response shapes.

    Args:
        value: Required. Provider response.

    Returns:
        The first likely audio URL, or None.
    """
    if isinstance(value, str):
        if media_utils.is_remote_url(value):
            return value
        return None

    keys = (
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
        "url",
    )
    return _find_url(value, keys)


def extract_async_refs(value):
    """Extract safe asynchronous reference URLs from provider responses.

    Args:
        value: Required. Provider response.

    Returns:
        A dictionary with safe async reference URLs.
    """
    refs = {}
    for key, aliases in ASYNC_REF_KEY_MAP.items():
        found = _find_first(value, aliases)
        if isinstance(found, str) and media_utils.is_remote_url(found):
            sanitized = sanitize_response(found)
            if sanitized:
                refs[key] = sanitized
    return refs


def extract_request_id(value):
    """Extract a request or task ID from common provider response shapes.

    Args:
        value: Required. Provider response.

    Returns:
        The first likely request ID, or None.
    """
    keys = (
        "request_id",
        "requestId",
        "task_id",
        "taskId",
        "taskUUID",
        "prediction_id",
        "predictionId",
        "generation_id",
        "generationId",
        "job_id",
        "jobId",
        "operation_id",
        "operationId",
        "id",
    )
    return _find_first(value, keys)


def extract_status(value):
    """Extract status from common provider response shapes.

    Args:
        value: Required. Provider response.

    Returns:
        The first likely status value, or None.
    """
    return _find_first(value, ("status", "state", "stage"))


def extract_stems(value):
    """Extract stems from common provider response shapes.

    Args:
        value: Required. Provider response.

    Returns:
        Stem output when found, or None.
    """
    found = _find_first(value, ("stems", "stem_urls", "stemUrls", "tracks", "parts"))
    if found is not None:
        return found
    return _extract_flat_stem_urls(value)


def _infer_status(audio_url, output_path, audio, stems, request_id):
    """Infer a status when a provider response does not include one.

    Args:
        audio_url: Optional. Audio URL.
        output_path: Optional. Saved output path.
        audio: Optional. Audio payload.
        stems: Optional. Stem output.
        request_id: Optional. Provider request ID.

    Returns:
        A normalized status string or None.
    """
    if audio_url or output_path or audio is not None or stems is not None:
        return "completed"
    if request_id:
        return "submitted"
    return None


def _provider_raw_response(value):
    """Return the original provider response when a provider wrapper supplies it.

    Args:
        value: Required. Provider wrapper or raw response.

    Returns:
        The original provider response when available, otherwise the input value.
    """
    if isinstance(value, dict) and "raw_response" in value:
        return value.get("raw_response")
    return value


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
        if media_utils.is_remote_url(value):
            return _redact_credential_query(value)
        return error_message(value)
    return value


def _find_url(value, keys):
    """Find the first remote URL in nested dictionaries and lists.

    Args:
        value: Required. Provider response.
        keys: Required. Candidate URL keys.

    Returns:
        The first remote URL, or None.
    """
    if isinstance(value, dict):
        for key in keys:
            candidate = value.get(key)
            if isinstance(candidate, str) and media_utils.is_remote_url(candidate):
                return candidate
            if isinstance(candidate, dict):
                nested = _find_url(candidate, keys)
                if nested:
                    return nested
            if isinstance(candidate, list | tuple):
                nested = _find_url(candidate, keys)
                if nested:
                    return nested

        for item in value.values():
            nested = _find_url(item, keys)
            if nested:
                return nested
    elif isinstance(value, list | tuple):
        for item in value:
            nested = _find_url(item, keys)
            if nested:
                return nested
    elif isinstance(value, str) and media_utils.is_remote_url(value):
        return value

    return None


def _find_first(value, keys):
    """Find the first matching value in nested dictionaries and lists.

    Args:
        value: Required. Provider response.
        keys: Required. Candidate keys.

    Returns:
        The first matching value, or None.
    """
    if isinstance(value, dict):
        for key in keys:
            if key in value and value[key] is not None:
                return value[key]
        for item in value.values():
            found = _find_first(item, keys)
            if found is not None:
                return found
    elif isinstance(value, list | tuple):
        for item in value:
            found = _find_first(item, keys)
            if found is not None:
                return found
    return None


def _extract_flat_stem_urls(value):
    """Extract flat stem URL fields such as `vocals_url`.

    Args:
        value: Required. Provider response.

    Returns:
        A dictionary of stem names to URLs, or None.
    """
    if not isinstance(value, dict):
        return None

    stems = {}
    ignored = {
        "audio_url",
        "music_url",
        "download_url",
        "result_url",
        "stream_url",
        "file_url",
        "url",
    }
    for key, item in value.items():
        normalized = str(key).strip().lower()
        if normalized in ignored or not normalized.endswith("_url"):
            continue
        stem_name = normalized.removesuffix("_url")
        if stem_name in {"stem", "stems", "zip"}:
            continue
        if isinstance(item, str) and media_utils.is_remote_url(item):
            stems[stem_name] = item

    return stems or None


def _is_sensitive_key(key):
    """Return whether a response key should be redacted.

    Args:
        key: Required. Response key.

    Returns:
        True when the key looks credential-like.
    """
    normalized = str(key).strip().lower().replace("-", "_")
    compact = normalized.replace("_", "")
    sensitive = {
        "access_key",
        "access_token",
        "api_key",
        "apikey",
        "api_token",
        "authorization",
        "bearer_token",
        "client_secret",
        "credential",
        "key",
        "password",
        "secret",
        "signature",
        "token",
        "x_api_key",
        "xi_api_key",
    }
    sensitive_compact = {item.replace("_", "") for item in sensitive}
    if normalized in sensitive or compact in sensitive_compact:
        return True
    return normalized.endswith(("_api_key", "_api_token", "_secret", "_token"))


def _redact_credential_query(url):
    """Redact credential-bearing URL query strings.

    Args:
        url: Required. URL.

    Returns:
        A URL with credential query values removed when needed.
    """
    parsed = urlsplit(url)
    if not parsed.query:
        return url

    if parsed.username or parsed.password:
        netloc = parsed.hostname or ""
        if parsed.port:
            netloc = f"{netloc}:{parsed.port}"
        return urlunsplit((parsed.scheme, netloc, parsed.path, "redacted=true", ""))

    query = parse_qsl(parsed.query, keep_blank_values=True)
    if not any(_is_sensitive_query_key(key) for key, _value in query):
        return url

    redacted = urlencode({"redacted": "true"})
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, redacted, ""))


def _is_sensitive_query_key(key):
    """Return whether a query key carries credentials or signed URL data.

    Args:
        key: Required. Query string key.

    Returns:
        True when the key should be redacted.
    """
    normalized = str(key).strip().lower()
    dashed = normalized.replace("_", "-")
    compact = normalized.replace("_", "").replace("-", "")
    if (
        normalized in SECRET_QUERY_NAMES
        or dashed in SECRET_QUERY_NAMES
        or compact in SECRET_QUERY_COMPACT_NAMES
    ):
        return True
    return any(
        marker in normalized
        for marker in ("signature", "token", "credential", "secret")
    )
