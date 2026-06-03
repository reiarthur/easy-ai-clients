from . import media_utils


def with_model(model=None, kwargs=None):
    """Return provider kwargs with model included when supplied.

    Args:
        model: Optional. Model name or identifier.
        kwargs: Optional. Existing keyword arguments.

    Returns:
        A new keyword argument dictionary.
    """
    payload = dict(kwargs or {})
    if model is not None:
        payload["model"] = model
    return payload


def add_optional(payload, **values):
    """Add non-None values to a payload.

    Args:
        payload: Required. Payload dictionary to update.
        **values: Optional values to add.

    Returns:
        The updated payload dictionary.
    """
    for key, value in values.items():
        if value is not None:
            payload[key] = value
    return payload


def media_argument(value, path_name="input_path", url_name="input_url",
                   bytes_name="input_bytes", data_uri_name="input_data_uri"):
    """Map a media value to a provider-friendly argument name.

    Args:
        value: Required. Media reference.
        path_name: Optional. Key for local paths.
        url_name: Optional. Key for remote URLs.
        bytes_name: Optional. Key for bytes-like values.
        data_uri_name: Optional. Key for data URIs.

    Returns:
        A dictionary with one media argument.
    """
    if media_utils.is_remote_url(value):
        return {url_name: value}
    if media_utils.is_data_uri(value):
        return {data_uri_name: value}
    if media_utils.is_bytes_like(value):
        return {bytes_name: bytes(value)}
    if media_utils.is_local_path(value):
        return {path_name: value}
    return {path_name: value}


def operation_name(operation, provider=None):
    """Build a readable operation name.

    Args:
        operation: Required. Public operation name.
        provider: Optional. Provider identifier.

    Returns:
        A readable operation string.
    """
    if provider:
        return f"{provider}.{operation}"
    return operation


def common_payload(prompt=None, lyrics=None, media=None, audio=None, voice=None,
                   request_id=None, output_path=None, audio_url=None):
    """Build a common provider payload fragment.

    Args:
        prompt: Optional. Prompt text.
        lyrics: Optional. Lyrics text.
        media: Optional. Media input.
        audio: Optional. Audio input.
        voice: Optional. Voice identifier or reference.
        request_id: Optional. Provider request ID.
        output_path: Optional. Local output path.
        audio_url: Optional. Remote audio URL.

    Returns:
        A payload dictionary without None values.
    """
    return add_optional(
        {},
        prompt=prompt,
        lyrics=lyrics,
        media=media,
        audio=audio,
        voice=voice,
        request_id=request_id,
        output_path=output_path,
        audio_url=audio_url,
    )
