from ..._common import provider_api, result_utils

PROVIDER = "topmediai"
ENV_NAME = "TOPMEDIAI_API_KEY"
DEFAULT_MODEL = "v4.5-plus"
ENDPOINT = "https://api.topmediai.com/v3/music/generate"
STATUS_ENDPOINT = "https://api.topmediai.com/v3/music/tasks"


def generate_lyrics_to_song(lyrics, prompt=None, output_path=None, sync=True, **kwargs):
    """Generate a song from lyrics with TopMediai.

    Args:
        lyrics: Required. Lyrics or structured song text.
        prompt: Optional. Style prompt.
        output_path: Optional. Local destination for completed audio.
        sync: Optional. When false, return after task creation.
        **kwargs: Optional. TopMediai fields.

    Returns:
        A provider response dictionary.
    """
    kwargs = provider_api.copy_kwargs(kwargs)
    timeout = provider_api.pop_value(kwargs, "timeout", default=60)
    poll_interval = provider_api.pop_value(kwargs, "poll_interval", default=None)
    max_poll_attempts = provider_api.pop_value(kwargs, "max_poll_attempts", default=None)
    model = provider_api.pop_value(kwargs, "model", "mv", default=DEFAULT_MODEL)
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
    """Return TopMediai task status.

    Args:
        request_id: Required. TopMediai task ID.
        **kwargs: Optional. Provider request options.

    Returns:
        A provider status dictionary.
    """
    timeout = provider_api.pop_value(kwargs, "timeout", default=60)
    endpoint = provider_api.pop_value(kwargs, "status_endpoint", default=STATUS_ENDPOINT)
    response = provider_api.request_json(
        "GET",
        endpoint,
        headers=_headers(),
        params={"ids": request_id},
        timeout=timeout,
    )
    response.setdefault("request_id", request_id)
    return response


def get_generation_result(request_id, output_path=None, **kwargs):
    """Return a TopMediai result.

    Args:
        request_id: Required. TopMediai task ID.
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
    """Build a TopMediai generation payload.

    Args:
        lyrics: Required. Lyrics or structured song text.
        prompt: Optional. Style prompt.
        model: Optional. TopMediai model version.
        **kwargs: Optional. TopMediai fields.

    Returns:
        A JSON payload dictionary.
    """
    provider_api.reject_duplicates(kwargs, "lyrics")
    instrumental = kwargs.get("instrumental")
    if instrumental in (1, True, "1", "true"):
        raise ValueError("TopMediai instrumental generation should not include lyrics.")
    action = provider_api.pop_value(kwargs, "action", default="generate")
    style = provider_api.pop_value(kwargs, "style", default=prompt)
    payload = {"action": action, "lyrics": lyrics, "mv": model or DEFAULT_MODEL}
    provider_api.add_optional(payload, style=style)
    return provider_api.merge_kwargs(payload, kwargs)


def _headers():
    """Return TopMediai headers.

    Returns:
        A headers dictionary.
    """
    return provider_api.auth_headers(
        PROVIDER,
        ENV_NAME,
        scheme="x-api-key",
        extra={"Content-Type": "application/json"},
    )
