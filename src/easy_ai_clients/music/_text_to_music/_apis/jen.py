import math
import time

from ..._common import cost_utils, env_utils, http_utils
from ..post_processing import (
    build_result,
    download_audio,
    estimated_cost,
    failure_result,
    first_audio_url,
    unavailable_cost,
)
from ..pre_processing import (
    add_if_present,
    endpoint_from_base,
    missing_endpoint_error,
    poll_settings,
    prepare_text_to_music,
    request_retries,
    request_timeout,
    safe_payload_kwargs,
    selected_model,
)

PROVIDER = "jen"
ENV_NAME = "JEN_MUSIC_API_KEY"
DEFAULT_MODEL = None
COST_SOURCE = "official_pricing_table"
BASE_URL = "https://app.jenmusic.ai"
GENERATE_PATH = "/api/v3/public/track/generate"
STATUS_PATH = "/api/v3/public/generation_status/{trackid}"
SUCCESS_STATUSES = {"generated"}
FAILURE_STATUSES = {"failed", "failure", "error", "cancelled", "canceled"}


def _selected_model(kwargs):
    """Return the selected Jen model.

    Args:
        kwargs: Required. Provider keyword arguments.

    Returns:
        The selected model, if provided.
    """
    return selected_model(kwargs, DEFAULT_MODEL)


def _build_payload(model, prepared, kwargs):
    """Build the Jen track generation payload.

    Args:
        model: Optional. Jen model.
        prepared: Required. Prepared prompt data.
        kwargs: Required. Provider keyword arguments.

    Returns:
        Provider request payload.

    Raises:
        RuntimeError: If duration is missing.
    """
    duration = kwargs.get("duration")
    if duration is None:
        raise RuntimeError("duration is required for Jen text-to-track generation.")

    payload = {
        "prompt": prepared["prompt"],
        "duration": duration,
    }
    if model:
        payload["model"] = model
    add_if_present(payload, kwargs, "format")
    handled = set(payload) | {"model"}
    payload.update(safe_payload_kwargs(kwargs, handled=handled))
    return payload


def _cost(model, kwargs):
    """Estimate Jen generation cost from documented duration pricing.

    Args:
        model: Optional. Jen model.
        kwargs: Required. Provider keyword arguments.

    Returns:
        Normalized cost metadata.
    """
    duration = kwargs.get("duration")
    if duration is None:
        return unavailable_cost(COST_SOURCE)
    minutes = math.ceil(float(duration) / 60.0)
    return estimated_cost(
        minutes * 0.040,
        COST_SOURCE,
        {
            "duration_seconds": duration,
            "billable_minutes": minutes,
            "price_per_minute_usd": 0.040,
        },
    )


def update_cost(result, **kwargs):
    """Refresh Jen cost metadata from documented minute pricing.

    Args:
        result: Required. Normalized result dictionary.
        **kwargs: Optional. Dispatcher compatibility values.

    Returns:
        The updated result dictionary.
    """
    details = result.get("cost_details") if isinstance(result, dict) else {}
    duration = (details or {}).get("duration_seconds") or (details or {}).get("duration")
    if duration is None:
        cost = cost_utils.unavailable_cost_metadata()
    else:
        minutes = math.ceil(float(duration) / 60.0)
        cost = cost_utils.normalize_cost(
            minutes * 0.040,
            source=COST_SOURCE,
            is_estimated=True,
            details={
                "duration_seconds": duration,
                "billable_minutes": minutes,
                "price_per_minute_usd": 0.040,
            },
        )
    return cost_utils.apply_cost_metadata(result, cost)


def generate_text_to_music(prompt, output_path=None, sync=True, **kwargs):
    """Generate a track with Jen Music.

    Args:
        prompt: Required. Music prompt.
        output_path: Optional. Destination path when final audio is available.
        sync: Optional. Poll until completion when true.
        **kwargs: Optional. Provider-native generation parameters.

    Returns:
        A normalized result dictionary.
    """
    kwargs = dict(kwargs)
    model = None
    try:
        prepared = prepare_text_to_music(prompt, kwargs)
        model = _selected_model(kwargs)
        payload = _build_payload(model, prepared, kwargs)
        endpoint = kwargs.get("endpoint_url") or endpoint_from_base(
            kwargs.get("base_url") or BASE_URL,
            GENERATE_PATH,
        )
        if not endpoint:
            raise missing_endpoint_error(PROVIDER, "the Jen API base URL")

        raw_response = _request_json("POST", endpoint, kwargs, json=payload)
        trackid = _extract_track_id(raw_response)
        status_url = _status_url(trackid, kwargs, raw_response)

        if not sync:
            return build_result(
                PROVIDER,
                model=model,
                status="submitted",
                raw_response=raw_response,
                request_id=trackid,
                cost=_cost(model, kwargs),
                status_url=status_url,
            )

        final_response = _poll_generation(trackid, kwargs, raw_response)
        audio_url = first_audio_url(final_response)
        saved_path = download_audio(
            audio_url,
            output_path,
            timeout=kwargs.get("download_timeout", request_timeout(kwargs)),
        )
        return build_result(
            PROVIDER,
            model=model,
            raw_response={"submit": raw_response, "result": final_response},
            request_id=trackid,
            audio_url=audio_url,
            output_path=saved_path,
            cost=_cost(model, kwargs),
            status_url=status_url,
        )
    except Exception as exc:
        return failure_result(PROVIDER, model=model, exc=exc, output_path=output_path)


