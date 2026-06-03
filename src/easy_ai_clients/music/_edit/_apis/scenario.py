from ..._common import operation_utils as _ops

PROVIDER = "scenario"
ENV_NAME = "SCENARIO_API_KEY"
SECRET_ENV_NAME = "SCENARIO_API_SECRET"
ENV_NAMES = (ENV_NAME, SECRET_ENV_NAME)
DEFAULT_MODEL = "model_meta-musicgen"
DEFAULT_MODEL_VERSION = "melody-large"
DEFAULT_ENDPOINT = "https://api.cloud.scenario.com/v1/generate/custom/{model_id}"


def edit_music(audio, prompt=None, output_path=None, sync=True, **kwargs):
    """Create a Scenario Meta MusicGen continuation job.

    Args:
        audio: Required. Input audio for melody or continuation.
        prompt: Optional. Prompt for the generated clip.
        output_path: Optional. Destination path for a final asset URL.
        sync: Optional. Accepted for dispatcher consistency.
        **kwargs: Optional. Provider-native Scenario generation fields.

    Returns:
        A normalized music result.
    """
    model = kwargs.get("modelId") or kwargs.get("model_id") or DEFAULT_MODEL
    payload = _build_payload(audio, prompt=prompt, **kwargs)
    endpoint = kwargs.get("endpoint") or DEFAULT_ENDPOINT.format(model_id=model)
    raw_response = _ops.post_json(
        endpoint,
        headers=_ops.merge_headers({}, kwargs.get("headers")),
        payload=payload,
        params=kwargs.get("params"),
        auth=_ops.basic_auth(PROVIDER),
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
            extra={"edit_flow": "musicgen_continuation_asset"},
        ),
        download_timeout=kwargs.get("download_timeout", 60),
    )


def get_generation_status(request_id, **kwargs):
    """Get Scenario job status.

    Args:
        request_id: Required. Scenario job ID.
        **kwargs: Optional. Provider request controls.

    Returns:
        A normalized music result.
    """
    endpoint = kwargs.get("status_endpoint") or _job_url(request_id, kwargs)
    raw_response = _ops.get_json(
        endpoint,
        headers=_ops.merge_headers({}, kwargs.get("headers")),
        params=kwargs.get("params") or {"job_id": request_id},
        auth=_ops.basic_auth(PROVIDER),
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
        request_kwargs=kwargs.get("request_kwargs"),
    )
    return _ops.result(PROVIDER, _ops.resolve_model(kwargs, DEFAULT_MODEL), raw_response, cost=_cost(raw_response))


def get_generation_result(request_id, output_path=None, **kwargs):
    """Get Scenario asset result.

    Args:
        request_id: Required. Scenario job or asset ID.
        output_path: Optional. Destination path.
        **kwargs: Optional. Provider request controls.

    Returns:
        A normalized music result.
    """
    if kwargs.get("result_endpoint"):
        raw_response = _ops.get_json(
            kwargs["result_endpoint"],
            headers=_ops.merge_headers({}, kwargs.get("headers")),
            params=kwargs.get("params") or {"id": request_id},
            auth=_ops.basic_auth(PROVIDER),
            timeout=kwargs.get("timeout", 60),
            retries=kwargs.get("retries", 2),
            request_kwargs=kwargs.get("request_kwargs"),
        )
    else:
        raw_response = _with_asset_url(
            _request_job(request_id, kwargs),
            kwargs,
        )
    return _ops.result(
        PROVIDER,
        _ops.resolve_model(kwargs, DEFAULT_MODEL),
        raw_response,
        output_path=output_path,
        cost=_cost(raw_response),
        download_timeout=kwargs.get("download_timeout", 60),
    )


def download_generation(request_id, output_path=None, **kwargs):
    """Download a completed Scenario asset result.

    Args:
        request_id: Required. Scenario job or asset ID.
        output_path: Optional. Destination path.
        **kwargs: Optional. Result endpoint controls.

    Returns:
        A normalized music result.
    """
    return get_generation_result(request_id, output_path=output_path, **kwargs)


def _build_payload(audio, prompt=None, **kwargs):
    """Build the Scenario Meta MusicGen continuation payload.

    Args:
        audio: Required. Source audio.
        prompt: Optional. Generation prompt.
        **kwargs: Optional. Provider-native generation fields.

    Returns:
        A provider payload dictionary.
    """
    payload = _ops.forwarded_payload(kwargs, exclude=("model", "model_id", "modelId"))
    payload.setdefault("modelVersion", kwargs.get("modelVersion", DEFAULT_MODEL_VERSION))
    payload.setdefault("continuation", True)
    _ops.add_prompt(payload, prompt)
    _ops.add_audio_input(payload, audio, url_key="inputAudio", generic_key="inputAudio")
    return payload


def _cost(raw_response=None, payload=None):
    """Return Scenario cost metadata.

    Args:
        raw_response: Optional. Provider response.
        payload: Optional. Request payload.

    Returns:
        Normalized cost metadata.
    """
    return _ops.unavailable_cost(
        {"reason": "Scenario model price must be fetched from pricing endpoints."}
    )


def _base_url(kwargs):
    return kwargs.get("base_url", "https://api.cloud.scenario.com").rstrip("/")


def _job_url(request_id, kwargs):
    return kwargs.get("status_url") or f"{_base_url(kwargs)}/v1/jobs/{request_id}"


def _asset_url(asset_id, kwargs):
    return kwargs.get("asset_url") or f"{_base_url(kwargs)}/v1/assets/{asset_id}"


def _request_job(request_id, kwargs):
    return _ops.get_json(
        _job_url(request_id, kwargs),
        headers=_ops.merge_headers({}, kwargs.get("headers")),
        auth=_ops.basic_auth(PROVIDER),
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
        request_kwargs=kwargs.get("request_kwargs"),
    )


def _with_asset_url(response, kwargs):
    if not isinstance(response, dict):
        return response
    asset_id = _asset_id(response)
    if not asset_id or _ops.result_utils.extract_audio_url(response):
        return response
    asset_response = _ops.get_json(
        _asset_url(asset_id, kwargs),
        headers=_ops.merge_headers({}, kwargs.get("headers")),
        auth=_ops.basic_auth(PROVIDER),
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
        request_kwargs=kwargs.get("request_kwargs"),
    )
    audio_url = _ops.result_utils.extract_audio_url(asset_response)
    if not audio_url:
        return response
    enriched = dict(response)
    enriched["audio_url"] = audio_url
    enriched["asset"] = asset_response
    return enriched


def _asset_id(response):
    job = response.get("job") if isinstance(response, dict) else None
    metadata = job.get("metadata") if isinstance(job, dict) else None
    asset_ids = metadata.get("assetIds") if isinstance(metadata, dict) else None
    if isinstance(asset_ids, list) and asset_ids:
        return asset_ids[0]
    if isinstance(asset_ids, str):
        return asset_ids
    return None
