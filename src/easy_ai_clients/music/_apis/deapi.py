from pathlib import Path

from .._common import (
    api_timeout,
    apply_cost_metadata,
    auth_header,
    download_generation_audio,
    normalize_cost,
    reject_parameter_present,
    reject_unknown_kwargs,
    request_json,
    standard_generation,
    validate_range,
)

MODELS = {
    "AceStep_1_5_Turbo": {
        "endpoint": "https://api.deapi.ai/api/v1/client/txt2music",
        "status_endpoint": "https://api.deapi.ai/api/v1/client/request-status/{request_id}",
        "result_endpoint": None,
        "doc": "https://docs.deapi.ai/api/generation/text-to-music",
    },
    "AceStep_1_5_XL_Turbo_INT8": {
        "endpoint": "https://api.deapi.ai/api/v1/client/txt2music",
        "status_endpoint": "https://api.deapi.ai/api/v1/client/request-status/{request_id}",
        "result_endpoint": None,
        "doc": "https://docs.deapi.ai/api/generation/text-to-music",
    },
}

DEAPI_SEED = -1
DEAPI_OUTPUT_FORMAT = "mp3"
DEAPI_GUIDANCE_SCALES = {
    "AceStep_1_5_Turbo": 1,
    "AceStep_1_5_XL_Turbo_INT8": 1,
}
PRICE_ENDPOINT = "https://api.deapi.ai/api/v2/audio/music/price"


def generate(lyrics, model="AceStep_1_5_Turbo", **kwargs):
    """Submit one deAPI music generation request.

    Args:
        lyrics: Required. Song lyrics sent as `lyrics`.
        model: Optional. Accepted values:
            - "AceStep_1_5_Turbo": Cheapest validated default.
            - "AceStep_1_5_XL_Turbo_INT8": XL Turbo INT8 variant.
        **kwargs: Optional provider parameters:
            - `prompt`: Required. Sent as `caption`.
            - `negative_prompt`: Not supported by deAPI music generation.
              Passing a value raises `ValueError`.
            - `duration`: Song duration in seconds. Defaults to `60`.
            - `steps`: Provider inference step count.
              Defaults to `8`; accepted values are `1` to `8`.
            - `bpm`: Tempo in beats per minute. Defaults to `116`.
            - `key_scale`: Musical key scale. Defaults to `"A minor"`.
            - `time_signature`: Time signature. Defaults to `4`.
            - `vocal_language`: Vocal language code. Defaults to `"pt"`.
            - `reference_audio`: Local path to an optional reference audio file.
            - `webhook_url`: HTTPS callback URL for job status changes.

    Returns:
        A normalized generation dictionary.

    Raises:
        ValueError: If the model is unsupported, `prompt` is missing,
            `negative_prompt` is passed, or kwargs include unsupported keys.
    """
    if model not in MODELS:
        raise ValueError(f"Unsupported model: {model}")
    prompt = kwargs.pop("prompt", None)
    reject_parameter_present(kwargs, "negative_prompt", "deapi")
    if prompt is None:
        raise ValueError("prompt is required for deapi")
    reject_unknown_kwargs(
        kwargs,
        {
            "duration",
            "steps",
            "bpm",
            "key_scale",
            "time_signature",
            "vocal_language",
            "reference_audio",
            "webhook_url",
        },
    )
    _validate_kwargs(model, kwargs)

    data = {
        "caption": prompt,
        "model": model,
        "lyrics": lyrics,
        "duration": kwargs.get("duration", 60),
        "inference_steps": kwargs.get("steps", 8),
        "guidance_scale": DEAPI_GUIDANCE_SCALES[model],
        "seed": DEAPI_SEED,
        "format": DEAPI_OUTPUT_FORMAT,
        "bpm": kwargs.get("bpm", 116),
        "keyscale": kwargs.get("key_scale", "A minor"),
        "timesignature": kwargs.get("time_signature", 4),
        "vocal_language": kwargs.get("vocal_language", "pt"),
    }
    if "webhook_url" in kwargs:
        data["webhook_url"] = kwargs["webhook_url"]

    if "reference_audio" in kwargs:
        reference_path = Path(kwargs["reference_audio"])
        with reference_path.open("rb") as reference_audio:
            response = request_json(
                "POST",
                MODELS[model]["endpoint"],
                headers=_headers(),
                data=data,
                files={"reference_audio": reference_audio},
                timeout=api_timeout(120),
            )
    else:
        response = request_json(
            "POST",
            MODELS[model]["endpoint"],
            headers=_headers(),
            json_payload=data,
            timeout=api_timeout(120),
        )
    request_id = response["data"]["request_id"]
    cost = _calculate_cost(data)
    return standard_generation(
        provider="deapi",
        model=model,
        request_id=request_id,
        status=_standard_status(response["data"].get("status")),
        cost_usd=cost,
        cost_source="deapi_price_endpoint" if cost is not None else None,
        cost_is_estimated=False,
        cost_details={
            "duration_seconds": data["duration"],
            "inference_steps": data["inference_steps"],
        },
    )


