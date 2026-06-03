from ..._common import provider_api, result_utils

PROVIDER = "falai"
ENV_NAME = "FAL_KEY"
DEFAULT_MODEL = "fal-ai/minimax-music/v2.6"
ENDPOINT = "https://queue.fal.run/{model}"
STATUS_ENDPOINT = "https://queue.fal.run/{model}/requests/{request_id}/status"
RESULT_ENDPOINT = "https://queue.fal.run/{model}/requests/{request_id}/response"


def generate_lyrics_to_song(lyrics, prompt=None, output_path=None, sync=True, **kwargs):
    """Generate a song from lyrics with a fal.ai music model.

    Args:
        lyrics: Required. Lyrics or structured song text.
        prompt: Optional. Model prompt.
        output_path: Optional. Local destination for completed audio.
        sync: Optional. When false, return after queue submission.
        **kwargs: Optional. fal.ai model fields.

    Returns:
        A provider response dictionary.
    """
    kwargs = provider_api.copy_kwargs(kwargs)
    timeout = provider_api.pop_value(kwargs, "timeout", default=60)
    poll_interval = provider_api.pop_value(kwargs, "poll_interval", default=None)
    max_poll_attempts = provider_api.pop_value(kwargs, "max_poll_attempts", default=None)
    model = provider_api.pop_value(kwargs, "model", "model_id", default=DEFAULT_MODEL)
    endpoint = provider_api.pop_value(kwargs, "endpoint", default=ENDPOINT.format(model=model))
    payload = _build_payload(lyrics, prompt=prompt, model=model, **kwargs)
    response = provider_api.request_json(
        "POST",
        endpoint,
        headers=_headers(),
        payload=payload,
        timeout=timeout,
    )
    response["model"] = model

    request_id = result_utils.extract_request_id(response)
    if not sync or not request_id:
        response.setdefault("status", "submitted")
        return response

    return provider_api.poll_result(
        lambda job_id: get_generation_status(job_id, model=model),
        request_id,
        output_path=output_path,
        result_function=lambda job_id, output_path=None: get_generation_result(
            job_id,
            output_path=output_path,
            model=model,
        ),
        poll_interval=poll_interval,
        max_poll_attempts=max_poll_attempts,
    )


def get_generation_status(request_id, **kwargs):
    """Return fal.ai queue status.

    Args:
        request_id: Required. fal.ai request ID.
        **kwargs: Optional. Provider request options.

    Returns:
        A provider status dictionary.
    """
    timeout = provider_api.pop_value(kwargs, "timeout", default=60)
    model = provider_api.pop_value(kwargs, "model", "model_id", default=DEFAULT_MODEL)
    endpoint = provider_api.pop_value(
        kwargs,
        "status_endpoint",
        default=STATUS_ENDPOINT.format(model=model, request_id=request_id),
    )
    response = provider_api.request_json("GET", endpoint, headers=_headers(), timeout=timeout)
    response.setdefault("request_id", request_id)
    response.setdefault("model", model)
    return response


def get_generation_result(request_id, output_path=None, **kwargs):
    """Return fal.ai queue result.

    Args:
        request_id: Required. fal.ai request ID.
        output_path: Optional. Local destination path.
        **kwargs: Optional. Provider request options.

    Returns:
        A provider result dictionary.
    """
    timeout = provider_api.pop_value(kwargs, "timeout", default=60)
    model = provider_api.pop_value(kwargs, "model", "model_id", default=DEFAULT_MODEL)
    endpoint = provider_api.pop_value(
        kwargs,
        "result_endpoint",
        default=RESULT_ENDPOINT.format(model=model, request_id=request_id),
    )
    response = provider_api.request_json("GET", endpoint, headers=_headers(), timeout=timeout)
    response.setdefault("request_id", request_id)
    response.setdefault("model", model)
    return provider_api.save_audio_from_response(response, output_path, timeout=timeout)


download_generation = get_generation_result


def _build_payload(lyrics, prompt=None, model=None, **kwargs):
    """Build a fal.ai model payload.

    Args:
        lyrics: Required. Lyrics or structured song text.
        prompt: Optional. Model prompt.
        model: Optional. fal.ai model ID.
        **kwargs: Optional. Model-specific fields.

    Returns:
        A JSON payload dictionary.
    """
    provider_api.reject_duplicates(kwargs, "lyrics")
    payload = {"lyrics": lyrics}
    provider_api.add_optional(payload, prompt=prompt)
    return provider_api.merge_kwargs(payload, kwargs)


def _headers():
    """Return fal.ai headers.

    Returns:
        A headers dictionary.
    """
    return provider_api.auth_headers(
        PROVIDER,
        ENV_NAME,
        scheme="fal",
        extra={"Content-Type": "application/json"},
    )
