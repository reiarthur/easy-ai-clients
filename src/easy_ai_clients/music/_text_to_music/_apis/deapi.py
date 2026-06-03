from ..._common import cost_utils, env_utils, http_utils, media_utils, result_utils
from .. import post_processing, pre_processing

PROVIDER = "deapi"
ENV_NAME = "DEAPI_API_KEY"
DEFAULT_MODEL = "ACE-Step-v1.5-turbo"
COST_SOURCE = "deapi_price_calculation_endpoint"


def _selected_model(kwargs):
    return pre_processing.selected_model(kwargs, DEFAULT_MODEL)


def _build_payload(model, prepared, kwargs):
    payload = dict(prepared)
    payload.setdefault("caption", payload.pop("prompt", None))
    payload.setdefault("model", model)
    payload.setdefault("lyrics", "[Instrumental]")
    payload.setdefault("duration", 30)
    payload.setdefault("inference_steps", 8)
    payload.setdefault("guidance_scale", 7)
    payload.setdefault("seed", -1)
    payload.setdefault("format", "mp3")
    return pre_processing.compact_payload(payload)


def _cost(model, kwargs):
    return cost_utils.unavailable_cost_metadata(
        source=COST_SOURCE,
        details={
            "model": model,
            "duration": kwargs.get("duration"),
            "inference_steps": kwargs.get("inference_steps"),
        },
    )


def update_cost(result, **kwargs):
    """Refresh deAPI cost metadata with the documented price endpoint.

    Args:
        result: Required. Normalized result dictionary.
        **kwargs: Optional. Dispatcher compatibility values.

    Returns:
        The updated result dictionary.
    """
    details = _cost_lookup_details(result)
    payload = {
        "model": details.get("model") or DEFAULT_MODEL,
        "duration": details.get("duration") or 30,
        "inference_steps": details.get("inference_steps") or 8,
    }
    try:
        response = http_utils.request_json(
            "POST",
            f"{_base_url(kwargs)}/api/v2/audio/music/price",
            headers=_headers(),
            json=payload,
            **pre_processing.http_options(kwargs),
        )
        price = _price_from_response(response)
        cost = cost_utils.normalize_cost(
            price,
            source="provider_response",
            is_estimated=True,
            details={
                "price_endpoint": "/api/v2/audio/music/price",
                **payload,
            },
        )
    except Exception:
        cost = cost_utils.unavailable_cost_metadata()
    return cost_utils.apply_cost_metadata(result, cost)


def generate_text_to_music(prompt, output_path=None, sync=True, **kwargs):
    options = dict(kwargs)
    model = _selected_model(options)
    prepared = pre_processing.prepared_prompt(prompt, options)
    payload = _build_payload(model, prepared, options)
    cost = _cost(model, payload)

    try:
        data, files = _multipart_payload(payload)
        response = http_utils.multipart_request(
            "POST",
            f"{_base_url(options)}/api/v2/audio/music",
            files=files,
            headers=_headers(),
            data=data,
            **pre_processing.http_options(options),
        )
        raw_response = http_utils.response_json(response)
        request_id = result_utils.extract_request_id(raw_response)
        refs = _refs(request_id, options, raw_response)
        if not sync or post_processing.collect_audio_candidates(raw_response):
            return post_processing.normalize_response(
                PROVIDER,
                model,
                raw_response,
                output_path=output_path,
                cost=cost,
                status=None if post_processing.collect_audio_candidates(raw_response) else "submitted",
                refs=refs,
                request_id=request_id,
                download_timeout=options.get("download_timeout", 60),
            )

        final_response = _poll_request(request_id, raw_response, options)
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
            _status_url(request_id, options),
            headers=_headers(),
            **pre_processing.http_options(options),
        )
        return post_processing.normalize_response(
            PROVIDER,
            model,
            response,
            output_path=output_path,
            refs=_refs(request_id, options, response),
            request_id=request_id,
            download_timeout=options.get("download_timeout", 60),
        )
    except Exception as exc:
        return _failure(model, exc, request_id=request_id, output_path=output_path)


def _multipart_payload(payload):
    payload = dict(payload)
    reference_audio = payload.pop("reference_audio", None)
    files = {}
    if reference_audio is not None:
        if media_utils.is_remote_url(reference_audio) or media_utils.is_data_uri(reference_audio):
            payload["reference_audio"] = reference_audio
        else:
            files["reference_audio"] = (
                media_utils.infer_filename(reference_audio),
                media_utils.read_media_bytes(reference_audio),
                media_utils.infer_mime_type(reference_audio),
            )
    return payload, files


def _poll_request(request_id, response, kwargs):
    if not request_id:
        return response
    return post_processing.poll_until_ready(
        lambda: http_utils.request_json(
            "GET",
            _status_url(request_id, kwargs),
            headers=_headers(),
            **pre_processing.http_options(kwargs),
        ),
        **pre_processing.poll_options(kwargs),
    )


def _headers():
    key = env_utils.require_env_var(ENV_NAME)
    return {
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    }


def _base_url(kwargs):
    return kwargs.get("base_url", "https://api.deapi.ai").rstrip("/")


def _status_url(request_id, kwargs):
    return kwargs.get("status_url") or f"{_base_url(kwargs)}/api/v2/jobs/{request_id}"


def _refs(request_id, kwargs, response):
    refs = {"result_url": response.get("result_url") if isinstance(response, dict) else None}
    if request_id:
        refs["status_url"] = _status_url(request_id, kwargs)
    return refs


def _cost_lookup_details(result):
    """Return deAPI price calculation fields from a result.

    Args:
        result: Required. Normalized result dictionary.

    Returns:
        Cost lookup details.
    """
    details = {}
    if isinstance(result, dict):
        details.update(result.get("cost_details") or {})
        if result.get("model") is not None:
            details.setdefault("model", result["model"])
    return details


def _price_from_response(response):
    """Extract deAPI price from a price calculation response.

    Args:
        response: Required. Provider response.

    Returns:
        The price value.
    """
    if isinstance(response, dict):
        data = response.get("data")
        if isinstance(data, dict) and data.get("price") is not None:
            return data["price"]
        if response.get("price") is not None:
            return response["price"]
    raise RuntimeError("deAPI price calculation response did not include data.price.")


def _failure(model, exc, request_id=None, output_path=None):
    return result_utils.failure_result(
        provider=PROVIDER,
        model=model,
        operation="text_to_music",
        exc=exc,
        request_id=request_id,
        output_path=output_path,
    )
