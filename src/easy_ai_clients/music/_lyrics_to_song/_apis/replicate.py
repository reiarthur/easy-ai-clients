from ..._common import cost_utils, provider_api, result_utils

PROVIDER = "replicate"
ENV_NAME = "REPLICATE_API_TOKEN"
DEFAULT_MODEL = "minimax/music-2.6"
PREDICTIONS_ENDPOINT = "https://api.replicate.com/v1/predictions"
MODEL_ENDPOINT = "https://api.replicate.com/v1/models/{model}/predictions"
STATUS_ENDPOINT = "https://api.replicate.com/v1/predictions/{request_id}"


def generate_lyrics_to_song(lyrics, prompt=None, output_path=None, sync=True, **kwargs):
    """Generate a song from lyrics with Replicate.

    Args:
        lyrics: Required. Lyrics or structured song text.
        prompt: Optional. Model prompt.
        output_path: Optional. Local destination for completed audio.
        sync: Optional. When false, return after prediction creation.
        **kwargs: Optional. Replicate prediction fields.

    Returns:
        A provider response dictionary.
    """
    kwargs = provider_api.copy_kwargs(kwargs)
    timeout = provider_api.pop_value(kwargs, "timeout", default=60)
    poll_interval = provider_api.pop_value(kwargs, "poll_interval", default=None)
    max_poll_attempts = provider_api.pop_value(kwargs, "max_poll_attempts", default=None)
    model = provider_api.pop_value(kwargs, "model", default=DEFAULT_MODEL)
    version = provider_api.pop_value(kwargs, "version", default=None)
    endpoint = provider_api.pop_value(
        kwargs,
        "endpoint",
        default=PREDICTIONS_ENDPOINT if version else MODEL_ENDPOINT.format(model=model),
    )
    payload = _build_payload(lyrics, prompt=prompt, model=model, version=version, **kwargs)
    response = provider_api.request_json(
        "POST",
        endpoint,
        headers=_headers(),
        payload=payload,
        timeout=timeout,
    )
    response["model"] = model
    cost_utils.apply_cost_metadata(response, _cost(model, payload))

    request_id = result_utils.extract_request_id(response)
    if not sync or not request_id:
        response.setdefault("status", "submitted")
        return response

    return provider_api.poll_result(
        get_generation_status,
        request_id,
        output_path=output_path,
        poll_interval=poll_interval,
        max_poll_attempts=max_poll_attempts,
    )


def get_generation_status(request_id, **kwargs):
    """Return Replicate prediction status.

    Args:
        request_id: Required. Replicate prediction ID.
        **kwargs: Optional. Provider request options.

    Returns:
        A provider status dictionary.
    """
    timeout = provider_api.pop_value(kwargs, "timeout", default=60)
    endpoint = provider_api.pop_value(
        kwargs,
        "status_endpoint",
        default=STATUS_ENDPOINT.format(request_id=request_id),
    )
    response = provider_api.request_json("GET", endpoint, headers=_headers(), timeout=timeout)
    response.setdefault("request_id", request_id)
    cost_utils.apply_cost_metadata(response, _cost(kwargs.get("model") or DEFAULT_MODEL, response))
    return response


def get_generation_result(request_id, output_path=None, **kwargs):
    """Return a Replicate prediction result.

    Args:
        request_id: Required. Replicate prediction ID.
        output_path: Optional. Local destination path.
        **kwargs: Optional. Provider request options.

    Returns:
        A provider result dictionary.
    """
    response = get_generation_status(request_id, **kwargs)
    timeout = provider_api.pop_value(kwargs, "timeout", default=60)
    return provider_api.save_audio_from_response(response, output_path, timeout=timeout)


download_generation = get_generation_result


def _build_payload(lyrics, prompt=None, model=None, version=None, **kwargs):
    """Build a Replicate prediction payload.

    Args:
        lyrics: Required. Lyrics or structured song text.
        prompt: Optional. Model prompt.
        model: Optional. Replicate model identifier.
        version: Optional. Replicate model version hash.
        **kwargs: Optional. Prediction fields.

    Returns:
        A JSON payload dictionary.
    """
    provider_api.reject_duplicates(kwargs, "lyrics")
    input_payload = provider_api.pop_value(kwargs, "input", default={})
    input_payload = dict(input_payload)
    if "lyrics" in input_payload:
        raise ValueError("Use the public lyrics argument instead of input['lyrics'].")
    input_payload.setdefault("lyrics", lyrics)
    if prompt is not None:
        input_payload.setdefault("prompt", prompt)

    payload = {"input": input_payload}
    if version is not None:
        payload["version"] = version
    for key in ("webhook", "webhook_events_filter"):
        value = provider_api.pop_value(kwargs, key, default=None)
        if value is not None:
            payload[key] = value
    return provider_api.merge_kwargs(payload, kwargs)


def _headers():
    """Return Replicate headers.

    Returns:
        A headers dictionary.
    """
    return provider_api.auth_headers(
        PROVIDER,
        ENV_NAME,
        scheme="bearer",
        extra={"Content-Type": "application/json"},
    )


def _cost(model=None, payload=None):
    """Return Replicate cost metadata when present in provider data.

    Args:
        model: Optional. Replicate model identifier.
        payload: Optional. Request payload or response.

    Returns:
        Normalized cost metadata.
    """
    payload = payload or {}
    response_cost = cost_utils.cost_from_response(payload)
    if cost_utils.has_available_cost(response_cost):
        return response_cost
    return cost_utils.unavailable_cost_metadata(details={"model": model})


def update_cost(result, **kwargs):
    """Refresh Replicate cost metadata from documented output pricing.

    Args:
        result: Required. Normalized result dictionary.
        **kwargs: Optional. Dispatcher compatibility values.

    Returns:
        The updated result dictionary.
    """
    model = result.get("model") if isinstance(result, dict) else None
    details = result.get("cost_details") if isinstance(result, dict) else {}
    cost = _cost(model or DEFAULT_MODEL, details or {})
    return cost_utils.apply_cost_metadata(result, cost)
