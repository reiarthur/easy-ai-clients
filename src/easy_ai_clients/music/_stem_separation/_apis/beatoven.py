from ..._common import operation_utils as _ops

PROVIDER = "beatoven"
ENV_NAME = "BEATOVEN_API_KEY"
DEFAULT_MODEL = "maestro"
STATUS_ENDPOINT_PATH = "/api/v1/tasks/{task_id}"


def separate_stems(audio, output_path=None, sync=True, **kwargs):
    """Get Beatoven stems from a task result or submit a stem request.

    Args:
        audio: Required. Beatoven task ID, or audio input when `endpoint` is
            supplied for a provider-native stem request.
        output_path: Optional. Destination path for `stems_url`.
        sync: Optional. Poll status when a task ID is available.
        **kwargs: Optional. Provider-native fields and local controls.

    Returns:
        A normalized result with `stems`.
    """
    model = _ops.resolve_model(kwargs, DEFAULT_MODEL)
    task_id = kwargs.get("task_id") or kwargs.get("taskId")

    if task_id or not kwargs.get("endpoint"):
        task_id = task_id or audio
        raw_response = _poll_or_status(task_id, sync=sync, **kwargs)
    else:
        payload = _build_payload(audio, **kwargs)
        raw_response = _ops.post_json(
            kwargs["endpoint"],
            headers=_headers(kwargs),
            payload=payload,
            params=kwargs.get("params"),
            timeout=kwargs.get("timeout", 60),
            retries=kwargs.get("retries", 2),
            request_kwargs=kwargs.get("request_kwargs"),
        )
        task_id = _ops.result_utils.extract_request_id(raw_response)
        if sync and task_id:
            raw_response = _poll_or_status(task_id, sync=True, **kwargs)

    return _ops.result(
        PROVIDER,
        model,
        raw_response,
        output_path=output_path,
        cost=_cost(raw_response),
        metadata=_ops.provider_metadata(raw_response, audio, include_stems=True),
        stems=True,
        download_timeout=kwargs.get("download_timeout", 60),
    )


def get_generation_status(request_id, **kwargs):
    """Get Beatoven task status.

    Args:
        request_id: Required. Beatoven task ID.
        **kwargs: Optional. Requires `base_url` unless `status_endpoint` is full.

    Returns:
        A normalized result with `stems` when available.
    """
    raw_response = _request_status(request_id, **kwargs)
    return _ops.result(
        PROVIDER,
        _ops.resolve_model(kwargs, DEFAULT_MODEL),
        raw_response,
        cost=_cost(raw_response),
        metadata=_ops.provider_metadata(raw_response, include_stems=True),
        stems=True,
    )


def get_generation_result(request_id, output_path=None, **kwargs):
    """Get Beatoven task result.

    Args:
        request_id: Required. Beatoven task ID.
        output_path: Optional. Destination path for `stems_url`.
        **kwargs: Optional. Status endpoint controls.

    Returns:
        A normalized result with `stems`.
    """
    raw_response = _request_status(request_id, **kwargs)
    return _ops.result(
        PROVIDER,
        _ops.resolve_model(kwargs, DEFAULT_MODEL),
        raw_response,
        output_path=output_path,
        cost=_cost(raw_response),
        metadata=_ops.provider_metadata(raw_response, include_stems=True),
        stems=True,
        download_timeout=kwargs.get("download_timeout", 60),
    )


def download_generation(request_id, output_path=None, **kwargs):
    """Download Beatoven stems from a completed task.

    Args:
        request_id: Required. Beatoven task ID.
        output_path: Optional. Destination path.
        **kwargs: Optional. Status endpoint controls.

    Returns:
        A normalized result with `stems`.
    """
    return get_generation_result(request_id, output_path=output_path, **kwargs)


def _build_payload(audio, **kwargs):
    """Build a Beatoven stem request payload.

    Args:
        audio: Required. Source audio.
        **kwargs: Optional. Provider-native fields.

    Returns:
        A provider payload dictionary.
    """
    payload = _ops.forwarded_payload(kwargs)
    payload.setdefault("model", _ops.resolve_model(kwargs, DEFAULT_MODEL))
    _ops.add_audio_input(payload, audio, url_key="audio_url", generic_key="audio")
    return payload


def _headers(kwargs):
    """Build Beatoven headers.

    Args:
        kwargs: Required. Local controls.

    Returns:
        Request headers.
    """
    headers = _ops.bearer_headers(PROVIDER, ENV_NAME)
    return _ops.merge_headers(headers, kwargs.get("headers"))


def _poll_or_status(task_id, sync=True, **kwargs):
    """Return Beatoven task status or poll until composed.

    Args:
        task_id: Required. Beatoven task ID.
        sync: Optional. Whether to poll.
        **kwargs: Optional. Local request controls.

    Returns:
        Raw provider response.
    """
    if not sync:
        return _request_status(task_id, **kwargs)
    return _ops.poll_status(
        task_id,
        lambda value: _request_status(value, **kwargs),
        None,
        interval=kwargs.get("poll_interval", 5),
        timeout=kwargs.get("poll_timeout", 300),
    )


def _request_status(task_id, **kwargs):
    """Request raw Beatoven task status.

    Args:
        task_id: Required. Beatoven task ID.
        **kwargs: Optional. Local request controls.

    Returns:
        Raw provider response.
    """
    path = kwargs.get("status_endpoint_path") or STATUS_ENDPOINT_PATH.format(
        task_id=task_id
    )
    endpoint = _ops.resolve_endpoint(
        {"endpoint": kwargs.get("status_endpoint"), "base_url": kwargs.get("base_url")},
        path=path,
    )
    return _ops.get_json(
        endpoint,
        headers=_headers(kwargs),
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
        request_kwargs=kwargs.get("request_kwargs"),
    )


def _cost(raw_response=None, payload=None):
    """Return Beatoven cost metadata.

    Args:
        raw_response: Optional. Provider response.
        payload: Optional. Request payload.

    Returns:
        Normalized cost metadata.
    """
    return _ops.unavailable_cost(
        {"reason": "Beatoven cost depends on downloaded minutes and plan."}
    )
