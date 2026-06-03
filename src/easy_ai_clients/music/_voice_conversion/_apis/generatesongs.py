from ..._common import operation_utils as _ops

PROVIDER = "generatesongs"
ENV_NAME = "GENERATESONGS_API_KEY"
DEFAULT_MODEL = None
BASE_URL = "https://generatesongs.ai/api/v1"
GENERATE_ENDPOINT_PATH = "/songs/generate"
STATUS_ENDPOINT_PATH = "/songs/{song_id}"
VOICE_WARNING = (
    "Voice consent and rights are the caller's responsibility; this client does "
    "not enforce provider policy locally."
)


def convert_voice(audio, voice=None, prompt=None, output_path=None, sync=True, **kwargs):
    """Generate or cover a song with GenerateSongs vocal reference fields.

    Args:
        audio: Required. Vocal file ID, source file ID, or uploaded vocal
            reference identifier.
        voice: Optional. Voice, singer, or `vocalFileId` override.
        prompt: Optional. Style prompt.
        output_path: Optional. Destination path for `downloadUrl`.
        sync: Optional. Poll song status when a song ID is returned.
        **kwargs: Optional. Provider-native song generation fields.

    Returns:
        A normalized music audio result.
    """
    model = _ops.resolve_model(kwargs, DEFAULT_MODEL)
    payload = _build_payload(audio, voice=voice, prompt=prompt, **kwargs)
    endpoint = _ops.resolve_endpoint(
        kwargs,
        base_url=BASE_URL,
        path=GENERATE_ENDPOINT_PATH,
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
            extra={"voice": voice, "conversion_flow": "vocal_file_song_generation"},
        ),
        warnings=[VOICE_WARNING],
        download_timeout=kwargs.get("download_timeout", 60),
    )


def get_generation_status(request_id, **kwargs):
    """Get GenerateSongs song status.

    Args:
        request_id: Required. GenerateSongs `songId`.
        **kwargs: Optional. Local request controls.

    Returns:
        A normalized music result.
    """
    raw_response = _request_status(request_id, **kwargs)
    return _ops.result(
        PROVIDER,
        _ops.resolve_model(kwargs),
        raw_response,
        cost=_cost(raw_response),
        warnings=[VOICE_WARNING],
    )


def get_generation_result(request_id, output_path=None, **kwargs):
    """Get GenerateSongs completed song result.

    Args:
        request_id: Required. GenerateSongs `songId`.
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
        warnings=[VOICE_WARNING],
        download_timeout=kwargs.get("download_timeout", 60),
    )


def download_generation(request_id, output_path=None, **kwargs):
    """Download a completed GenerateSongs result.

    Args:
        request_id: Required. GenerateSongs `songId`.
        output_path: Optional. Destination path.
        **kwargs: Optional. Local request controls.

    Returns:
        A normalized music result.
    """
    return get_generation_result(request_id, output_path=output_path, **kwargs)


def _build_payload(audio, voice=None, prompt=None, **kwargs):
    """Build the GenerateSongs voice-oriented song payload.

    Args:
        audio: Required. Vocal file ID or source reference.
        voice: Optional. Voice or vocal file ID override.
        prompt: Optional. Style prompt.
        **kwargs: Optional. Provider-native fields.

    Returns:
        A provider payload dictionary.
    """
    payload = _ops.forwarded_payload(kwargs)
    if prompt is not None:
        payload.setdefault("style", prompt)
    if isinstance(voice, str) and voice.lower() in ("male", "female"):
        payload.setdefault("vocalGender", voice.lower())
    elif voice is not None and "vocalFileId" not in payload and "vocal_file_id" not in payload:
        payload.setdefault("vocalFileId", voice)
    if "vocalFileId" not in payload and "vocal_file_id" not in payload:
        payload.setdefault("vocalFileId", audio)
    return payload


def _headers(kwargs):
    """Build GenerateSongs headers.

    Args:
        kwargs: Required. Local controls.

    Returns:
        Request headers.
    """
    headers = _ops.bearer_headers(PROVIDER, ENV_NAME)
    return _ops.merge_headers(headers, kwargs.get("headers"))


def _request_status(song_id, **kwargs):
    """Request raw GenerateSongs song status.

    Args:
        song_id: Required. GenerateSongs song ID.
        **kwargs: Optional. Local request controls.

    Returns:
        Raw provider response.
    """
    path = kwargs.get("status_endpoint_path") or STATUS_ENDPOINT_PATH.format(
        song_id=song_id
    )
    endpoint = _ops.resolve_endpoint(
        {"endpoint": kwargs.get("status_endpoint"), "base_url": kwargs.get("base_url")},
        base_url=BASE_URL,
        path=path,
    )
    return _ops.get_json(
        endpoint,
        headers=_headers(kwargs),
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
        request_kwargs=kwargs.get("request_kwargs"),
    )


def _cost(raw_response=None, payload=None):
    """Return GenerateSongs cost metadata.

    Args:
        raw_response: Optional. Provider response.
        payload: Optional. Request payload.

    Returns:
        Normalized cost metadata.
    """
    return _ops.unavailable_cost(
        {"credits": 1, "reason": "USD cost depends on credit package or plan."}
    )
