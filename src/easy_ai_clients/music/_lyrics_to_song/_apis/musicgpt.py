from ..._common import provider_api, result_utils

PROVIDER = "musicgpt"
ENV_NAME = "MUSICGPT_API_KEY"
DEFAULT_MODEL = "MusicAI"
ENDPOINT = "https://api.musicgpt.com/api/public/v1/MusicAI"
STATUS_ENDPOINT = "https://api.musicgpt.com/api/public/v1/MusicAI/{request_id}"


def generate_lyrics_to_song(lyrics, prompt=None, output_path=None, sync=True, **kwargs):
    """Generate a song from lyrics with MusicGPT.

    Args:
        lyrics: Required. Lyrics or structured song text.
        prompt: Optional. Musical prompt.
        output_path: Optional. Local destination for completed audio.
        sync: Optional. When false, return after task creation.
        **kwargs: Optional. MusicGPT fields.

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
    """Return MusicGPT task status or result.

    Args:
        request_id: Required. MusicGPT task ID.
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
    return response


def get_generation_result(request_id, output_path=None, **kwargs):
    """Return a MusicGPT result.

    Args:
        request_id: Required. MusicGPT task ID.
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
    """Build a MusicGPT payload.

    Args:
        lyrics: Required. Lyrics or structured song text.
        prompt: Optional. Musical prompt.
        model: Optional. Provider model label.
        **kwargs: Optional. MusicGPT fields.

    Returns:
        A JSON payload dictionary.
    """
    provider_api.reject_duplicates(kwargs, "lyrics")
    payload = {"lyrics": lyrics}
    provider_api.add_optional(payload, prompt=prompt)
    return provider_api.merge_kwargs(payload, kwargs)


def _headers():
    """Return MusicGPT headers.

    Returns:
        A headers dictionary.
    """
    return provider_api.auth_headers(
        PROVIDER,
        ENV_NAME,
        scheme="authorization",
        extra={"Content-Type": "application/json"},
    )
