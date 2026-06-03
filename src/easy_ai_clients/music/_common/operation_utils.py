import base64
import time
import uuid
from pathlib import Path

from . import cost_utils, env_utils, http_utils, media_utils, result_utils

CONTROL_KWARGS = {
    "api_url",
    "auth",
    "base_url",
    "download_timeout",
    "endpoint",
    "endpoint_path",
    "headers",
    "method",
    "output_path",
    "params",
    "poll_interval",
    "poll_timeout",
    "request_kwargs",
    "result_endpoint",
    "result_endpoint_path",
    "retries",
    "status_endpoint",
    "status_endpoint_path",
    "sync",
    "timeout",
    "url",
}

COMPLETED_STATUSES = {
    "completed",
    "complete",
    "composed",
    "generated",
    "succeeded",
    "success",
    "successful",
    "done",
    "finished",
}

FAILED_STATUSES = {
    "canceled",
    "cancelled",
    "error",
    "failed",
    "failure",
    "rejected",
}


def forwarded_payload(kwargs, exclude=None):
    """Return provider kwargs that should be forwarded in the request payload.

    Args:
        kwargs: Required. Provider keyword arguments.
        exclude: Optional. Extra keys to exclude.

    Returns:
        A payload dictionary without local control keys or None values.
    """
    excluded = set(CONTROL_KWARGS)
    excluded.update(exclude or ())
    return {
        key: value
        for key, value in dict(kwargs or {}).items()
        if key not in excluded and value is not None
    }


def resolve_model(kwargs, default_model=None):
    """Return the requested provider model or a documented default.

    Args:
        kwargs: Required. Provider keyword arguments.
        default_model: Optional. Default model.

    Returns:
        A model value or None.
    """
    return kwargs.get("model") or kwargs.get("model_id") or default_model


def add_prompt(payload, prompt=None):
    """Add prompt to a payload when supplied.

    Args:
        payload: Required. Payload dictionary.
        prompt: Optional. Prompt text.

    Returns:
        The updated payload.
    """
    if prompt is not None and "prompt" not in payload:
        payload["prompt"] = prompt
    return payload


def add_audio_input(payload, audio, url_key="audio_url", base64_key="audio_base64",
                    data_uri_key=None, bytes_key=None, path_key=None,
                    generic_key="audio"):
    """Add an audio input using URL, base64, data URI, bytes, path, or generic field.

    Args:
        payload: Required. Payload dictionary.
        audio: Required. Audio input.
        url_key: Optional. Payload key for remote URLs.
        base64_key: Optional. Payload key for local bytes encoded as base64.
        data_uri_key: Optional. Payload key for data URI values.
        bytes_key: Optional. Payload key for raw bytes.
        path_key: Optional. Payload key for local paths.
        generic_key: Optional. Fallback key.

    Returns:
        The updated payload.
    """
    keys = (url_key, base64_key, data_uri_key, bytes_key, path_key, generic_key)
    if any(key and key in payload for key in keys):
        return payload

    if media_utils.is_remote_url(audio) and url_key:
        payload[url_key] = audio
    elif media_utils.is_data_uri(audio) and data_uri_key:
        payload[data_uri_key] = audio
    elif media_utils.is_data_uri(audio) and base64_key:
        payload[base64_key] = strip_data_uri(audio)
    elif media_utils.is_bytes_like(audio) and bytes_key:
        payload[bytes_key] = bytes(audio)
    elif media_utils.is_bytes_like(audio) and base64_key:
        payload[base64_key] = base64.b64encode(bytes(audio)).decode("ascii")
    elif media_utils.is_local_path(audio) and path_key:
        payload[path_key] = str(audio)
    elif media_utils.is_local_path(audio) and base64_key:
        data = media_utils.read_media_bytes(audio)
        payload[base64_key] = base64.b64encode(data).decode("ascii")
    elif generic_key:
        payload[generic_key] = audio

    return payload


def strip_data_uri(value):
    """Return the base64 body from a data URI.

    Args:
        value: Required. Data URI or other value.

    Returns:
        The data URI body when present, otherwise the original value.
    """
    if media_utils.is_data_uri(value) and "," in value:
        return value.split(",", 1)[1]
    return value


def input_metadata(audio=None, extra=None):
    """Return non-sensitive input metadata for provider metadata.

    Args:
        audio: Optional. Audio input.
        extra: Optional. Extra metadata.

    Returns:
        A metadata dictionary.
    """
    metadata = {}
    if audio is not None:
        metadata["input_audio"] = media_utils.describe_media(audio)
    if extra:
        metadata.update(extra)
    return metadata


