import math

from ..._common import cost_utils
from ..._common import operation_utils as _ops

PROVIDER = "jen"
ENV_NAME = "JEN_MUSIC_API_KEY"
DEFAULT_MODEL = None
EXTEND_ENDPOINT_PATH = "/api/v3/public/track/extend/{track_id}"
STATUS_ENDPOINT_PATH = "/api/v3/public/generation_status/{track_id}"


def edit_music(audio, prompt=None, output_path=None, sync=True, **kwargs):
    """Extend an existing Jen track.

    Args:
        audio: Required. Jen track ID for the track to extend.
        prompt: Optional. Continuation prompt.
        output_path: Optional. Destination path for the final URL.
        sync: Optional. Poll status when a track ID is returned.
        **kwargs: Optional. Provider-native extension fields.

    Returns:
        A normalized music result.
    """
    model = _ops.resolve_model(kwargs, DEFAULT_MODEL)
    track_id = _track_id(audio, kwargs)
    payload = _build_payload(audio, prompt=prompt, **kwargs)
    endpoint = _ops.resolve_endpoint(
        kwargs,
        path=EXTEND_ENDPOINT_PATH.format(track_id=track_id),
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
    request_id = _ops.result_utils.extract_request_id(raw_response) or track_id
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
            extra={"edit_flow": "track_extension", "track_id": track_id},
        ),
        download_timeout=kwargs.get("download_timeout", 60),
    )


def get_generation_status(request_id, **kwargs):
    """Get Jen generation status.

    Args:
        request_id: Required. Jen track ID.
        **kwargs: Optional. Local request controls.

    Returns:
        A normalized music result.
    """
    raw_response = _request_status(request_id, **kwargs)
    return _ops.result(
        PROVIDER,
        _ops.resolve_model(kwargs, DEFAULT_MODEL),
        raw_response,
        cost=_cost(raw_response),
    )


def get_generation_result(request_id, output_path=None, **kwargs):
    """Get a Jen generation result through the status endpoint.

    Args:
        request_id: Required. Jen track ID.
        output_path: Optional. Destination path.
        **kwargs: Optional. Local request controls.

    Returns:
        A normalized music result.
    """
    raw_response = _request_status(request_id, **kwargs)
    return _ops.result(
        PROVIDER,
        _ops.resolve_model(kwargs, DEFAULT_MODEL),
        raw_response,
        output_path=output_path,
        cost=_cost(raw_response),
        download_timeout=kwargs.get("download_timeout", 60),
    )


def download_generation(request_id, output_path=None, **kwargs):
    """Download a completed Jen result.

    Args:
        request_id: Required. Jen track ID.
        output_path: Optional. Destination path.
        **kwargs: Optional. Local request controls.

    Returns:
        A normalized music result.
    """
    return get_generation_result(request_id, output_path=output_path, **kwargs)


def _build_payload(audio, prompt=None, **kwargs):
    """Build the Jen extension payload.

    Args:
        audio: Required. Jen track ID.
        prompt: Optional. Continuation prompt.
        **kwargs: Optional. Provider-native payload fields.

    Returns:
        A provider payload dictionary.
    """
    payload = _ops.forwarded_payload(
        kwargs,
        exclude=("track_id", "trackid", "trackId"),
    )
    _ops.add_prompt(payload, prompt)
    return payload


def _headers(kwargs):
    """Build Jen headers.

    Args:
        kwargs: Required. Local controls.

    Returns:
        Request headers.
    """
    headers = _ops.bearer_headers(PROVIDER, ENV_NAME)
    return _ops.merge_headers(headers, kwargs.get("headers"))


def _track_id(audio, kwargs):
    """Return the Jen track ID.

    Args:
        audio: Required. Audio argument used as track ID for Jen.
        kwargs: Required. Provider keyword arguments.

    Returns:
        A track ID.
    """
    track_id = (
        kwargs.get("track_id")
        or kwargs.get("trackid")
        or kwargs.get("trackId")
        or audio
    )
    if not track_id:
        raise RuntimeError("track_id is required for Jen extension.")
    return track_id


def _request_status(track_id, **kwargs):
    """Request raw Jen status.

    Args:
        track_id: Required. Jen track ID.
        **kwargs: Optional. Local request controls.

    Returns:
        Raw provider response.
    """
    path = kwargs.get("status_endpoint_path") or STATUS_ENDPOINT_PATH.format(
        track_id=track_id
    )
    url = _ops.resolve_endpoint(
        {"endpoint": kwargs.get("status_endpoint"), "base_url": kwargs.get("base_url")},
        path=path,
    )
    return _ops.get_json(
        url,
        headers=_headers(kwargs),
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
        request_kwargs=kwargs.get("request_kwargs"),
    )


def _cost(raw_response=None, payload=None):
    """Return Jen cost metadata.

    Args:
        raw_response: Optional. Provider response.
        payload: Optional. Request payload.

    Returns:
        Normalized cost metadata.
    """
    payload = payload or {}
    duration = payload.get("duration") or payload.get("duration_seconds")
    if duration is None:
        return _ops.unavailable_cost(
            {"reason": "Jen cost requires the requested duration in seconds."}
        )
    minutes = math.ceil(float(duration) / 60)
    return {
        "cost_usd": minutes * 0.040,
        "cost_currency": "USD",
        "cost_is_estimated": True,
        "cost_source": "official_pricing_table",
        "cost_details": {
            "duration_seconds": duration,
            "billable_minutes": minutes,
            "price_per_minute_usd": 0.040,
        },
    }


def update_cost(result, **kwargs):
    """Refresh Jen edit cost metadata from documented minute pricing.

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
        minutes = math.ceil(float(duration) / 60)
        cost = cost_utils.normalize_cost(
            minutes * 0.040,
            source="official_pricing_table",
            is_estimated=True,
            details={
                "duration_seconds": duration,
                "billable_minutes": minutes,
                "price_per_minute_usd": 0.040,
            },
        )
    return cost_utils.apply_cost_metadata(result, cost)
