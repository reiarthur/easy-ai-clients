from ..._common import http_utils, media_utils, provider_api

PROVIDER = "elevenlabs"
ENV_NAME = "ELEVENLABS_API_KEY"
DEFAULT_MODEL = "music_v1"
ENDPOINT = "https://api.elevenlabs.io/v1/music/video-to-music"


def generate_media_to_music(media, prompt=None, output_path=None, sync=True, **kwargs):
    """Generate music from video or visual media with ElevenLabs.

    Args:
        media: Required. Video input as URL, local path, bytes, base64, or data URI.
        prompt: Optional. Musical prompt.
        output_path: Optional. Local destination for returned audio.
        sync: Optional. When false, return provider task metadata if returned.
        **kwargs: Optional. ElevenLabs video-to-music fields.

    Returns:
        A provider response dictionary.
    """
    kwargs = provider_api.copy_kwargs(kwargs)
    timeout = provider_api.pop_value(kwargs, "timeout", default=60)
    model = provider_api.pop_value(kwargs, "model", default=DEFAULT_MODEL)
    endpoint = provider_api.pop_value(kwargs, "endpoint", default=ENDPOINT)
    data, files, close_files, metadata = _build_payload(
        media,
        prompt=prompt,
        model=model,
        **kwargs,
    )
    headers = provider_api.auth_headers(PROVIDER, ENV_NAME, scheme="xi-api-key")
    try:
        if files:
            response = http_utils.multipart_request(
                "POST",
                endpoint,
                files=files,
                headers=headers,
                data=data,
                timeout=timeout,
            )
            return _response_to_result(response, model, output_path, metadata, timeout)

        headers["Content-Type"] = "application/json"
        response = provider_api.request_json(
            "POST",
            endpoint,
            headers=headers,
            payload=data,
            timeout=timeout,
        )
    finally:
        close_files()

    response["model"] = model
    response["provider_metadata"] = metadata
    if not sync:
        response.setdefault("status", "submitted")
    return provider_api.save_audio_from_response(response, output_path, timeout=timeout)


def _build_payload(media, prompt=None, model=None, **kwargs):
    """Build an ElevenLabs video-to-music payload.

    Args:
        media: Required. Media input or list of media inputs.
        prompt: Optional. Musical prompt.
        model: Optional. Provider model name.
        **kwargs: Optional. Provider fields.

    Returns:
        A `(data, files, close_files, metadata)` tuple.
    """
    media_values = media if isinstance(media, list | tuple) else [media]
    metadata = {"input_media": [provider_api.safe_media_metadata(item) for item in media_values]}
    data = dict(kwargs)
    provider_api.add_optional(data, prompt=prompt, model_id=model)

    if all(media_utils.is_remote_url(item) for item in media_values):
        data["video_urls"] = list(media_values)
        return data, None, lambda: None, metadata

    files = []
    closers = []
    for index, item in enumerate(media_values):
        field_name = "videos" if len(media_values) > 1 else "video"
        file_map, close_file = provider_api.multipart_file(
            item,
            field_name=field_name,
            filename=media_utils.infer_filename(item, default=f"media-{index + 1}"),
        )
        files.extend(file_map.items())
        closers.append(close_file)

    return data, files, lambda: [close_file() for close_file in closers], metadata


def _response_to_result(response, model, output_path, metadata, timeout):
    """Convert an ElevenLabs HTTP response into a provider result.

    Args:
        response: Required. HTTP response object.
        model: Required. Provider model name.
        output_path: Optional. Local destination path.
        metadata: Required. Safe provider metadata.
        timeout: Required. Download timeout in seconds.

    Returns:
        A provider response dictionary.
    """
    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        parsed = http_utils.response_json(response)
        parsed["model"] = model
        parsed["provider_metadata"] = metadata
        return provider_api.save_audio_from_response(parsed, output_path, timeout=timeout)

    saved_path = provider_api.save_bytes(response.content, output_path)
    return {
        "model": model,
        "status": "completed",
        "audio": None if saved_path else response.content,
        "output_path": saved_path,
        "provider_metadata": metadata,
    }