def bearer_headers(provider, env_name, scheme="Bearer", header_name="Authorization",
                   extra=None):
    """Build authentication headers from an environment variable.

    Args:
        provider: Required. Provider identifier.
        env_name: Required. Environment variable name.
        scheme: Optional. Authorization scheme. Use None for raw header value.
        header_name: Optional. Header name.
        extra: Optional. Extra headers.

    Returns:
        A headers dictionary.
    """
    token = env_utils.require_env_var(env_name)
    value = token if scheme is None else f"{scheme} {token}"
    headers = {header_name: value}
    if extra:
        headers.update(extra)
    return headers


def basic_auth(provider):
    """Return requests-compatible Basic Auth credentials for a provider.

    Args:
        provider: Required. Provider identifier.

    Returns:
        A tuple with key and secret.
    """
    values = env_utils.require_env_vars(provider)
    names = env_utils.env_var_names(provider)
    return values[names[0]], values[names[1]]


def merge_headers(default_headers, extra_headers=None):
    """Merge default and caller-supplied headers.

    Args:
        default_headers: Required. Default headers.
        extra_headers: Optional. Extra headers.

    Returns:
        A headers dictionary.
    """
    headers = dict(default_headers or {})
    if extra_headers:
        headers.update(extra_headers)
    return headers


def make_task_uuid(value=None):
    """Return an existing task UUID or create a new one.

    Args:
        value: Optional. Existing UUID.

    Returns:
        A UUID string.
    """
    return value or str(uuid.uuid4())


def join_url(base_url=None, path=None):
    """Join a base URL and endpoint path without inventing either value.

    Args:
        base_url: Optional. Base URL.
        path: Optional. Endpoint path or full URL.

    Returns:
        A full URL.

    Raises:
        RuntimeError: If only a relative path is available.
    """
    if path and media_utils.is_remote_url(path):
        return path
    if base_url and path:
        return f"{base_url.rstrip('/')}/{str(path).lstrip('/')}"
    if base_url and not path:
        return base_url
    if path:
        raise RuntimeError("base_url is required when endpoint path is relative.")
    raise RuntimeError("endpoint is required for this provider flow.")


def resolve_endpoint(kwargs, default_endpoint=None, base_url=None, path=None):
    """Resolve the endpoint from kwargs or documented defaults.

    Args:
        kwargs: Required. Provider keyword arguments.
        default_endpoint: Optional. Full default endpoint.
        base_url: Optional. Documented base URL.
        path: Optional. Documented endpoint path.

    Returns:
        A full URL.
    """
    endpoint = kwargs.get("endpoint") or kwargs.get("api_url") or kwargs.get("url")
    if endpoint:
        return endpoint

    endpoint_path = kwargs.get("endpoint_path") or path
    endpoint_base = kwargs.get("base_url") or base_url
    if default_endpoint:
        return join_url(path=default_endpoint)
    return join_url(endpoint_base, endpoint_path)


def request_json_or_content(method, url, headers=None, params=None, json=None,
                            data=None, files=None, auth=None, timeout=60,
                            retries=2, request_kwargs=None):
    """Send an HTTP request and return JSON or binary content.

    Args:
        method: Required. HTTP method.
        url: Required. Endpoint URL.
        headers: Optional. Request headers.
        params: Optional. Query parameters.
        json: Optional. JSON body.
        data: Optional. Form body.
        files: Optional. Multipart files.
        auth: Optional. Requests auth value.
        timeout: Optional. Request timeout.
        retries: Optional. Retry count.
        request_kwargs: Optional. Extra requests kwargs.

    Returns:
        Parsed JSON when available, otherwise response bytes.
    """
    kwargs = dict(request_kwargs or {})
    response = http_utils.request(
        method,
        url,
        headers=headers,
        params=params,
        json=json,
        data=data,
        files=files,
        auth=auth,
        timeout=timeout,
        retries=retries,
        **kwargs,
    )
    content_type = response.headers.get("content-type", "").lower()
    if "json" in content_type:
        return http_utils.response_json(response)
    text = response.text.strip() if hasattr(response, "text") else ""
    if text.startswith("{") or text.startswith("["):
        return http_utils.response_json(response)
    return response.content


