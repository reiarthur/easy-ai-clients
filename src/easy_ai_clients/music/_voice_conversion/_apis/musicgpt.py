from ..._common import operation_utils as _ops

PROVIDER = "musicgpt"
ENV_NAME = "MUSICGPT_API_KEY"
DEFAULT_MODEL = None
DEFAULT_ENDPOINT = "https://api.musicgpt.com/api/public/v1/MusicAI"
STATUS_ENDPOINT = "https://api.musicgpt.com/api/public/v1/byId"
VOICE_WARNING = (
    "Voice consent and rights are the caller's responsibility; this client does "
    "not enforce provider policy locally."
)


def convert_voice(audio, voice=None, prompt=None, output_path=None, sync=True, **kwargs):
    """Convert or apply a voice through MusicGPT MusicAI.

    Args:
        audio: Required. Source vocal or music audio.
        voice: Optional. `voice_id`, singer, or custom voice reference.
        prompt: Optional. Style or conversion instruction.
        output_path: Optional. Destination path for a final URL.
        sync: Optional. Accepted for dispatcher consistency.
        **kwargs: Optional. Provider-native MusicAI fields.

    Returns:
        A normalized music audio result.
    """
    model = _ops.resolve_model(kwargs, DEFAULT_MODEL)
    payload = _build_payload(audio, voice=voice, prompt=prompt, **kwargs)
    endpoint = _ops.resolve_endpoint(kwargs, default_endpoint=DEFAULT_ENDPOINT)
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
            extra={"voice": voice, "conversion_flow": "musicai_voice"},
        ),
        warnings=[VOICE_WARNING],
        download_timeout=kwargs.get("download_timeout", 60),
    )


def get_generation_status(request_id, **kwargs):
    """Get MusicGPT voice task status through a supplied status endpoint.

    Args:
        request_id: Required. MusicGPT task ID.
        **kwargs: Optional. Must include `status_endpoint`.

    Returns:
        A normalized music result.
    """
    endpoint = kwargs.get("status_endpoint") or STATUS_ENDPOINT
    raw_response = _ops.get_json(
        endpoint,
        headers=_headers(kwargs),
        params=kwargs.get("params") or {
            "conversionType": "MUSIC_AI",
            "task_id": request_id,
        },
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
        request_kwargs=kwargs.get("request_kwargs"),
    )
    return _ops.result(PROVIDER, _ops.resolve_model(kwargs), raw_response, cost=_cost(raw_response))


def get_generation_result(request_id, output_path=None, **kwargs):
    """Get MusicGPT voice task result.

    Args:
        request_id: Required. MusicGPT task ID.
        output_path: Optional. Destination path.
        **kwargs: Optional. Must include `result_endpoint` or `status_endpoint`.

    Returns:
        A normalized music result.
    """
    endpoint = _ops.resolve_endpoint(
        {"endpoint": kwargs.get("result_endpoint") or kwargs.get("status_endpoint") or STATUS_ENDPOINT}
    )
    raw_response = _ops.get_json(
        endpoint,
        headers=_headers(kwargs),
        params=kwargs.get("params") or {
            "conversionType": "MUSIC_AI",
            "task_id": request_id,
        },
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
        request_kwargs=kwargs.get("request_kwargs"),
    )
    return _ops.result(
        PROVIDER,
        _ops.resolve_model(kwargs),
        raw_response,
        output_path=output_path,
        cost=_cost(raw_response),
        warnings=[VOICE_WARNING],
        download_timeout=kwargs.get("download_timeout", 60),
    )


def download_generation(request_id, output_path=None, **kwargs):
    """Download a completed MusicGPT voice task result.

    Args:
        request_id: Required. MusicGPT task ID.
        output_path: Optional. Destination path.
        **kwargs: Optional. Result endpoint controls.

    Returns:
        A normalized music result.
    """
    return get_generation_result(request_id, output_path=output_path, **kwargs)


def _build_payload(audio, voice=None, prompt=None, **kwargs):
    """Build the MusicGPT voice conversion payload.

    Args:
        audio: Required. Source audio.
        voice: Optional. Voice ID or custom voice reference.
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
    """Build MusicGPT headers.

    Args:
        kwargs: Required. Local controls.

    Returns:
        Request headers.
    """
    headers = _ops.bearer_headers(PROVIDER, ENV_NAME, scheme=None)
    return _ops.merge_headers(headers, kwargs.get("headers"))


def _cost(raw_response=None, payload=None):
    """Return MusicGPT cost metadata.

    Args:
        raw_response: Optional. Provider response.
        payload: Optional. Request payload.

    Returns:
        Normalized cost metadata.
    """
    return _ops.unavailable_cost(
        {"reason": "MusicGPT voice cost depends on feature, plan, and duration blocks."}
    )
