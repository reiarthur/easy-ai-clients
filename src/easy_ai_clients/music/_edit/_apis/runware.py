from ..._common import cost_utils
from ..._common import operation_utils as _ops

PROVIDER = "runware"
ENV_NAME = "RUNWARE_API_KEY"
DEFAULT_MODEL = "runware:ace-step@v1.5-turbo"


def edit_music(audio, prompt=None, output_path=None, sync=True, **kwargs):
    """Run a Runware ACE-Step repaint/edit task.

    Args:
        audio: Required. Source audio URL, UUID, data URI, bytes, or path.
        prompt: Optional. Positive prompt for the edit.
        output_path: Optional. Destination path for a final URL.
        sync: Optional. Accepted for dispatcher consistency.
        **kwargs: Optional. Provider-native Runware task fields.

    Returns:
        A normalized music result.
    """
    model = _ops.resolve_model(kwargs, DEFAULT_MODEL)
    payload = _build_payload(audio, prompt=prompt, **kwargs)
    endpoint = _ops.resolve_endpoint(kwargs)
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
            extra={"edit_flow": "ace_step_repaint"},
        ),
        download_timeout=kwargs.get("download_timeout", 60),
    )


def get_generation_status(request_id, **kwargs):
    """Get Runware task status using a caller-supplied status endpoint.

    Args:
        request_id: Required. Runware task UUID.
        **kwargs: Optional. Must include `status_endpoint`.

    Returns:
        A normalized music result.
    """
    endpoint = _ops.resolve_endpoint({"endpoint": kwargs.get("status_endpoint")})
    raw_response = _ops.post_json(
        endpoint,
        headers=_headers(kwargs),
        payload={"taskUUID": request_id},
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
        request_kwargs=kwargs.get("request_kwargs"),
    )
    return _ops.result(PROVIDER, _ops.resolve_model(kwargs, DEFAULT_MODEL), raw_response, cost=_cost(raw_response))


def get_generation_result(request_id, output_path=None, **kwargs):
    """Get Runware task result using a caller-supplied result endpoint.

    Args:
        request_id: Required. Runware task UUID.
        output_path: Optional. Destination path.
        **kwargs: Optional. Must include `result_endpoint`.

    Returns:
        A normalized music result.
    """
    endpoint = _ops.resolve_endpoint({"endpoint": kwargs.get("result_endpoint")})
    raw_response = _ops.post_json(
        endpoint,
        headers=_headers(kwargs),
        payload={"taskUUID": request_id},
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
        request_kwargs=kwargs.get("request_kwargs"),
    )
    return _ops.result(
        PROVIDER,
        _ops.resolve_model(kwargs, DEFAULT_MODEL),
        raw_response,
        output_path=output_path,
        cost=_cost(raw_response),
        download_timeout=kwargs.get("download_timeout", 60),
    )


def download_generation(request_id, output_path=None, **kwargs):
    """Download a completed Runware task result.

    Args:
        request_id: Required. Runware task UUID.
        output_path: Optional. Destination path.
        **kwargs: Optional. Result endpoint controls.

    Returns:
        A normalized music result.
    """
    return get_generation_result(request_id, output_path=output_path, **kwargs)


def _build_payload(audio, prompt=None, **kwargs):
    """Build the Runware audio inference payload.

    Args:
        audio: Required. Input audio for repaint/edit.
        prompt: Optional. Positive prompt.
        **kwargs: Optional. Provider-native Runware task fields.

    Returns:
        A provider payload dictionary.
    """
    payload = _ops.forwarded_payload(kwargs, exclude=("model", "model_id"))
    payload.setdefault("taskType", "audioInference")
    payload.setdefault("taskUUID", _ops.make_task_uuid(kwargs.get("taskUUID")))
    payload.setdefault("model", _ops.resolve_model(kwargs, DEFAULT_MODEL))
    payload.setdefault("outputType", "URL")
    if prompt is not None:
        payload.setdefault("positivePrompt", prompt)
    inputs = dict(payload.get("inputs") or {})
    if "audio" not in inputs:
        audio_holder = {}
        _ops.add_audio_input(audio_holder, audio, url_key="audio", generic_key="audio")
        inputs["audio"] = audio_holder.get("audio")
    payload["inputs"] = inputs
    return payload


def _headers(kwargs):
    """Build Runware headers.

    Args:
        kwargs: Required. Local controls.

    Returns:
        Request headers.
    """
    headers = _ops.bearer_headers(PROVIDER, ENV_NAME)
    return _ops.merge_headers(headers, kwargs.get("headers"))


def _cost(raw_response=None, payload=None):
    """Return Runware cost metadata.

    Args:
        raw_response: Optional. Provider response.
        payload: Optional. Request payload.

    Returns:
        Normalized cost metadata.
    """
    response_cost = cost_utils.cost_from_response(raw_response)
    if cost_utils.has_available_cost(response_cost):
        return response_cost

    payload = payload or {}
    return _ops.unavailable_cost(
        {"reason": "Runware cost requires a returned provider cost field."}
    )


def update_cost(result, **kwargs):
    """Refresh Runware edit cost metadata from response or documented pricing.

    Args:
        result: Required. Normalized result dictionary.
        **kwargs: Optional. Ignored except for dispatcher compatibility.

    Returns:
        The updated result dictionary.
    """
    raw_response = result.get("raw_response") if isinstance(result, dict) else result
    details = result.get("cost_details") if isinstance(result, dict) else {}
    cost = _cost(raw_response, details)
    return cost_utils.apply_cost_metadata(result, cost)