def get_json(url, headers=None, params=None, auth=None, timeout=60, retries=2,
             request_kwargs=None):
    """Send a GET request and return JSON or binary content.

    Args:
        url: Required. Endpoint URL.
        headers: Optional. Request headers.
        params: Optional. Query parameters.
        auth: Optional. Requests auth value.
        timeout: Optional. Request timeout.
        retries: Optional. Retry count.
        request_kwargs: Optional. Extra requests kwargs.

    Returns:
        Parsed JSON when available, otherwise response bytes.
    """
    return request_json_or_content(
        "GET",
        url,
        headers=headers,
        params=params,
        auth=auth,
        timeout=timeout,
        retries=retries,
        request_kwargs=request_kwargs,
    )


def post_json(url, headers=None, payload=None, params=None, auth=None, timeout=60,
              retries=2, request_kwargs=None):
    """Send a JSON POST request.

    Args:
        url: Required. Endpoint URL.
        headers: Optional. Request headers.
        payload: Optional. JSON body.
        params: Optional. Query parameters.
        auth: Optional. Requests auth value.
        timeout: Optional. Request timeout.
        retries: Optional. Retry count.
        request_kwargs: Optional. Extra requests kwargs.

    Returns:
        Parsed JSON when available, otherwise response bytes.
    """
    return request_json_or_content(
        "POST",
        url,
        headers=headers,
        params=params,
        json=payload,
        auth=auth,
        timeout=timeout,
        retries=retries,
        request_kwargs=request_kwargs,
    )


def poll_status(request_id, status_getter, result_getter=None, interval=5,
                timeout=300):
    """Poll provider status until completion or timeout.

    Args:
        request_id: Required. Provider request ID.
        status_getter: Required. Callable that returns a status response.
        result_getter: Optional. Callable that returns a result response.
        interval: Optional. Poll interval in seconds.
        timeout: Optional. Maximum polling time in seconds.

    Returns:
        The final provider response.
    """
    deadline = time.time() + timeout
    last_response = None

    while time.time() <= deadline:
        last_response = status_getter(request_id)
        status = result_utils.extract_status(last_response)
        normalized = str(status).strip().lower() if status is not None else ""
        if normalized in COMPLETED_STATUSES:
            if result_getter:
                return result_getter(request_id)
            return last_response
        if normalized in FAILED_STATUSES:
            return last_response
        time.sleep(interval)

    return last_response or {"request_id": request_id, "status": "submitted"}


def maybe_download(raw_response, output_path=None, timeout=60, prefer_stems=False):
    """Download a final audio URL or save direct audio bytes when requested.

    Args:
        raw_response: Required. Provider response.
        output_path: Optional. Destination path.
        timeout: Optional. Download timeout.
        prefer_stems: Optional. Prefer stem ZIP URLs over general audio URLs.

    Returns:
        The saved path, or None.
    """
    if not output_path:
        return None

    audio_url = None
    if prefer_stems:
        audio_url = _find_url_by_keys(
            raw_response,
            ("stems_url", "stemsUrl", "stem_url", "stemUrl", "zip_url", "zipUrl"),
        )
    audio_url = audio_url or result_utils.extract_audio_url(raw_response)
    if audio_url:
        return media_utils.download_url(audio_url, output_path, timeout=timeout)

    if isinstance(raw_response, bytes | bytearray | memoryview):
        path = Path(output_path)
        if path.parent:
            path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(bytes(raw_response))
        return str(path)

    return None


def normalize_stems(raw_response):
    """Normalize stem artifacts from common provider response shapes.

    Args:
        raw_response: Required. Provider response.

    Returns:
        A normalized stems dictionary or None.
    """
    zip_url = _find_url_by_keys(
        raw_response,
        ("stems_url", "stemsUrl", "stem_url", "stemUrl", "zip_url", "zipUrl"),
    )
    stem_value = result_utils.extract_stems(raw_response)
    items = _stem_items(stem_value)
    grouped = _find_first(raw_response, ("grouped_files", "groupedFiles", "files"))

    stems = {}
    if zip_url:
        stems["zip_url"] = zip_url
    if items:
        stems["items"] = items
    if grouped is not None and grouped != stem_value:
        stems["groups"] = grouped

    if stems:
        return stems
    return stem_value


