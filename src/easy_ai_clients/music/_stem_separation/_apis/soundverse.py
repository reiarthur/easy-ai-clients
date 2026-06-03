from ..._common import operation_utils as _ops

PROVIDER = "soundverse"
ENV_NAME = "SOUNDVERSE_API_KEY"
DEFAULT_MODEL = None
BASE_URL = "https://api.soundverse.ai"
STATUS_ENDPOINT_PATH = "/v5/status"
STEM_ENDPOINT_PATH = "/v1/generate/stem-separation/{stem_type}"


def separate_stems(audio, output_path=None, sync=True, **kwargs):
    """Get Soundverse stems from a task or provider-native endpoint.

    Args:
        audio: Required. Source audio URL or Soundverse message ID.
        output_path: Optional. Destination path for a ZIP or final URL.
        sync: Optional. Poll status when a message ID is supplied.
        **kwargs: Optional. Provider-native fields and local controls.

    Returns:
        A normalized result with `stems`.
    """
    model = _ops.resolve_model(kwargs, DEFAULT_MODEL)
    message_id = kwargs.get("message_id") or kwargs.get("request_id")

    if message_id:
        message_id = message_id or audio
        raw_response = _poll_or_status(message_id, sync=sync, **kwargs)
    else:
        payload = _build_payload(audio, **kwargs)
        endpoint = _stem_endpoint(kwargs)
        raw_response = _ops.post_json(
            endpoint,
            headers=_headers(kwargs),
            payload=payload,
            params=kwargs.get("params"),
            timeout=kwargs.get("timeout", 60),
            retries=kwargs.get("retries", 2),
            request_kwargs=kwargs.get("request_kwargs"),
        )
        message_id = _ops.result_utils.extract_request_id(raw_response)
        if sync and message_id:
            raw_response = _poll_or_status(message_id, sync=True, **kwargs)

    return _ops.result(
        PROVIDER,
        model,
        raw_response,
        output_path=output_path,
        cost=_cost(raw_response),
        metadata=_ops.provider_metadata(raw_response, audio, include_stems=True),
        stems=True,
        download_timeout=kwargs.get("download_timeout", 60),
    )


def get_generation_status(request_id, **kwargs):
    """Get Soundverse task status.

    Args:
        request_id: Required. Soundverse message ID.
        **kwargs: Optional. Local request controls.

    Returns:
        A normalized result with `stems` when available.
    """
    raw_response = _request_status(request_id, **kwargs)
    return _ops.result(
        PROVIDER,
        _ops.resolve_model(kwargs),
        raw_response,
        cost=_cost(raw_response),
        metadata=_ops.provider_metadata(raw_response, include_stems=True),
        stems=True,
    )


def get_generation_result(request_id, output_path=None, **kwargs):
    """Get Soundverse stem task result.

    Args:
        request_id: Required. Soundverse message ID.
        output_path: Optional. Destination path.
        **kwargs: Optional. Local request controls.

    Returns:
        A normalized result with `stems`.
    """
    raw_response = _request_status(request_id, **kwargs)
    return _ops.result(
        PROVIDER,
        _ops.resolve_model(kwargs),
        raw_response,
        output_path=output_path,
        cost=_cost(raw_response),
        metadata=_ops.provider_metadata(raw_response, include_stems=True),
        stems=True,
        download_timeout=kwargs.get("download_timeout", 60),
    )


def download_generation(request_id, output_path=None, **kwargs):
    """Download Soundverse stems from a completed task.

    Args:
        request_id: Required. Soundverse message ID.
        output_path: Optional. Destination path.
        **kwargs: Optional. Local request controls.

    Returns:
        A normalized result with `stems`.
    """
    return get_generation_result(request_id, output_path=output_path, **kwargs)


def _build_payload(audio, **kwargs):
    """Build the Soundverse stem payload.

    Args:
        audio: Required. Source audio.
        **kwargs: Optional. Provider-native fields.

    Returns:
        A provider payload dictionary.
    """
    payload = _ops.forwarded_payload(kwargs, exclude=("stem", "stem_type", "mode"))
    _ops.add_audio_input(payload, audio, url_key="audioUrl", generic_key="audioUrl")
    return payload


def _stem_endpoint(kwargs):
    """Return the documented Soundverse stem separation endpoint.

    Args:
        kwargs: Required. Provider kwargs.

    Returns:
        A full endpoint URL.
    """
    stem_type = kwargs.get("stem_type") or kwargs.get("stem") or kwargs.get("mode")
    stem_type = _stem_type(stem_type)
    return _ops.resolve_endpoint(
        {
            "endpoint": kwargs.get("endpoint"),
            "base_url": kwargs.get("base_url"),
        },
        base_url=BASE_URL,
        path=STEM_ENDPOINT_PATH.format(stem_type=stem_type),
    )


def _stem_type(value):
    """Normalize Soundverse stem endpoint variants.

    Args:
        value: Optional. Stem endpoint variant.

    Returns:
        One of the documented endpoint path variants.
    """
    if value in (None, "", "all"):
        return "all-stems"
    return str(value).strip()


def _headers(kwargs):
    """Build Soundverse headers.

    Args:
        kwargs: Required. Local controls.

    Returns:
        Request headers.
    """
    headers = _ops.bearer_headers(PROVIDER, ENV_NAME)
    return _ops.merge_headers(headers, kwargs.get("headers"))


def _poll_or_status(message_id, sync=True, **kwargs):
    """Return Soundverse status or poll until completion.

    Args:
        message_id: Required. Soundverse message ID.
        sync: Optional. Whether to poll.
        **kwargs: Optional. Local request controls.

    Returns:
        Raw provider response.
    """
    if not sync:
        return _request_status(message_id, **kwargs)
    return _ops.poll_status(
        message_id,
        lambda value: _request_status(value, **kwargs),
        None,
        interval=kwargs.get("poll_interval", 5),
        timeout=kwargs.get("poll_timeout", 300),
    )


def _request_status(message_id, **kwargs):
    """Request raw Soundverse status.

    Args:
        message_id: Required. Soundverse message ID.
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
        params=kwargs.get("params") or {"message_id": message_id},
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
        {"reason": "Soundverse public docs do not expose stem separation cost."}
    )