def get_status(generation):
    """Return an updated deAPI generation dictionary.

    Args:
        generation: Required. Dictionary returned by `generate()`.

    Returns:
        The updated generation dictionary.

    Raises:
        RuntimeError: If the provider reports a terminal failure.
    """
    response = _status_response(generation)
    status = response["data"]["status"]
    if generation.get("cost_source") == "unavailable":
        _apply_status_cost(generation, response["data"])
    if status in {"failed", "error", "cancelled", "canceled"}:
        generation["status"] = "failed"
        raise RuntimeError(f"deapi generation failed with status: {status}")
    if status == "done":
        generation["status"] = "completed"
    else:
        generation["status"] = "running"
    if generation.get("cost_source") == "unavailable":
        _apply_status_cost(generation, response["data"])
    return generation


def download_result(generation):
    """Download a completed deAPI result and return the generation dictionary.

    Args:
        generation: Required. Dictionary returned by `generate()`.

    Returns:
        The updated generation dictionary.

    Raises:
        RuntimeError: If the provider reports a terminal failure.
    """
    response = _status_response(generation)
    status = response["data"]["status"]
    if generation.get("cost_source") == "unavailable":
        _apply_status_cost(generation, response["data"])
    if status in {"failed", "error", "cancelled", "canceled"}:
        generation["status"] = "failed"
        raise RuntimeError(f"deapi generation failed with status: {status}")
    if status != "done":
        generation["status"] = "running"
        return generation
    generation["status"] = "completed"
    return download_generation_audio(generation, "deapi", response["data"].get("result_url"), "mp3")


def _headers():
    headers = auth_header("DEAPI_API_KEY", "bearer")
    headers["Accept"] = "application/json"
    return headers


def _validate_kwargs(model, kwargs):
    if "duration" in kwargs and not 10 <= kwargs["duration"] <= 600:
        validate_range("duration", kwargs["duration"], 10, 600, " seconds")
    if "steps" in kwargs:
        try:
            validate_range("steps", kwargs["steps"], 1, 8)
        except ValueError as exc:
            raise ValueError(f"{exc} for {model}") from None
    if "bpm" in kwargs and kwargs["bpm"] is not None and not 30 <= kwargs["bpm"] <= 300:
        validate_range("bpm", kwargs["bpm"], 30, 300)
    if "time_signature" in kwargs and kwargs["time_signature"] not in {2, 3, 4, 6}:
        raise ValueError("time_signature must be 2, 3, 4, or 6")


def _status_response(generation):
    status_endpoint = MODELS[generation["model"]]["status_endpoint"].format(
        request_id=generation["request_id"]
    )
    return request_json("GET", status_endpoint, headers=_headers(), timeout=api_timeout(120))


def _calculate_cost(data):
    for model in _price_model_candidates(data["model"]):
        payload = {
            "model": model,
            "duration": data["duration"],
            "inference_steps": data["inference_steps"],
        }
        try:
            response = request_json(
                "POST",
                PRICE_ENDPOINT,
                headers=_headers(),
                json_payload=payload,
                timeout=_price_timeout(),
            )
        except Exception:
            continue
        cost = _extract_cost(response)
        if cost is not None:
            return cost
    return None


def _apply_status_cost(generation, status_data):
    cost = normalize_cost(status_data.get("cost"))
    if cost is None:
        return generation
    return apply_cost_metadata(
        generation,
        cost,
        source="provider_response",
        is_estimated=False,
    )


def _price_model_candidates(model):
    return (model,)


def _extract_cost(value):
    if isinstance(value, dict):
        for key in ("cost", "price", "total_cost", "totalPrice", "amount"):
            cost = normalize_cost(value.get(key))
            if cost is not None:
                return cost
        for item in value.values():
            cost = _extract_cost(item)
            if cost is not None:
                return cost
    if isinstance(value, list):
        for item in value:
            cost = _extract_cost(item)
            if cost is not None:
                return cost
    return normalize_cost(value)


def _price_timeout():
    return min(api_timeout(15), 15)


def _standard_status(provider_status):
    if provider_status == "done":
        return "completed"
    if provider_status in {"failed", "error", "cancelled", "canceled"}:
        return "failed"
    return "submitted"



