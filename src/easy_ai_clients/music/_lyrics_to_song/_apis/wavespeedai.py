from ..._common import cost_utils, provider_api, result_utils

PROVIDER = "wavespeedai"
ENV_NAME = "WAVESPEEDAI_API_KEY"
DEFAULT_MODEL = "wavespeed-ai/song-generation"
ENDPOINT = "https://api.wavespeed.ai/api/v3/wavespeed-ai/song-generation"
RESULT_ENDPOINT = "https://api.wavespeed.ai/api/v3/predictions/{request_id}/result"


def generate_lyrics_to_song(lyrics, prompt=None, output_path=None, sync=True, **kwargs):
    """Generate a song from lyrics with WaveSpeedAI.

    Args:
        lyrics: Required. Lyrics with supported section tags.
        prompt: Optional. Musical description.
        output_path: Optional. Local destination for completed audio.
        sync: Optional. When false, return after prediction creation.
        **kwargs: Optional. WaveSpeedAI fields.

    Returns:
        A provider response dictionary.
    """
    kwargs = provider_api.copy_kwargs(kwargs)
    timeout = provider_api.pop_value(kwargs, "timeout", default=60)
    poll_interval = provider_api.pop_value(kwargs, "poll_interval", default=None)
    max_poll_attempts = provider_api.pop_value(kwargs, "max_poll_attempts", default=None)
    model = provider_api.pop_value(kwargs, "model", default=DEFAULT_MODEL)
    endpoint = provider_api.pop_value(kwargs, "endpoint", default=ENDPOINT)
    payload = _build_payload(lyrics, prompt=prompt, model=model, **kwargs)
    response = provider_api.request_json(
        "POST",
        endpoint,
        headers=_headers(),
        payload=payload,
        timeout=timeout,
    )
    response["model"] = model
    cost_utils.apply_cost_metadata(response, _cost(model))

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
    """Return WaveSpeedAI prediction status or result.

    Args:
        request_id: Required. WaveSpeedAI prediction ID.
        **kwargs: Optional. Provider request options.

    Returns:
        A provider status dictionary.
    """
    timeout = provider_api.pop_value(kwargs, "timeout", default=60)
    endpoint = provider_api.pop_value(
        kwargs,
        "result_endpoint",
        default=RESULT_ENDPOINT.format(request_id=request_id),
    )
    response = provider_api.request_json("GET", endpoint, headers=_headers(), timeout=timeout)
    response.setdefault("request_id", request_id)
    cost_utils.apply_cost_metadata(response, _cost(kwargs.get("model") or DEFAULT_MODEL))
    return response


def get_generation_result(request_id, output_path=None, **kwargs):
    """Return a WaveSpeedAI result.

    Args:
        request_id: Required. WaveSpeedAI prediction ID.
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
    """Build a WaveSpeedAI song payload.

    Args:
        lyrics: Required. Lyrics with supported section tags.
        prompt: Optional. Musical description.
        model: Optional. Provider model name.
        **kwargs: Optional. WaveSpeedAI fields.

    Returns:
        A JSON payload dictionary.
    """
    provider_api.reject_duplicates(kwargs, "lyric")
    description = provider_api.pop_value(kwargs, "description", default=prompt)
    payload = {"lyric": lyrics}
    provider_api.add_optional(payload, description=description)
    return provider_api.merge_kwargs(payload, kwargs)


def _headers():
    """Return WaveSpeedAI headers.

    Returns:
        A headers dictionary.
    """
    return provider_api.auth_headers(
        PROVIDER,
        ENV_NAME,
        scheme="bearer",
        extra={"Content-Type": "application/json"},
    )


def _cost(model=None):
    """Return estimated WaveSpeedAI starting price metadata.

    Args:
        model: Optional. WaveSpeedAI model name.

    Returns:
        Normalized cost metadata.
    """
    return cost_utils.normalize_cost(
        0.05,
        source="official_pricing_table",
        is_estimated=True,
        details={"model": model, "starting_price_usd": 0.05},
    )


def update_cost(result, **kwargs):
    """Refresh WaveSpeedAI cost metadata from documented starting price.

    Args:
        result: Required. Normalized result dictionary.
        **kwargs: Optional. Dispatcher compatibility values.

    Returns:
        The updated result dictionary.
    """
    model = result.get("model") if isinstance(result, dict) else None
    cost = _cost(model or DEFAULT_MODEL)
    return cost_utils.apply_cost_metadata(result, cost)
