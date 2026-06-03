from ..._common import operation_utils as _ops

PROVIDER = "stability"
ENV_NAME = "STABILITY_API_KEY"
DEFAULT_MODEL = "stable-audio-2.5"


def edit_music(audio, prompt=None, output_path=None, sync=True, **kwargs):
    """Edit or inpaint music with Stability Stable Audio.

    Args:
        audio: Required. Source music audio.
        prompt: Optional. Edit, continuation, or inpainting instruction.
        output_path: Optional. Destination path. Downloads only when a final URL
            or direct audio body is returned.
        sync: Optional. Accepted for dispatcher consistency.
        **kwargs: Optional. Provider-native payload fields and local controls.

    Returns:
        A normalized music result.
    """
    model = _ops.resolve_model(kwargs, DEFAULT_MODEL)
    payload = _build_payload(audio, prompt=prompt, **kwargs)
    endpoint = _ops.resolve_endpoint(kwargs)
    headers = _ops.bearer_headers(PROVIDER, ENV_NAME)
    headers = _ops.merge_headers(headers, kwargs.get("headers"))
    raw_response = _ops.post_json(
        endpoint,
        headers=headers,
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
        metadata=_ops.provider_metadata(
            raw_response,
            audio,
            extra={"edit_flow": "stable_audio_temporal_edit"},
        ),
        download_timeout=kwargs.get("download_timeout", 60),
    )


def _build_payload(audio, prompt=None, **kwargs):
    """Build the Stability edit payload.

    Args:
        audio: Required. Source music audio.
        prompt: Optional. Edit prompt.
        **kwargs: Optional. Provider-native payload fields.

    Returns:
        A provider payload dictionary.
    """
    payload = _ops.forwarded_payload(kwargs)
    model = _ops.resolve_model(kwargs, DEFAULT_MODEL)
    if model is not None:
        payload.setdefault("model", model)
    _ops.add_prompt(payload, prompt)
    _ops.add_audio_input(
        payload,
        audio,
        url_key=None,
        base64_key=None,
        data_uri_key=None,
        generic_key="audio",
    )
    return payload


def _cost(raw_response=None, payload=None):
    """Return Stability cost metadata.

    Args:
        raw_response: Optional. Provider response.
        payload: Optional. Request payload.

    Returns:
        Normalized cost metadata.
    """
    return _ops.unavailable_cost(
        {"reason": "Stable Audio responses do not expose per-request cost."}
    )