def get_generation_status(request_id, **kwargs):
    """Fetch Jen generation status.

    Args:
        request_id: Required. Jen track ID.
        **kwargs: Optional. Provider request options.

    Returns:
        A normalized result dictionary.
    """
    kwargs = dict(kwargs)
    model = _selected_model(kwargs)
    try:
        response = _request_json("GET", _status_url(request_id, kwargs), kwargs)
        return build_result(
            PROVIDER,
            model=model,
            raw_response=response,
            request_id=request_id,
            cost=_cost(model, kwargs),
            status_url=_status_url(request_id, kwargs),
        )
    except Exception as exc:
        return failure_result(PROVIDER, model=model, exc=exc, request_id=request_id)


def get_generation_result(request_id, output_path=None, **kwargs):
    """Fetch and optionally download a Jen generation result.

    Args:
        request_id: Required. Jen track ID.
        output_path: Optional. Destination path.
        **kwargs: Optional. Provider request options.

    Returns:
        A normalized result dictionary.
    """
    kwargs = dict(kwargs)
    model = _selected_model(kwargs)
    try:
        response = _request_json("GET", _status_url(request_id, kwargs), kwargs)
        audio_url = first_audio_url(response)
        saved_path = download_audio(audio_url, output_path, timeout=kwargs.get("download_timeout", 60))
        return build_result(
            PROVIDER,
            model=model,
            raw_response=response,
            request_id=request_id,
            audio_url=audio_url,
            output_path=saved_path,
            cost=_cost(model, kwargs),
            status_url=_status_url(request_id, kwargs),
        )
    except Exception as exc:
        return failure_result(PROVIDER, model=model, exc=exc, request_id=request_id, output_path=output_path)


download_generation = get_generation_result


def _request_json(method, url, kwargs, json=None):
    """Send an authenticated Jen JSON request.

    Args:
        method: Required. HTTP method.
        url: Required. Request URL.
        kwargs: Required. Provider keyword arguments.
        json: Optional. JSON body.

    Returns:
        Provider response JSON.
    """
    api_key = env_utils.require_env_var(ENV_NAME)
    return http_utils.request_json(
        method,
        url,
        headers={"Authorization": f"Bearer {api_key}"},
        json=json,
        timeout=request_timeout(kwargs),
        retries=request_retries(kwargs),
    )


def _poll_generation(trackid, kwargs, raw_response=None):
    """Poll Jen until the track is generated.

    Args:
        trackid: Required. Jen track ID.
        kwargs: Required. Provider keyword arguments.
        raw_response: Optional. Submit response.

    Returns:
        Final provider response JSON.
    """
    if not trackid:
        raise RuntimeError("Jen response did not include trackid.")

    interval, max_polls = poll_settings(kwargs, interval=10, max_polls=90)
    response = raw_response or {}
    for _attempt in range(max_polls):
        response = _request_json("GET", _status_url(trackid, kwargs, raw_response), kwargs)
        status = str(response.get("status", "")).lower()
        if status in SUCCESS_STATUSES or first_audio_url(response):
            return response
        if status in FAILURE_STATUSES:
            raise RuntimeError(f"Jen task failed with status '{status}'.")
        time.sleep(interval)
    raise TimeoutError("Jen task did not complete before max_polls.")


def _extract_track_id(response):
    """Extract a Jen track ID from a response.

    Args:
        response: Required. Provider response JSON.

    Returns:
        Track ID, or None.
    """
    if not isinstance(response, dict):
        return None
    for key in ("trackid", "track_id", "trackId", "id"):
        if response.get(key):
            return response[key]
    data = response.get("data")
    if isinstance(data, dict):
        return _extract_track_id(data)
    return None


def _status_url(trackid, kwargs, raw_response=None):
    """Return the Jen status URL.

    Args:
        trackid: Required. Jen track ID.
        kwargs: Required. Provider keyword arguments.
        raw_response: Optional. Submit response.

    Returns:
        Status URL.
    """
    if raw_response and isinstance(raw_response, dict):
        for key in ("status_url", "statusUrl", "url"):
            if raw_response.get(key):
                return raw_response[key]
    if kwargs.get("status_url"):
        return str(kwargs["status_url"]).format(trackid=trackid)
    status_url = endpoint_from_base(
        kwargs.get("base_url") or BASE_URL,
        STATUS_PATH.format(trackid=trackid),
    )
    if not status_url:
        raise missing_endpoint_error(PROVIDER, "the Jen API base URL for status polling")
    return status_url
