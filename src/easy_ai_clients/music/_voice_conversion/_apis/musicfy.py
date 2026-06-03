from ..._common import operation_utils as _ops

PROVIDER = "musicfy"
ENV_NAME = "MUSICFY_API_KEY"
DEFAULT_MODEL = None
VOICE_WARNING = (
    "Voice consent and rights are the caller's responsibility; this client does "
    "not enforce provider policy locally."
)


def convert_voice(audio, voice=None, prompt=None, output_path=None, sync=True, **kwargs):
    """Convert a singing voice with Musicfy.

    Args:
        audio: Required. Source vocal or music audio.
        voice: Optional. Voice ID, singer, or reference voice identifier.
        prompt: Optional. Style or conversion instruction.
        output_path: Optional. Destination path for a final URL.
        sync: Optional. Accepted for dispatcher consistency.
        **kwargs: Optional. Provider-native conversion fields. Include
            `endpoint` when using a Musicfy flow without a wrapper default.

    Returns:
        A normalized music audio result.
    """
    model = _ops.resolve_model(kwargs, DEFAULT_MODEL)
    payload = _build_payload(audio, voice=voice, prompt=prompt, **kwargs)
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
        metadata=_ops.provider_metadata(
            raw_response,
            audio,
            extra={"voice": voice, "conversion_flow": "voice_conversion"},
        ),
        warnings=[VOICE_WARNING],
        download_timeout=kwargs.get("download_timeout", 60),
    )


def _build_payload(audio, voice=None, prompt=None, **kwargs):
    """Build the Musicfy voice conversion payload.

    Args:
        audio: Required. Source vocal or music audio.
        voice: Optional. Voice ID, singer, or reference.
        prompt: Optional. Style or instruction.
        **kwargs: Optional. Provider-native fields.

    Returns:
        A provider payload dictionary.
    """
    payload = _ops.forwarded_payload(kwargs)
    _ops.add_prompt(payload, prompt)
    if voice is not None:
        payload.setdefault("voice_id", voice)
    _ops.add_audio_input(payload, audio, url_key="audio_url", generic_key="audio")
    return payload


def _headers(kwargs):
    """Build Musicfy headers.

    Args:
        kwargs: Required. Local controls.

    Returns:
        Request headers.
    """
    headers = _ops.bearer_headers(PROVIDER, ENV_NAME)
    return _ops.merge_headers(headers, kwargs.get("headers"))


def _cost(raw_response=None, payload=None):
    """Return Musicfy cost metadata.

    Args:
        raw_response: Optional. Provider response.
        payload: Optional. Request payload.

    Returns:
        Normalized cost metadata.
    """
    return _ops.unavailable_cost(
        {"reason": "Musicfy cost depends on converted minutes and account plan."}
    )
