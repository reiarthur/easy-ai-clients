from ..._common import cost_utils, provider_api, result_utils

PROVIDER = "runware"
ENV_NAME = "RUNWARE_API_KEY"
DEFAULT_MODEL = "minimax:music@2.6"
ENDPOINT = "https://api.runware.ai/v1"


def generate_lyrics_to_song(lyrics, prompt=None, output_path=None, sync=True, **kwargs):
    """Generate a song from lyrics with Runware music models.

    Args:
        lyrics: Required. Lyrics or structured song text.
        prompt: Optional. Positive prompt.
        output_path: Optional. Local destination for completed audio.
        sync: Optional. When false, submit as an async task.
        **kwargs: Optional. Runware audio inference fields.

    Returns:
        A provider response dictionary.
    """
    kwargs = provider_api.copy_kwargs(kwargs)
    timeout = provider_api.pop_value(kwargs, "timeout", default=60)
    model = provider_api.pop_value(kwargs, "model", default=DEFAULT_MODEL)
    endpoint = provider_api.pop_value(kwargs, "endpoint", default=ENDPOINT)
    payload = _build_payload(lyrics, prompt=prompt, model=model, sync=sync, **kwargs)
    response = provider_api.request_json(
        "POST",
        endpoint,
        headers=_headers(),
        payload=[payload],
        timeout=timeout,
    )
    response = _prepare_response(response, payload, model)
    cost = _cost(model, response)
    if not cost_utils.has_available_cost(cost):
        cost = _cost(model, payload)
    _apply_cost(response, cost)

    request_id = result_utils.extract_request_id(response)
    if not sync or payload.get("deliveryMethod") == "async" or not request_id:
        response.setdefault("status", "submitted")
        return response

    return provider_api.save_audio_from_response(response, output_path, timeout=timeout)


def get_generation_status(request_id, **kwargs):
    """Return Runware task status or result.

    Args:
        request_id: Required. Runware task UUID.
        **kwargs: Optional. Provider request options.

    Returns:
        A provider status dictionary.
    """
    timeout = provider_api.pop_value(kwargs, "timeout", default=60)
    endpoint = provider_api.pop_value(kwargs, "endpoint", default=ENDPOINT)
    payload = {"taskType": "getResponse", "taskUUID": request_id}
    response = provider_api.request_json(
        "POST",
        endpoint,
        headers=_headers(),
        payload=[payload],
        timeout=timeout,
    )
    response = _prepare_response(response, payload, kwargs.get("model"))
    _apply_cost(response, _cost(response.get("model"), response))
    response.setdefault("request_id", request_id)
    return response


def get_generation_result(request_id, output_path=None, **kwargs):
    """Return a Runware result.

    Args:
        request_id: Required. Runware task UUID.
        output_path: Optional. Local destination path.
        **kwargs: Optional. Provider request options.

    Returns:
        A provider result dictionary.
    """
    response = get_generation_status(request_id, **kwargs)
    timeout = provider_api.pop_value(kwargs, "timeout", default=60)
    return provider_api.save_audio_from_response(response, output_path, timeout=timeout)


download_generation = get_generation_result


def _build_payload(lyrics, prompt=None, model=None, sync=True, **kwargs):
    """Build a Runware audio inference payload.

    Args:
        lyrics: Required. Lyrics or structured song text.
        prompt: Optional. Positive prompt.
        model: Optional. Runware model identifier.
        sync: Optional. Whether caller requested synchronous behavior.
        **kwargs: Optional. Runware fields.

    Returns:
        A JSON task payload dictionary.
    """
    provider_api.reject_duplicates(kwargs, "lyrics")
    settings = provider_api.pop_value(kwargs, "settings", default={})
    settings = dict(settings)
    if settings.get("instrumental") is True:
        raise ValueError("Runware instrumental generation should not include lyrics.")
    if "lyrics" in settings:
        raise ValueError("Use the public lyrics argument instead of settings['lyrics'].")
    settings.setdefault("lyrics", lyrics)

    task_uuid = provider_api.pop_value(
        kwargs,
        "taskUUID",
        "task_uuid",
        default=provider_api.generated_task_uuid(),
    )
    positive_prompt = provider_api.pop_value(
        kwargs,
        "positivePrompt",
        "positive_prompt",
        default=prompt,
    )
    delivery_method = provider_api.pop_value(
        kwargs,
        "deliveryMethod",
        "delivery_method",
        default=None if sync else "async",
    )
    payload = {
        "taskType": "audioInference",
        "taskUUID": task_uuid,
        "model": model or DEFAULT_MODEL,
        "settings": settings,
    }
    provider_api.add_optional(
        payload,
        positivePrompt=positive_prompt,
        deliveryMethod=delivery_method,
    )
    return provider_api.merge_kwargs(payload, kwargs)


def _prepare_response(response, payload, model):
    """Normalize Runware list responses to a dictionary.

    Args:
        response: Required. Runware response.
        payload: Required. Submitted task payload.
        model: Optional. Provider model identifier.

    Returns:
        A provider response dictionary.
    """
    if isinstance(response, list) and response:
        response = response[0]
    elif isinstance(response, dict) and isinstance(response.get("data"), list) and response["data"]:
        response = response["data"][0]
    if not isinstance(response, dict):
        response = {"raw_response": response}
    response.setdefault("request_id", payload.get("taskUUID"))
    response.setdefault("model", model or payload.get("model"))
    return response


def _cost(model=None, payload=None):
    """Return Runware cost metadata when the provider response includes it.

    Args:
        model: Optional. Runware model identifier.
        payload: Optional. Provider response or task payload.

    Returns:
        Normalized cost metadata.
    """
    payload = payload or {}
    response_cost = cost_utils.cost_from_response(payload)
    if cost_utils.has_available_cost(response_cost):
        return response_cost

    return cost_utils.unavailable_cost_metadata(details={"model": model})


def _apply_cost(response, cost):
    """Attach cost metadata to a provider response when available.

    Args:
        response: Required. Provider response dictionary.
        cost: Required. Normalized cost metadata.

    Returns:
        None.
    """
    if isinstance(response, dict) and cost_utils.has_available_cost(cost):
        cost_utils.apply_cost_metadata(response, cost)


def update_cost(result, **kwargs):
    """Refresh Runware cost metadata from response data or documented pricing.

    Args:
        result: Required. Normalized result dictionary.
        **kwargs: Optional. Ignored except for dispatcher compatibility.

    Returns:
        The updated result dictionary.
    """
    raw_response = result.get("raw_response") if isinstance(result, dict) else result
    model = result.get("model") if isinstance(result, dict) else None
    details = result.get("cost_details") if isinstance(result, dict) else {}
    cost = _cost(model or DEFAULT_MODEL, raw_response or details or {})
    return cost_utils.apply_cost_metadata(result, cost)


def _headers():
    """Return Runware headers.

    Returns:
        A headers dictionary.
    """
    return provider_api.auth_headers(
        PROVIDER,
        ENV_NAME,
        scheme="bearer",
        extra={"Content-Type": "application/json"},
    )
