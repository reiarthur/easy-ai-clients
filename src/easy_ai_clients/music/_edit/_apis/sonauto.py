from ..._common import operation_utils as _ops

PROVIDER = "sonauto"
ENV_NAME = "SONAUTO_API_KEY"
DEFAULT_MODEL = "v3"
BASE_URL = "https://api.sonauto.ai/v1"
EDIT_ENDPOINT_PATH = "/generations/v3/extend"
STATUS_ENDPOINT_PATH = "/generations/status/{request_id}"
RESULT_ENDPOINT_PATH = "/generations/{request_id}"


def edit_music(audio, prompt=None, output_path=None, sync=True, **kwargs):
    """Extend or inpaint music with Sonauto.

    Args:
        audio: Required. Source audio URL, data URI, bytes, or local path.
        prompt: Optional. Edit or continuation prompt.
        output_path: Optional. Destination path for a final URL.
        sync: Optional. Poll when a task ID is returned.
        **kwargs: Optional. Provider-native edit fields.

    Returns:
        A normalized music result.
    """
    model = _ops.resolve_model(kwargs, DEFAULT_MODEL)
    payload = _build_payload(audio, prompt=prompt, **kwargs)
    headers = _headers(kwargs)
    endpoint = _ops.resolve_endpoint(
        kwargs,
        base_url=BASE_URL,
        path=EDIT_ENDPOINT_PATH,
    )
    raw_response = _ops.post_json(
        endpoint,
        headers=headers,
        payload=payload,
        params=kwargs.get("params"),
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
        request_kwargs=kwargs.get("request_kwargs"),
    )
    request_id = _ops.result_utils.extract_request_id(raw_response)
    if sync and request_id:
        raw_response = _ops.poll_status(
            request_id,
            lambda value: _request_status(value, **kwargs),
            lambda value: _request_result(value, **kwargs),
            interval=kwargs.get("poll_interval", 5),
            timeout=kwargs.get("poll_timeout", 300),
        )
    return _ops.result(
        PROVIDER,
        model,
        raw_response,
        output_path=output_path,
        cost=_cost(raw_response, payload),
        metadata=_ops.provider_metadata(
            raw_response,
            audio,
            extra={"edit_flow": "extend_or_inpaint"},
        ),
        download_timeout=kwargs.get("download_timeout", 60),
    )


def get_generation_status(request_id, **kwargs):
    """Get Sonauto generation status.

    Args:
        request_id: Required. Sonauto task ID.
        **kwargs: Optional. Local request controls.

    Returns:
        A normalized music result.
    """
    raw_response = _request_status(request_id, **kwargs)
    return _ops.result(
        PROVIDER,
        _ops.resolve_model(kwargs, DEFAULT_MODEL),
        raw_response,
        cost=_cost(raw_response),
    )


def get_generation_result(request_id, output_path=None, **kwargs):
    """Get a completed Sonauto generation result.

    Args:
        request_id: Required. Sonauto task ID.
        output_path: Optional. Destination path for a final URL.
        **kwargs: Optional. Local request controls.

    Returns:
        A normalized music result.
    """
    raw_response = _request_result(request_id, **kwargs)
    return _ops.result(
        PROVIDER,
        _ops.resolve_model(kwargs, DEFAULT_MODEL),
        raw_response,
        output_path=output_path,
        cost=_cost(raw_response),
        download_timeout=kwargs.get("download_timeout", 60),
    )


def download_generation(request_id, output_path=None, **kwargs):
    """Download a completed Sonauto generation result.

    Args:
        request_id: Required. Sonauto task ID.
        output_path: Optional. Destination path.
        **kwargs: Optional. Local request controls.

    Returns:
        A normalized music result.
    """
    return get_generation_result(request_id, output_path=output_path, **kwargs)


def _build_payload(audio, prompt=None, **kwargs):
    """Build the Sonauto edit payload.

    Args:
        audio: Required. Source audio.
        prompt: Optional. Prompt.
        **kwargs: Optional. Provider-native payload fields.

    Returns:
        A provider payload dictionary.
    """
    payload = _ops.forwarded_payload(kwargs)
    _ops.add_prompt(payload, prompt)
    _ops.add_audio_input(payload, audio, url_key="audio_url", base64_key="audio_base64")
    return payload


def _headers(kwargs):
    """Build Sonauto headers.

    Args:
        kwargs: Required. Local controls.

    Returns:
        Request headers.
    """
    headers = _ops.bearer_headers(PROVIDER, ENV_NAME)
    return _ops.merge_headers(headers, kwargs.get("headers"))


def _request_status(request_id, **kwargs):
    """Request raw Sonauto status.

    Args:
        request_id: Required. Sonauto task ID.
        **kwargs: Optional. Local request controls.

    Returns:
        Raw provider response.
    """
    path = kwargs.get("status_endpoint_path") or STATUS_ENDPOINT_PATH.format(
        request_id=request_id
    )
    url = _ops.resolve_endpoint(
        {"endpoint": kwargs.get("status_endpoint"), "base_url": kwargs.get("base_url")},
        base_url=BASE_URL,
        path=path,
    )
    return _ops.get_json(
        url,
        headers=_headers(kwargs),
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
        request_kwargs=kwargs.get("request_kwargs"),
    )


def _request_result(request_id, **kwargs):
    """Request raw Sonauto result.

    Args:
        request_id: Required. Sonauto task ID.
        **kwargs: Optional. Local request controls.

    Returns:
        Raw provider response.
    """
    path = kwargs.get("result_endpoint_path") or RESULT_ENDPOINT_PATH.format(
        request_id=request_id
    )
    url = _ops.resolve_endpoint(
        {"endpoint": kwargs.get("result_endpoint"), "base_url": kwargs.get("base_url")},
        base_url=BASE_URL,
        path=path,
    )
    return _ops.get_json(
        url,
        headers=_headers(kwargs),
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
        request_kwargs=kwargs.get("request_kwargs"),
    )


def _cost(raw_response=None, payload=None):
    """Return Sonauto cost metadata.

    Args:
        raw_response: Optional. Provider response.
        payload: Optional. Request payload.

    Returns:
        Normalized cost metadata.
    """
    return _ops.unavailable_cost(
        {"reason": "The edit-specific credit cost is not exposed in the response."}
    )
