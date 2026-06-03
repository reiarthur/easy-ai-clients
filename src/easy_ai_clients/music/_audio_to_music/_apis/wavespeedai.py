from ..._common import cost_utils, env_utils, http_utils
from ..post_processing import build_result, wait_for_result
from ..pre_processing import apply_audio_reference, prepare_audio_to_music, without_internal_kwargs

PROVIDER = "wavespeedai"
ENV_NAME = "WAVESPEEDAI_API_KEY"
DEFAULT_MODEL = "wavespeed-ai/song-generation"
DEFAULT_ENDPOINT = "https://api.wavespeed.ai/api/v3/wavespeed-ai/song-generation"
DEFAULT_RESULT_ENDPOINT = "https://api.wavespeed.ai/api/v3/predictions/{request_id}/result"


def generate_audio_to_music(audio, prompt=None, output_path=None, sync=True, **kwargs):
    """Submit a WaveSpeedAI song generation request with prompt audio."""
    model = kwargs.pop("model", DEFAULT_MODEL)
    endpoint = kwargs.pop("endpoint", DEFAULT_ENDPOINT)
    timeout = kwargs.pop("timeout", 60)
    retries = kwargs.pop("retries", 2)
    payload = _build_payload(audio, prompt=prompt, model=model, **kwargs)
    raw_response = http_utils.request_json(
        "POST",
        endpoint,
        headers=_headers(),
        json=payload,
        timeout=timeout,
        retries=retries,
    )
    request_id = _request_id(raw_response)
    if not sync or not request_id:
        return build_result(
            PROVIDER,
            model,
            raw_response,
            output_path=output_path,
            status="submitted" if request_id else None,
            request_id=request_id,
            cost=_cost(model=model),
        )

    final_response = wait_for_result(
        lambda: get_generation_result(request_id, model=model, timeout=timeout, retries=retries),
        max_wait_seconds=kwargs.get("max_wait_seconds", 600),
        poll_interval=kwargs.get("poll_interval", 5),
        completed_statuses=("completed",),
    )
    return build_result(PROVIDER, model, final_response, output_path=output_path, cost=_cost(model=model))


def get_generation_status(request_id, model=None, **kwargs):
    """Fetch WaveSpeedAI prediction status/result."""
    endpoint = kwargs.get("result_endpoint", DEFAULT_RESULT_ENDPOINT).format(request_id=request_id)
    return http_utils.request_json(
        "GET",
        endpoint,
        headers=_headers(),
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
    )


def get_generation_result(request_id, output_path=None, model=None, **kwargs):
    """Fetch WaveSpeedAI prediction result."""
    response = get_generation_status(request_id, model=model, **kwargs)
    return build_result(PROVIDER, model or DEFAULT_MODEL, response, output_path=output_path)


def _build_payload(audio, prompt=None, model=None, **kwargs):
    """Build the WaveSpeedAI song-generation payload."""
    prepare_audio_to_music(audio, prompt=prompt)
    payload = without_internal_kwargs(kwargs)
    lyric = kwargs.get("lyric") or kwargs.get("lyrics")
    if lyric is None:
        lyric = prompt or ""
    payload.pop("lyrics", None)
    payload.setdefault("lyric", lyric)
    if prompt is not None and "description" not in payload and lyric != prompt:
        payload["description"] = prompt
    apply_audio_reference(
        payload,
        audio,
        url_field=kwargs.get("url_field", "prompt_audio"),
        data_uri_field=kwargs.get("data_uri_field", "prompt_audio"),
        file_id_field=kwargs.get("file_id_field"),
        prefer=kwargs.get("audio_format"),
        mime_type=kwargs.get("mime_type"),
    )
    return payload


def _cost(model=None, **kwargs):
    """Return estimated WaveSpeedAI starting cost metadata."""
    return cost_utils.normalize_cost(
        0.05,
        source="official_pricing_table",
        is_estimated=True,
        details={"model": model, "starting_price_usd": 0.05, **kwargs},
    )


def update_cost(result, **kwargs):
    """Refresh WaveSpeedAI cost metadata from documented starting price.

    Args:
        result: Required. Normalized result dictionary.
        **kwargs: Optional. Dispatcher compatibility values.

    Returns:
        The updated result dictionary.
    """
    model = result.get("model") if isinstance(result, dict) else None
    cost = _cost(model or DEFAULT_MODEL)
    return cost_utils.apply_cost_metadata(result, cost)


def _headers():
    api_key = env_utils.require_env_var(ENV_NAME)
    return {"Authorization": f"Bearer {api_key}"}


def _request_id(response):
    if isinstance(response, dict):
        data = response.get("data")
        nested_id = data.get("id") if isinstance(data, dict) else None
        return response.get("id") or response.get("request_id") or response.get("requestId") or nested_id
    return None
