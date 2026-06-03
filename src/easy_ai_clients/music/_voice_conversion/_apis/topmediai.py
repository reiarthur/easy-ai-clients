from ..._common import operation_utils as _ops

PROVIDER = "topmediai"
ENV_NAME = "TOPMEDIAI_API_KEY"
DEFAULT_MODEL = "v4.5-plus"
VOICE_ENDPOINT_PATH = "/v3/music/generate-singer"
STATUS_ENDPOINT_PATH = "/v3/music/tasks"
BASE_URL = "https://api.topmediai.com"
VOICE_WARNING = (
    "Voice consent and rights are the caller's responsibility; this client does "
    "not enforce provider policy locally."
)


def convert_voice(audio, voice=None, prompt=None, output_path=None, sync=True, **kwargs):
    """Run a TopMediai singer or voice conversion flow.

    Args:
        audio: Required. Source audio URL or song/task reference.
        voice: Optional. Singer ID, gender, or voice reference.
        prompt: Optional. Style or conversion instruction.
        output_path: Optional. Destination path for a final URL.
        sync: Optional. Accepted for dispatcher consistency.
        **kwargs: Optional. Provider-native v3 singer fields.

    Returns:
        A normalized music audio result.
    """
    model = _ops.resolve_model(kwargs, DEFAULT_MODEL)
    payload = _build_payload(audio, voice=voice, prompt=prompt, **kwargs)
    endpoint = _ops.resolve_endpoint(kwargs, base_url=BASE_URL, path=VOICE_ENDPOINT_PATH)
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
            extra={"voice": voice, "conversion_flow": "generate_singer"},
        ),
        warnings=[VOICE_WARNING],
        download_timeout=kwargs.get("download_timeout", 60),
    )


def get_generation_status(request_id, **kwargs):
    """Get TopMediai voice task status.

    Args:
        request_id: Required. TopMediai task ID.
        **kwargs: Optional. Requires `base_url` unless `status_endpoint` is full.

    Returns:
        A normalized music result.
    """
    endpoint = _ops.resolve_endpoint(
        {"endpoint": kwargs.get("status_endpoint"), "base_url": kwargs.get("base_url")},
        base_url=BASE_URL,
        path=STATUS_ENDPOINT_PATH,
    )
    raw_response = _ops.get_json(
        endpoint,
        headers=_headers(kwargs),
        params=kwargs.get("params") or {"ids": request_id},
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
        request_kwargs=kwargs.get("request_kwargs"),
    )
    return _ops.result(
        PROVIDER,
        _ops.resolve_model(kwargs, DEFAULT_MODEL),
        raw_response,
        cost=_cost(raw_response),
        warnings=[VOICE_WARNING],
    )


def get_generation_result(request_id, output_path=None, **kwargs):
    """Get TopMediai voice task result.

    Args:
        request_id: Required. TopMediai task ID.
        output_path: Optional. Destination path.
        **kwargs: Optional. Status endpoint controls.

    Returns:
        A normalized music result.
    """
    status = get_generation_status(request_id, **kwargs)
    return _ops.result(
        PROVIDER,
        status.get("model"),
        status.get("raw_response"),
        output_path=output_path,
        cost=_cost(status.get("raw_response")),
        warnings=[VOICE_WARNING],
        download_timeout=kwargs.get("download_timeout", 60),
    )


def download_generation(request_id, output_path=None, **kwargs):
    """Download a completed TopMediai voice task result.

    Args:
        request_id: Required. TopMediai task ID.
        output_path: Optional. Destination path.
        **kwargs: Optional. Status endpoint controls.

    Returns:
        A normalized music result.
    """
    return get_generation_result(request_id, output_path=output_path, **kwargs)


def _build_payload(audio, voice=None, prompt=None, **kwargs):
    """Build the TopMediai voice conversion payload.

    Args:
        audio: Required. Source audio or task reference.
        voice: Optional. Singer ID, gender, or voice reference.
        prompt: Optional. Style or instruction.
        **kwargs: Optional. Provider-native v3 fields.

    Returns:
        A provider payload dictionary.
    """
    payload = _ops.forwarded_payload(kwargs)
    model = _ops.resolve_model(kwargs, DEFAULT_MODEL)
    if model is not None:
        payload.setdefault("mv", model)
    _ops.add_prompt(payload, prompt)
    if voice is not None:
        payload.setdefault("singer_id", voice)
    _ops.add_audio_input(payload, audio, url_key="audio_url", generic_key="audio_url")
    return payload


def _headers(kwargs):
    """Build TopMediai headers.

    Args:
        kwargs: Required. Local controls.

    Returns:
        Request headers.
    """
    headers = _ops.bearer_headers(
        PROVIDER,
        ENV_NAME,
        scheme=None,
        header_name="x-api-key",
    )
    return _ops.merge_headers(headers, kwargs.get("headers"))


def _cost(raw_response=None, payload=None):
    """Return TopMediai cost metadata.

    Args:
        raw_response: Optional. Provider response.
        payload: Optional. Request payload.

    Returns:
        Normalized cost metadata.
    """
    return _ops.unavailable_cost(
        {"reason": "TopMediai cost is credit-based and plan dependent."}
    )
