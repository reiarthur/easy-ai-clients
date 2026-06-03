from ..._common import provider_api

PROVIDER = "minimax"
ENV_NAME = "MINIMAX_API_KEY"
DEFAULT_MODEL = "music-2.6"
ENDPOINT = "https://api.minimax.io/v1/music_generation"


def generate_lyrics_to_song(lyrics, prompt=None, output_path=None, sync=True, **kwargs):
    """Generate a song from lyrics with MiniMax Music.

    Args:
        lyrics: Required. Lyrics or structured song text.
        prompt: Optional. Style prompt. Required by provider for instrumental mode.
        output_path: Optional. Local destination for URL or hex output.
        sync: Optional. Ignored for the documented non-stream request.
        **kwargs: Optional. MiniMax music generation fields.

    Returns:
        A provider response dictionary.
    """
    kwargs = provider_api.copy_kwargs(kwargs)
    timeout = provider_api.pop_value(kwargs, "timeout", default=60)
    model = provider_api.pop_value(kwargs, "model", default=DEFAULT_MODEL)
    endpoint = provider_api.pop_value(kwargs, "endpoint", default=ENDPOINT)
    payload = _build_payload(lyrics, prompt=prompt, model=model, **kwargs)
    headers = provider_api.auth_headers(
        PROVIDER,
        ENV_NAME,
        scheme="bearer",
        extra={"Content-Type": "application/json"},
    )
    response = provider_api.request_json(
        "POST",
        endpoint,
        headers=headers,
        payload=payload,
        timeout=timeout,
    )
    response["model"] = model
    return provider_api.save_audio_from_response(response, output_path, timeout=timeout)


def _build_payload(lyrics, prompt=None, model=None, **kwargs):
    """Build a MiniMax music generation payload.

    Args:
        lyrics: Required. Lyrics or structured song text.
        prompt: Optional. Style prompt.
        model: Optional. Provider model name.
        **kwargs: Optional. MiniMax fields.

    Returns:
        A JSON payload dictionary.
    """
    provider_api.reject_duplicates(kwargs, "lyrics")
    payload = {"model": model or DEFAULT_MODEL, "lyrics": lyrics}
    provider_api.add_optional(payload, prompt=prompt)
    return provider_api.merge_kwargs(payload, kwargs)
