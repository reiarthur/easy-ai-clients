from ..._common import media_utils, provider_api, result_utils

PROVIDER = "musicgpt"
ENV_NAME = "MUSICGPT_API_KEY"
DEFAULT_MODEL = "MusicAI"
ENDPOINT = "https://api.musicgpt.com/api/public/v1/MusicAI"
STATUS_ENDPOINT = "https://api.musicgpt.com/api/public/v1/MusicAI/{request_id}"


def generate_media_to_music(media, prompt=None, output_path=None, sync=True, **kwargs):
    """Generate music from visual media with MusicGPT.

    Args:
        media: Required. Image input as URL, local path, bytes, base64, or data URI.
        prompt: Optional. Musical prompt.
        output_path: Optional. Local destination for completed audio.
        sync: Optional. When false, return after task creation.
        **kwargs: Optional. MusicGPT image-to-song fields.

    Returns:
        A provider response dictionary.
    """
    kwargs = provider_api.copy_kwargs(kwargs)
    timeout = provider_api.pop_value(kwargs, "timeout", default=60)
    poll_interval = provider_api.pop_value(kwargs, "poll_interval", default=None)
    max_poll_attempts = provider_api.pop_value(kwargs, "max_poll_attempts", default=None)
    model = provider_api.pop_value(kwargs, "model", default=DEFAULT_MODEL)
    endpoint = provider_api.pop_value(kwargs, "endpoint", default=ENDPOINT)
    payload, metadata = _build_payload(media, prompt=prompt, model=model, **kwargs)
    response = provider_api.request_json(
        "POST",
        endpoint,
        headers=_headers(),
        payload=payload,
        timeout=timeout,
    )
    response["model"] = model
    response["provider_metadata"] = metadata

    request_id = result_utils.extract_request_id(response)
    if not sync or not request_id:
        response.setdefault("status", "submitted")
        return response

    result = provider_api.poll_result(
        get_generation_status,
        request_id,
        output_path=output_path,
        poll_interval=poll_interval,
        max_poll_attempts=max_poll_attempts,
    )
    result.setdefault("provider_metadata", metadata)
    return result


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


def _build_payload(media, prompt=None, model=None, **kwargs):
    """Build a MusicGPT media-to-music payload.

    Args:
        media: Required. Image or visual media input.
        prompt: Optional. Musical prompt.
        model: Optional. Provider model label.
        **kwargs: Optional. MusicGPT fields.

    Returns:
        A `(payload, metadata)` tuple.
    """
    metadata = {"input_media": provider_api.safe_media_metadata(media)}
    payload = dict(kwargs)
    provider_api.add_optional(payload, prompt=prompt)
    if media_utils.is_remote_url(media):
        payload["image_url"] = media
    else:
        payload["image"] = provider_api.media_as_data_uri(media)
    return payload, metadata


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
