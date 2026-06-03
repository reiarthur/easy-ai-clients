from ..._common import operation_utils as _ops

PROVIDER = "elevenlabs"
ENV_NAME = "ELEVENLABS_API_KEY"
DEFAULT_MODEL = "music_v1"


def separate_stems(audio, output_path=None, sync=True, **kwargs):
    """Separate stems with ElevenLabs.

    Args:
        audio: Required. Source music audio.
        output_path: Optional. Destination path for returned ZIP or final URL.
        sync: Optional. Accepted for dispatcher consistency.
        **kwargs: Optional. Provider-native stem separation fields. Include
            `endpoint` when using an ElevenLabs flow without a wrapper default.

    Returns:
        A normalized result with `stems`.
    """
    model = _ops.resolve_model(kwargs, DEFAULT_MODEL)
    payload = _build_payload(audio, **kwargs)
    endpoint = _ops.resolve_endpoint(kwargs)
    raw_response = _ops.post_json(
        endpoint,
        headers=_headers(kwargs),
        payload=payload,
        params=kwargs.get("params"),
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
        request_kwargs=kwargs.get("request_kwargs"),
    )
    return _ops.result(
        PROVIDER,
        model,
        raw_response,
        output_path=output_path,
        cost=_cost(raw_response, payload),
        metadata=_ops.provider_metadata(raw_response, audio, include_stems=True),
        stems=True,
        download_timeout=kwargs.get("download_timeout", 60),
    )


def _build_payload(audio, **kwargs):
    """Build the ElevenLabs stem separation payload.

    Args:
        audio: Required. Source music audio.
        **kwargs: Optional. Provider-native fields.

    Returns:
        A provider payload dictionary.
    """
    payload = _ops.forwarded_payload(kwargs)
    model = _ops.resolve_model(kwargs, DEFAULT_MODEL)
    if model is not None:
        payload.setdefault("model", model)
    _ops.add_audio_input(payload, audio, url_key="audio_url", generic_key="audio")
    return payload


def _headers(kwargs):
    """Build ElevenLabs headers.

    Args:
        kwargs: Required. Local controls.

    Returns:
        Request headers.
    """
    headers = _ops.bearer_headers(
        PROVIDER,
        ENV_NAME,
        scheme=None,
        header_name="xi-api-key",
    )
    return _ops.merge_headers(headers, kwargs.get("headers"))


def _cost(raw_response=None, payload=None):
    """Return ElevenLabs cost metadata.

    Args:
        raw_response: Optional. Provider response.
        payload: Optional. Request payload.

    Returns:
        Normalized cost metadata.
    """
    return _ops.unavailable_cost(
        {"reason": "ElevenLabs stem separation cost is not exposed per response."}
    )
