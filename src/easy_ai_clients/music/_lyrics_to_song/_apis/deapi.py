from ..._common import cost_utils, provider_api, result_utils

PROVIDER = "deapi"
ENV_NAME = "DEAPI_API_KEY"
DEFAULT_MODEL = "ACE-Step-v1.5-turbo"
ENDPOINT = "https://api.deapi.ai/api/v2/audio/music"
STATUS_ENDPOINT = "https://api.deapi.ai/api/v2/jobs/{request_id}"


def generate_lyrics_to_song(lyrics, prompt=None, output_path=None, sync=True, **kwargs):
    """Generate a song from lyrics with deAPI Text-to-Music.

    Args:
        lyrics: Required. Lyrics or `[Instrumental]` song structure.
        prompt: Optional. Caption describing style and arrangement.
        output_path: Optional. Local destination for completed audio.
        sync: Optional. When false, return after request creation.
        **kwargs: Optional. deAPI text-to-music fields.

    Returns:
        A provider response dictionary.
    """
    kwargs = provider_api.copy_kwargs(kwargs)
    timeout = provider_api.pop_value(kwargs, "timeout", default=60)
    poll_interval = provider_api.pop_value(kwargs, "poll_interval", default=None)
    max_poll_attempts = provider_api.pop_value(kwargs, "max_poll_attempts", default=None)
    model = provider_api.pop_value(kwargs, "model", default=DEFAULT_MODEL)
    endpoint = provider_api.pop_value(kwargs, "endpoint", default=ENDPOINT)
    data, files, close_files = _build_payload(lyrics, prompt=prompt, model=model, **kwargs)
    try:
        response = provider_api.request_json(
            "POST",
            endpoint,
            headers=_headers(),
            data=data,
            payload=None,
            timeout=timeout,
        ) if files is None else _multipart_json(endpoint, data, files, timeout)
    finally:
        close_files()

    response["model"] = model
    response.setdefault("cost_details", _cost_details(model, data))
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
    """Return deAPI job status.

    Args:
        request_id: Required. deAPI request ID.
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
    response.setdefault("cost_details", _cost_details(kwargs.get("model"), kwargs))
    return response


def get_generation_result(request_id, output_path=None, **kwargs):
    """Return a deAPI result.

    Args:
        request_id: Required. deAPI request ID.
        output_path: Optional. Local destination path.
        **kwargs: Optional. Provider request options.

    Returns:
        A provider result dictionary.
    """
    response = get_generation_status(request_id, **kwargs)
    timeout = provider_api.pop_value(kwargs, "timeout", default=60)
    return provider_api.save_audio_from_response(response, output_path, timeout=timeout)


download_generation = get_generation_result


def _build_payload(lyrics, prompt=None, model=None, **kwargs):
    """Build a deAPI multipart payload.

    Args:
        lyrics: Required. Lyrics or `[Instrumental]` song structure.
        prompt: Optional. Caption describing the music.
        model: Optional. deAPI model slug.
        **kwargs: Optional. deAPI fields.

    Returns:
        A `(data, files, close_files)` tuple.
    """
    provider_api.reject_duplicates(kwargs, "lyrics")
    reference_audio = provider_api.pop_value(kwargs, "reference_audio", default=None)
    data = {
        "caption": provider_api.pop_value(kwargs, "caption", default=prompt or ""),
        "model": model or DEFAULT_MODEL,
        "lyrics": lyrics,
        "duration": provider_api.pop_value(kwargs, "duration", default=120),
        "inference_steps": provider_api.pop_value(kwargs, "inference_steps", default=8),
        "guidance_scale": provider_api.pop_value(kwargs, "guidance_scale", default=7),
        "seed": provider_api.pop_value(kwargs, "seed", default=-1),
        "format": provider_api.pop_value(kwargs, "format", default="mp3"),
    }
    data.update(kwargs)

    if reference_audio is None:
        return data, None, lambda: None

    files, close_files = provider_api.multipart_file(
        reference_audio,
        field_name="reference_audio",
    )
    return data, files, close_files


def _multipart_json(endpoint, data, files, timeout):
    """Send a deAPI multipart request and parse JSON.

    Args:
        endpoint: Required. Endpoint URL.
        data: Required. Multipart form fields.
        files: Required. Multipart file mapping.
        timeout: Required. Request timeout in seconds.

    Returns:
        Parsed JSON response.
    """
    response = provider_api.http_utils.multipart_request(
        "POST",
        endpoint,
        files=files,
        headers=_headers(),
        data=data,
        timeout=timeout,
    )
    return provider_api.http_utils.response_json(response)


def _headers():
    """Return deAPI headers.

    Returns:
        A headers dictionary.
    """
    return provider_api.auth_headers(
        PROVIDER,
        ENV_NAME,
        scheme="bearer",
        extra={"Accept": "application/json"},
    )


def update_cost(result, **kwargs):
    """Refresh deAPI cost metadata with the documented price endpoint.

    Args:
        result: Required. Normalized result dictionary.
        **kwargs: Optional. Dispatcher compatibility values.

    Returns:
        The updated result dictionary.
    """
    details = _cost_lookup_details(result)
    payload = {
        "model": details.get("model") or DEFAULT_MODEL,
        "duration": details.get("duration") or 120,
        "inference_steps": details.get("inference_steps") or 8,
    }
    try:
        response = provider_api.request_json(
            "POST",
            _price_endpoint(kwargs),
            headers=_headers(),
            payload=payload,
            timeout=provider_api.pop_value(kwargs, "timeout", default=60),
        )
        cost = cost_utils.normalize_cost(
            _price_from_response(response),
            source="provider_response",
            is_estimated=True,
            details={
                "price_endpoint": "/api/v2/audio/music/price",
                **payload,
            },
        )
    except Exception:
        cost = cost_utils.unavailable_cost_metadata()
    return cost_utils.apply_cost_metadata(result, cost)


def _cost_details(model, payload):
    """Return deAPI cost lookup details.

    Args:
        model: Optional. deAPI model.
        payload: Required. Request payload.

    Returns:
        Cost detail fields.
    """
    return {
        "model": model or (payload or {}).get("model") or DEFAULT_MODEL,
        "duration": (payload or {}).get("duration"),
        "inference_steps": (payload or {}).get("inference_steps"),
    }


def _cost_lookup_details(result):
    """Return deAPI price calculation fields from a result.

    Args:
        result: Required. Normalized result dictionary.

    Returns:
        Cost lookup details.
    """
    details = {}
    if isinstance(result, dict):
        details.update(result.get("cost_details") or {})
        if result.get("model") is not None:
            details.setdefault("model", result["model"])
    return details


def _price_endpoint(kwargs):
    """Return the deAPI price calculation endpoint.

    Args:
        kwargs: Required. Provider options.

    Returns:
        Endpoint URL.
    """
    endpoint = kwargs.get("price_endpoint")
    if endpoint:
        return endpoint
    base_url = kwargs.get("base_url", "https://api.deapi.ai").rstrip("/")
    return f"{base_url}/api/v2/audio/music/price"


def _price_from_response(response):
    """Extract deAPI price from a price calculation response.

    Args:
        response: Required. Provider response.

    Returns:
        The price value.
    """
    if isinstance(response, dict):
        data = response.get("data")
        if isinstance(data, dict) and data.get("price") is not None:
            return data["price"]
        if response.get("price") is not None:
            return response["price"]
    raise RuntimeError("deAPI price calculation response did not include data.price.")
