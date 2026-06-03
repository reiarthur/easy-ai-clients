from ..._common import operation_utils as _ops

PROVIDER = "falai"
ENV_NAME = "FAL_KEY"
DEFAULT_MODEL = None
QUEUE_BASE_URL = "https://queue.fal.run"


def edit_music(audio, prompt=None, output_path=None, sync=True, **kwargs):
    """Run a fal.ai music edit model through the queue API.

    Args:
        audio: Required. Source audio or reference audio.
        prompt: Optional. Edit, inpaint, or outpaint prompt.
        output_path: Optional. Destination path for a final URL.
        sync: Optional. Accepted for dispatcher consistency.
        **kwargs: Optional. Provider-native model fields.

    Returns:
        A normalized music result.
    """
    model = _model_id(kwargs)
    payload = _build_payload(audio, prompt=prompt, **kwargs)
    endpoint = kwargs.get("endpoint") or f"{QUEUE_BASE_URL}/{model}"
    raw_response = _ops.post_json(
        endpoint,
        headers=_headers(kwargs),
        payload=payload,
        params=kwargs.get("params"),
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
        request_kwargs=kwargs.get("request_kwargs"),
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
            extra={"edit_flow": "fal_queue_model", "model_id": model},
        ),
        download_timeout=kwargs.get("download_timeout", 60),
    )


def get_generation_status(request_id, **kwargs):
    """Get fal.ai status using a caller-supplied status endpoint.

    Args:
        request_id: Required. fal.ai request ID.
        **kwargs: Optional. Must include `status_endpoint`.

    Returns:
        A normalized music result.
    """
    endpoint = _ops.resolve_endpoint({"endpoint": kwargs.get("status_endpoint")})
    raw_response = _ops.get_json(
        endpoint,
        headers=_headers(kwargs),
        params=kwargs.get("params") or {"request_id": request_id},
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
        request_kwargs=kwargs.get("request_kwargs"),
    )
    return _ops.result(PROVIDER, _model_id(kwargs, required=False), raw_response, cost=_cost(raw_response))


def get_generation_result(request_id, output_path=None, **kwargs):
    """Get fal.ai result using a caller-supplied result endpoint.

    Args:
        request_id: Required. fal.ai request ID.
        output_path: Optional. Destination path.
        **kwargs: Optional. Must include `result_endpoint`.

    Returns:
        A normalized music result.
    """
    endpoint = _ops.resolve_endpoint({"endpoint": kwargs.get("result_endpoint")})
    raw_response = _ops.get_json(
        endpoint,
        headers=_headers(kwargs),
        params=kwargs.get("params") or {"request_id": request_id},
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
        request_kwargs=kwargs.get("request_kwargs"),
    )
    return _ops.result(
        PROVIDER,
        _model_id(kwargs, required=False),
        raw_response,
        output_path=output_path,
        cost=_cost(raw_response),
        download_timeout=kwargs.get("download_timeout", 60),
    )


def download_generation(request_id, output_path=None, **kwargs):
    """Download a completed fal.ai result.

    Args:
        request_id: Required. fal.ai request ID.
        output_path: Optional. Destination path.
        **kwargs: Optional. Result endpoint controls.

    Returns:
        A normalized music result.
    """
    return get_generation_result(request_id, output_path=output_path, **kwargs)


def _build_payload(audio, prompt=None, **kwargs):
    """Build the fal.ai edit payload.

    Args:
        audio: Required. Source or reference audio.
        prompt: Optional. Edit prompt.
        **kwargs: Optional. Provider-native model fields.

    Returns:
        A provider payload dictionary.
    """
    payload = _ops.forwarded_payload(kwargs, exclude=("model", "model_id"))
    _ops.add_prompt(payload, prompt)
    _ops.add_audio_input(payload, audio, url_key="reference_audio", generic_key="audio")
    return payload


def _headers(kwargs):
    """Build fal.ai headers.

    Args:
        kwargs: Required. Local controls.

    Returns:
        Request headers.
    """
    headers = _ops.bearer_headers(PROVIDER, ENV_NAME, scheme="Key")
    return _ops.merge_headers(headers, kwargs.get("headers"))


def _model_id(kwargs, required=True):
    """Return the fal.ai model ID.

    Args:
        kwargs: Required. Provider keyword arguments.
        required: Optional. Whether missing model should raise.

    Returns:
        A model ID or None.
    """
    model = kwargs.get("model_id") or kwargs.get("model") or DEFAULT_MODEL
    if required and not model:
        raise RuntimeError("model or model_id is required for fal.ai music edit.")
    return model


def _cost(raw_response=None, payload=None):
    """Return fal.ai cost metadata.

    Args:
        raw_response: Optional. Provider response.
        payload: Optional. Request payload.

    Returns:
        Normalized cost metadata.
    """
    return _ops.unavailable_cost(
        {"reason": "fal.ai music cost is model-specific and not universal."}
    )
