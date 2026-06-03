from ..._common import provider_api, result_utils

PROVIDER = "generatesongs"
ENV_NAME = "GENERATESONGS_API_KEY"
DEFAULT_MODEL = "songs-generate"
ENDPOINT = "https://generatesongs.ai/api/v1/songs/generate"
STATUS_ENDPOINT = "https://generatesongs.ai/api/v1/songs/{request_id}"


def generate_lyrics_to_song(lyrics, prompt=None, output_path=None, sync=True, **kwargs):
    """Generate a song from lyrics with GenerateSongs.ai.

    Args:
        lyrics: Required. Lyrics or structured song text.
        prompt: Optional. Style prompt.
        output_path: Optional. Local destination for completed audio.
        sync: Optional. When false, return after song creation.
        **kwargs: Optional. GenerateSongs fields.

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
    _set_song_request_id(response)

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
    """Return GenerateSongs song status.

    Args:
        request_id: Required. GenerateSongs song ID.
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
    """Return a GenerateSongs result.

    Args:
        request_id: Required. GenerateSongs song ID.
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
    """Build a GenerateSongs payload.

    Args:
        lyrics: Required. Lyrics or structured song text.
        prompt: Optional. Style prompt.
        model: Optional. Provider model label.
        **kwargs: Optional. GenerateSongs fields.

    Returns:
        A JSON payload dictionary.
    """
    provider_api.reject_duplicates(kwargs, "lyrics")
    style = provider_api.pop_value(kwargs, "style", default=prompt)
    has_reference = any(
        kwargs.get(name)
        for name in ("referenceFileId", "vocalFileId", "melodyFileId")
    )
    if style is None and not has_reference:
        raise ValueError(
            "GenerateSongs requires prompt/style or a referenceFileId, vocalFileId, "
            "or melodyFileId."
        )
    payload = {"lyrics": lyrics}
    provider_api.add_optional(payload, style=style)
    return provider_api.merge_kwargs(payload, kwargs)


def _set_song_request_id(response):
    """Copy GenerateSongs song ID to the normalized request ID field.

    Args:
        response: Required. Provider response dictionary.

    Returns:
        None.
    """
    request_id = response.get("songId") or response.get("song_id")
    if request_id is not None:
        response.setdefault("request_id", request_id)


def _headers():
    """Return GenerateSongs headers.

    Returns:
        A headers dictionary.
    """
    return provider_api.auth_headers(
        PROVIDER,
        ENV_NAME,
        scheme="bearer",
        extra={"Content-Type": "application/json"},
    )
