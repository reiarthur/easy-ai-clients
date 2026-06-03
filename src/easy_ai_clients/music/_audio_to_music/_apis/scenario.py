from ..._common import cost_utils, env_utils, http_utils, result_utils
from ..post_processing import build_result, wait_for_result
from ..pre_processing import (
    add_prompt,
    apply_audio_reference,
    prepare_audio_to_music,
    without_internal_kwargs,
)

PROVIDER = "scenario"
ENV_NAME = "SCENARIO_API_KEY"
SECRET_ENV_NAME = "SCENARIO_API_SECRET"
ENV_NAMES = (ENV_NAME, SECRET_ENV_NAME)
DEFAULT_MODEL = "stereo-melody-large"
DEFAULT_MODEL_ID = "model_meta-musicgen"
DEFAULT_ENDPOINT = "https://api.cloud.scenario.com/v1/generate/custom/{model_id}"


def generate_audio_to_music(audio, prompt=None, output_path=None, sync=True, **kwargs):
    """Submit a Scenario Meta MusicGen audio task."""
    model = kwargs.pop("model", DEFAULT_MODEL)
    endpoint = _endpoint(kwargs)
    timeout = kwargs.pop("timeout", 60)
    retries = kwargs.pop("retries", 2)
    payload = _build_payload(audio, prompt=prompt, model=model, **kwargs)
    raw_response = http_utils.request_json(
        "POST",
        endpoint,
        auth=_auth(),
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
        lambda: get_generation_result(
            request_id,
            model=model,
            timeout=timeout,
            retries=retries,
        ),
        max_wait_seconds=kwargs.get("max_wait_seconds", 600),
        poll_interval=kwargs.get("poll_interval", 5),
    )
    return build_result(PROVIDER, model, final_response, output_path=output_path, cost=_cost(model=model))


def get_generation_status(request_id, model=None, **kwargs):
    """Fetch Scenario job status."""
    endpoint = _format_endpoint(kwargs.get("status_endpoint"), request_id)
    endpoint = endpoint or _job_url(request_id, kwargs)
    return http_utils.request_json(
        "GET",
        endpoint,
        auth=_auth(),
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
    )


def get_generation_result(request_id, output_path=None, model=None, **kwargs):
    """Fetch Scenario result and resolve the first generated asset URL."""
    response = get_generation_status(request_id, model=model, **kwargs)
    response = _with_asset_url(response, kwargs)
    return build_result(PROVIDER, model or DEFAULT_MODEL, response, output_path=output_path)


def _build_payload(audio, prompt=None, model=None, **kwargs):
    """Build the Scenario custom generation payload."""
    prepare_audio_to_music(audio, prompt=prompt)
    payload = without_internal_kwargs(kwargs)
    payload.setdefault("modelVersion", model or DEFAULT_MODEL)
    add_prompt(payload, prompt, field_name=kwargs.get("prompt_field", "prompt"))
    apply_audio_reference(
        payload,
        audio,
        url_field=kwargs.get("url_field", "inputAudio"),
        data_uri_field=kwargs.get("data_uri_field", "inputAudio"),
        file_id_field=kwargs.get("file_id_field", "inputAudio"),
        prefer=kwargs.get("audio_format"),
        mime_type=kwargs.get("mime_type"),
    )
    return payload


def _cost(model=None, **kwargs):
    """Return unavailable Scenario cost metadata."""
    return cost_utils.unavailable_cost_metadata(
        source="scenario_pricing_endpoint",
        details={"model": model, **kwargs},
    )


def _endpoint(kwargs):
    endpoint = kwargs.pop("endpoint", None)
    if endpoint:
        return endpoint
    model_id = kwargs.pop("model_id", DEFAULT_MODEL_ID)
    return DEFAULT_ENDPOINT.format(model_id=model_id)


def _base_url(kwargs):
    return kwargs.get("base_url", "https://api.cloud.scenario.com").rstrip("/")


def _job_url(request_id, kwargs):
    return kwargs.get("status_url") or f"{_base_url(kwargs)}/v1/jobs/{request_id}"


def _asset_url(asset_id, kwargs):
    return kwargs.get("asset_url") or f"{_base_url(kwargs)}/v1/assets/{asset_id}"


def _with_asset_url(response, kwargs):
    if not isinstance(response, dict):
        return response
    asset_id = _asset_id(response)
    if not asset_id or result_utils.extract_audio_url(response):
        return response
    asset_response = http_utils.request_json(
        "GET",
        _asset_url(asset_id, kwargs),
        auth=_auth(),
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
    )
    audio_url = result_utils.extract_audio_url(asset_response)
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


def _auth():
    values = env_utils.require_env_vars(PROVIDER)
    return values[ENV_NAME], values[SECRET_ENV_NAME]


def _request_id(response):
    if isinstance(response, dict):
        return response.get("job_id") or response.get("jobId") or response.get("id")
    return None


def _format_endpoint(endpoint, request_id):
    if not endpoint:
        return None
    return endpoint.format(job_id=request_id, request_id=request_id, id=request_id)
