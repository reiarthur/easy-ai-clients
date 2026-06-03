from ..._common import provider_api, result_utils

PROVIDER = "soundverse"
ENV_NAME = "SOUNDVERSE_API_KEY"
DEFAULT_MODEL = "v5-song"
ENDPOINT = "https://api.soundverse.ai/v5/generate/song"
STATUS_ENDPOINT = "https://api.soundverse.ai/v5/status"


def generate_lyrics_to_song(lyrics, prompt=None, output_path=None, sync=True, **kwargs):
    """Generate a song from lyrics with Soundverse.

    Args:
        lyrics: Required. Lyrics or structured song text.
        prompt: Optional. Musical prompt.
        output_path: Optional. Local destination for completed audio.
        sync: Optional. When false, return after request creation.
        **kwargs: Optional. Soundverse fields.

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
    _set_message_request_id(response)

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
    """Return Soundverse status or result.

    Args:
        request_id: Required. Soundverse message ID.
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
        params={"message_id": request_id},
        timeout=timeout,
    )
    response.setdefault("request_id", request_id)
    return response


def get_generation_result(request_id, output_path=None, **kwargs):
    """Return a Soundverse result.

    Args:
        request_id: Required. Soundverse message ID.
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
    """Build a Soundverse song payload.

    Args:
        lyrics: Required. Lyrics or structured song text.
        prompt: Optional. Musical prompt.
        model: Optional. Provider model label.
        **kwargs: Optional. Soundverse fields.

    Returns:
        A JSON payload dictionary.
    """
    provider_api.reject_duplicates(kwargs, "lyrics")
    payload = {"lyrics": lyrics}
    provider_api.add_optional(payload, prompt=prompt)
    return provider_api.merge_kwargs(payload, kwargs)


def _set_message_request_id(response):
    """Copy Soundverse message ID to the normalized request ID field.

    Args:
        response: Required. Provider response dictionary.

    Returns:
        None.
    """
    request_id = response.get("message_id") or response.get("messageId")
    if request_id is not None:
        response.setdefault("request_id", request_id)


def _headers():
    """Return Soundverse headers.

    Returns:
        A headers dictionary.
    """
    return provider_api.auth_headers(
        PROVIDER,
        ENV_NAME,
        scheme="bearer",
        extra={"Content-Type": "application/json"},
    )
