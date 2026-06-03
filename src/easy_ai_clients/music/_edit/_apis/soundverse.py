from ..._common import operation_utils as _ops

PROVIDER = "soundverse"
ENV_NAME = "SOUNDVERSE_API_KEY"
DEFAULT_MODEL = None
BASE_URL = "https://api.soundverse.ai"
EDIT_ENDPOINT_PATH = "/v5/extend/song"
STATUS_ENDPOINT_PATH = "/v5/status"


def edit_music(audio, prompt=None, output_path=None, sync=True, **kwargs):
    """Extend music with Soundverse.

    Args:
        audio: Required. Source audio URL or task/audio reference.
        prompt: Optional. Continuation prompt.
        output_path: Optional. Destination path for a final URL.
        sync: Optional. Poll status when `message_id` is returned.
        **kwargs: Optional. Provider-native Soundverse fields.

    Returns:
        A normalized music result.
    """
    model = _ops.resolve_model(kwargs, DEFAULT_MODEL)
    payload = _build_payload(audio, prompt=prompt, **kwargs)
    endpoint = _ops.resolve_endpoint(
        kwargs,
        base_url=BASE_URL,
        path=EDIT_ENDPOINT_PATH,
    )
    raw_response = _ops.post_json(
        endpoint,
        headers=_headers(kwargs),
        payload=payload,
        params=kwargs.get("params"),
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
        request_kwargs=kwargs.get("request_kwargs"),
    )
    request_id = _ops.result_utils.extract_request_id(raw_response)
    if sync and request_id:
        raw_response = _ops.poll_status(
            request_id,
            lambda value: _request_status(value, **kwargs),
            None,
            interval=kwargs.get("poll_interval", 5),
            timeout=kwargs.get("poll_timeout", 300),
        )
    return _ops.result(
        PROVIDER,
        model,
        raw_response,
        output_path=output_path,
        cost=_cost(raw_response, payload),
        metadata=_ops.provider_metadata(
            raw_response,
            audio,
            extra={"edit_flow": "extend_song"},
        ),
        download_timeout=kwargs.get("download_timeout", 60),
    )


def get_generation_status(request_id, **kwargs):
    """Get Soundverse task status.

    Args:
        request_id: Required. Soundverse message ID.
        **kwargs: Optional. Local request controls.

    Returns:
        A normalized music result.
    """
    raw_response = _request_status(request_id, **kwargs)
    return _ops.result(PROVIDER, _ops.resolve_model(kwargs), raw_response, cost=_cost(raw_response))


def get_generation_result(request_id, output_path=None, **kwargs):
    """Get Soundverse task result through the status endpoint.

    Args:
        request_id: Required. Soundverse message ID.
        output_path: Optional. Destination path.
        **kwargs: Optional. Local request controls.

    Returns:
        A normalized music result.
    """
    raw_response = _request_status(request_id, **kwargs)
    return _ops.result(
        PROVIDER,
        _ops.resolve_model(kwargs),
        raw_response,
        output_path=output_path,
        cost=_cost(raw_response),
        download_timeout=kwargs.get("download_timeout", 60),
    )


def download_generation(request_id, output_path=None, **kwargs):
    """Download a completed Soundverse result.

    Args:
        request_id: Required. Soundverse message ID.
        output_path: Optional. Destination path.
        **kwargs: Optional. Local request controls.

    Returns:
        A normalized music result.
    """
    return get_generation_result(request_id, output_path=output_path, **kwargs)


def _build_payload(audio, prompt=None, **kwargs):
    """Build the Soundverse edit payload.

    Args:
        audio: Required. Source audio.
        prompt: Optional. Continuation prompt.
        **kwargs: Optional. Provider-native fields.

    Returns:
        A provider payload dictionary.
    """
    payload = _ops.forwarded_payload(kwargs)
    _ops.add_prompt(payload, prompt)
    _ops.add_audio_input(payload, audio, url_key="audio_url", generic_key="audio_url")
    return payload


def _headers(kwargs):
    """Build Soundverse headers.

    Args:
        kwargs: Required. Local controls.

    Returns:
        Request headers.
    """
    headers = _ops.bearer_headers(PROVIDER, ENV_NAME)
    return _ops.merge_headers(headers, kwargs.get("headers"))


def _request_status(request_id, **kwargs):
    """Request raw Soundverse status.

    Args:
        request_id: Required. Message ID.
        **kwargs: Optional. Local request controls.

    Returns:
        Raw provider response.
    """
    endpoint = _ops.resolve_endpoint(
        {"endpoint": kwargs.get("status_endpoint"), "base_url": kwargs.get("base_url")},
        base_url=BASE_URL,
        path=STATUS_ENDPOINT_PATH,
    )
    return _ops.get_json(
        endpoint,
        headers=_headers(kwargs),
        params=kwargs.get("params") or {"message_id": request_id},
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
        request_kwargs=kwargs.get("request_kwargs"),
    )


def _cost(raw_response=None, payload=None):
    """Return Soundverse cost metadata.

    Args:
        raw_response: Optional. Provider response.
        payload: Optional. Request payload.

    Returns:
        Normalized cost metadata.
    """
    return _ops.unavailable_cost(
        {"reason": "Soundverse public docs do not expose per-request cost."}
    )
