from ..._common import provider_api

PROVIDER = "novita"
ENV_NAME = "NOVITA_API_KEY"
DEFAULT_MODEL = "music-2.5+"
ENDPOINT = "https://api.novita.ai/v3/minimax-music"


def generate_lyrics_to_song(lyrics, prompt=None, output_path=None, sync=True, **kwargs):
    """Generate a song from lyrics with Novita MiniMax Music.

    Args:
        lyrics: Required. Lyrics or structured song text.
        prompt: Optional. Style prompt.
        output_path: Optional. Local destination for the first returned URL.
        sync: Optional. Ignored because the documented endpoint returns URLs.
        **kwargs: Optional. Novita MiniMax fields.

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
    """Build a Novita MiniMax Music payload.

    Args:
        lyrics: Required. Lyrics or structured song text.
        prompt: Optional. Style prompt.
        model: Optional. Provider model name.
        **kwargs: Optional. Novita fields.

    Returns:
        A JSON payload dictionary.
    """
    provider_api.reject_duplicates(kwargs, "lyrics")
    watermark = kwargs.pop("watermark", None)
    if watermark is not None and "aigc_watermark" not in kwargs:
        kwargs["aigc_watermark"] = watermark

    payload = {"model": model or DEFAULT_MODEL, "lyrics": lyrics}
    provider_api.add_optional(payload, prompt=prompt)
    return provider_api.merge_kwargs(payload, kwargs)
