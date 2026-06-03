from ..._common import provider_api

PROVIDER = "segmind"
ENV_NAME = "SEGMIND_API_KEY"
DEFAULT_MODEL = "ace-step-music"
ENDPOINT = "https://api.segmind.com/v1/ace-step-music"


def generate_lyrics_to_song(lyrics, prompt=None, output_path=None, sync=True, **kwargs):
    """Generate a song from lyrics with Segmind ACE-Step.

    Args:
        lyrics: Required. Lyrics or structured song text.
        prompt: Optional. Genre or style direction.
        output_path: Optional. Local path for binary or base64 output.
        sync: Optional. Ignored because this endpoint returns audio content.
        **kwargs: Optional. Segmind model fields.

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
        scheme="x-api-key",
        extra={"Content-Type": "application/json"},
    )

    if payload.get("base64"):
        response = provider_api.request_json(
            "POST",
            endpoint,
            headers=headers,
            payload=payload,
            timeout=timeout,
        )
        response["model"] = model
        return provider_api.save_audio_from_response(response, output_path, timeout=timeout)

    audio = provider_api.request_binary(
        "POST",
        endpoint,
        headers=headers,
        payload=payload,
        timeout=timeout,
    )
    saved_path = provider_api.save_bytes(audio, output_path)
    return {
        "model": model,
        "status": "completed",
        "audio": None if saved_path else audio,
        "output_path": saved_path,
    }


def _build_payload(lyrics, prompt=None, model=None, **kwargs):
    """Build a Segmind ACE-Step payload.

    Args:
        lyrics: Required. Lyrics or structured song text.
        prompt: Optional. Genres and musical elements.
        model: Optional. Provider model name.
        **kwargs: Optional. Segmind fields.

    Returns:
        A JSON payload dictionary.
    """
    provider_api.reject_duplicates(kwargs, "lyrics")
    genres = provider_api.pop_value(kwargs, "genres", default=prompt)
    output_seconds = provider_api.pop_value(kwargs, "output_seconds", default=None)
    payload = {"lyrics": lyrics}
    provider_api.add_optional(payload, genres=genres, output_seconds=output_seconds)
    return provider_api.merge_kwargs(payload, kwargs)