def provider_metadata(raw_response=None, audio=None, extra=None, include_stems=False):
    """Build provider metadata while preserving grouped stem artifacts.

    Args:
        raw_response: Optional. Provider response.
        audio: Optional. Input audio.
        extra: Optional. Extra metadata.
        include_stems: Optional. Whether to include stem artifacts.

    Returns:
        A metadata dictionary.
    """
    metadata = input_metadata(audio, extra=extra)
    if include_stems:
        artifacts = {}
        stems = result_utils.extract_stems(raw_response)
        zip_url = _find_url_by_keys(
            raw_response,
            ("stems_url", "stemsUrl", "stem_url", "stemUrl", "zip_url", "zipUrl"),
        )
        grouped = _find_first(raw_response, ("grouped_files", "groupedFiles", "files"))
        if zip_url:
            artifacts["zip_url"] = zip_url
        if stems is not None:
            artifacts["stems"] = stems
        if grouped is not None:
            artifacts["grouped_files"] = grouped
        if artifacts:
            metadata["stem_artifacts"] = artifacts
    return metadata or None


def result(provider, model, raw_response, output_path=None, cost=None,
           metadata=None, warnings=None, stems=False, download_timeout=60,
           operation=None):
    """Build a normalized provider result.

    Args:
        provider: Required. Provider identifier.
        model: Optional. Provider model.
        raw_response: Required. Original provider response.
        output_path: Optional. Destination path.
        cost: Optional. Cost metadata.
        metadata: Optional. Provider metadata.
        warnings: Optional. Warning strings.
        stems: Optional. Whether to normalize stems.
        download_timeout: Optional. Download timeout.
        operation: Optional. Public operation name.

    Returns:
        A normalized result dictionary.
    """
    saved_path = maybe_download(
        raw_response,
        output_path,
        timeout=download_timeout,
        prefer_stems=stems,
    )
    audio = bytes(raw_response) if isinstance(raw_response, bytes | bytearray | memoryview) else None
    cost = cost or cost_utils.unavailable_cost_metadata(source="unavailable")
    stem_output = normalize_stems(raw_response) if stems else None
    if stems and stem_output is None and saved_path:
        stem_output = {"zip_path": saved_path}
    if stems and stem_output is None and audio is not None:
        stem_output = {"zip_bytes": audio}

    return result_utils.normalized_result(
        provider=provider,
        operation=operation,
        model=model,
        status=result_utils.extract_status(raw_response),
        request_id=result_utils.extract_request_id(raw_response),
        audio_url=result_utils.extract_audio_url(raw_response),
        output_path=saved_path,
        audio=audio,
        stems=stem_output,
        cost_usd=cost["cost_usd"],
        cost_is_estimated=cost["cost_is_estimated"],
        cost_source=cost["cost_source"],
        cost_details=cost["cost_details"],
        provider_metadata=metadata,
        raw_response=raw_response,
        warnings=warnings,
    )


def unavailable_cost(details=None):
    """Return unavailable cost metadata.

    Args:
        details: Optional. Cost details.

    Returns:
        Normalized unavailable cost metadata.
    """
    return cost_utils.unavailable_cost_metadata(source="unavailable", details=details)


def _stem_items(value):
    """Return normalized individual stem items.

    Args:
        value: Required. Raw stem value.

    Returns:
        A list of stem item dictionaries.
    """
    items = []
    if isinstance(value, dict):
        for name, item in value.items():
            if isinstance(item, str) and media_utils.is_remote_url(item):
                items.append({"name": name, "url": item})
            elif isinstance(item, dict):
                url = result_utils.extract_audio_url(item)
                entry = dict(item)
                entry.setdefault("name", name)
                if url:
                    entry.setdefault("url", url)
                items.append(entry)
    elif isinstance(value, list | tuple):
        for item in value:
            if isinstance(item, str) and media_utils.is_remote_url(item):
                items.append({"url": item})
            elif isinstance(item, dict):
                entry = dict(item)
                url = result_utils.extract_audio_url(item)
                if url:
                    entry.setdefault("url", url)
                items.append(entry)
    return items


def _find_url_by_keys(value, keys):
    """Find a remote URL by key in nested response data.

    Args:
        value: Required. Response value.
        keys: Required. Candidate keys.

    Returns:
        A remote URL or None.
    """
    found = _find_first(value, keys)
    if isinstance(found, str) and media_utils.is_remote_url(found):
        return found
    return None


def _find_first(value, keys):
    """Find the first matching key in nested response data.

    Args:
        value: Required. Response value.
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
