from ..._common import cost_utils, env_utils, http_utils, result_utils
from .. import post_processing, pre_processing

PROVIDER = "scenario"
ENV_NAME = "SCENARIO_API_KEY"
SECRET_ENV_NAME = "SCENARIO_API_SECRET"
ENV_NAMES = (ENV_NAME, SECRET_ENV_NAME)
DEFAULT_MODEL = "model_meta-musicgen"
DEFAULT_MODEL_VERSION = "stereo-large"
COST_SOURCE = "scenario_pricing_api"

MODEL_VERSIONS = {
    "stereo-melody-large",
    "stereo-large",
    "melody-large",
    "large",
}


def _selected_model(kwargs):
    model = pre_processing.selected_model(kwargs, DEFAULT_MODEL)
    if str(model) in MODEL_VERSIONS:
        kwargs.setdefault("modelVersion", model)
        return DEFAULT_MODEL
    return model


def _build_payload(model, prepared, kwargs):
    payload = dict(prepared)
    payload.setdefault("duration", 8)
    payload.setdefault("modelVersion", kwargs.get("modelVersion", DEFAULT_MODEL_VERSION))
    return pre_processing.compact_payload(payload)


def _cost(model, kwargs):
    return cost_utils.unavailable_cost_metadata(
        source=COST_SOURCE,
        details={
            "modelId": model,
            "modelVersion": kwargs.get("modelVersion"),
            "duration": kwargs.get("duration"),
        },
    )


def generate_text_to_music(prompt, output_path=None, sync=True, **kwargs):
    options = dict(kwargs)
    model = _selected_model(options)
    prepared = pre_processing.prepared_prompt(prompt, options)
    payload = _build_payload(model, prepared, options)
    cost = _cost(model, payload)

    try:
        response = http_utils.request_json(
            "POST",
            _generation_url(model, options),
            headers={"Content-Type": "application/json"},
            json=payload,
            auth=_auth(),
            **pre_processing.http_options(options),
        )
        request_id = _job_id(response)
        refs = _refs(request_id, options)
        if not sync or post_processing.collect_audio_candidates(response):
            return post_processing.normalize_response(
                PROVIDER,
                model,
                response,
                output_path=output_path,
                cost=cost,
                status=None if post_processing.collect_audio_candidates(response) else "submitted",
                refs=refs,
                request_id=request_id,
                download_timeout=options.get("download_timeout", 60),
            )

        final_response = _with_asset_url(_poll_job(request_id, response, options), options)
        return post_processing.normalize_response(
            PROVIDER,
            model,
            final_response,
            output_path=output_path,
            cost=cost,
            refs=refs,
            request_id=request_id,
            download_timeout=options.get("download_timeout", 60),
        )
    except Exception as exc:
        return _failure(model, exc, output_path=output_path)


def get_generation_status(request_id, **kwargs):
    return get_generation_result(request_id, **kwargs)


def get_generation_result(request_id, **kwargs):
    options = dict(kwargs)
    output_path = options.get("output_path")
    model = _selected_model(options)
    try:
        response = http_utils.request_json(
            "GET",
            _job_url(request_id, options),
            auth=_auth(),
            **pre_processing.http_options(options),
        )
        response = _with_asset_url(response, options)
        return post_processing.normalize_response(
            PROVIDER,
            model,
            response,
            output_path=output_path,
            refs=_refs(request_id, options),
            request_id=request_id,
            download_timeout=options.get("download_timeout", 60),
        )
    except Exception as exc:
        return _failure(model, exc, request_id=request_id, output_path=output_path)


def _poll_job(request_id, response, kwargs):
    if not request_id:
        return response
    return post_processing.poll_until_ready(
        lambda: http_utils.request_json(
            "GET",
            _job_url(request_id, kwargs),
            auth=_auth(),
            **pre_processing.http_options(kwargs),
        ),
        **pre_processing.poll_options(kwargs),
    )


def _auth():
    credentials = env_utils.require_env_vars(PROVIDER)
    return credentials[ENV_NAME], credentials[SECRET_ENV_NAME]


def _base_url(kwargs):
    return kwargs.get("base_url", "https://api.cloud.scenario.com").rstrip("/")


def _generation_url(model, kwargs):
    return (
        kwargs.get("endpoint_url")
        or f"{_base_url(kwargs)}/v1/generate/custom/{str(model).strip('/')}"
    )


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
        **pre_processing.http_options(kwargs),
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


def _refs(request_id, kwargs):
    if not request_id:
        return {}
    url = _job_url(request_id, kwargs)
    return {
        "status_url": url,
        "result_url": url,
    }


def _job_id(response):
    job = response.get("job")
    job_id = job.get("id") if isinstance(job, dict) else None
    return (
        response.get("jobId")
        or response.get("job_id")
        or job_id
        or result_utils.extract_request_id(response)
    )


def _failure(model, exc, request_id=None, output_path=None):
    return result_utils.failure_result(
        provider=PROVIDER,
        model=model,
        operation="text_to_music",
        exc=exc,
        request_id=request_id,
        output_path=output_path,
    )
