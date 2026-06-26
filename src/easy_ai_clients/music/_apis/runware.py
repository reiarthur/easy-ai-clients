import json
import uuid

from .._common import (
    api_timeout,
    apply_cost_metadata,
    auth_header,
    download_generation_audio,
    normalize_cost,
    normalize_duration,
    raise_input_limit_error,
    reject_parameter_present,
    reject_unknown_kwargs,
    request_json,
    sanitize,
    standard_generation,
    text_limit_field,
    validate_range,
)

MODELS = {
    "runware:ace-step@v1.5-turbo": {
        "endpoint": "https://api.runware.ai/v1",
        "status_endpoint": "https://api.runware.ai/v1",
        "result_endpoint": "https://api.runware.ai/v1",
        "doc": "https://runware.ai/docs/models/ace-step-v1-5-turbo",
    },
    "runware:ace-step@v1.5-xl-base": {
        "endpoint": "https://api.runware.ai/v1",
        "status_endpoint": "https://api.runware.ai/v1",
        "result_endpoint": "https://api.runware.ai/v1",
        "doc": "https://runware.ai/docs/models/ace-step-v1-5-xl-base",
    },
    "runware:ace-step@v1.5-xl-turbo": {
        "endpoint": "https://api.runware.ai/v1",
        "status_endpoint": "https://api.runware.ai/v1",
        "result_endpoint": "https://api.runware.ai/v1",
        "doc": "https://runware.ai/docs/models/ace-step-v1-5-xl-turbo",
    },
    "runware:ace-step@v1.5-xl-sft": {
        "endpoint": "https://api.runware.ai/v1",
        "status_endpoint": "https://api.runware.ai/v1",
        "result_endpoint": "https://api.runware.ai/v1",
        "doc": "https://runware.ai/docs/models/ace-step-v1-5-xl-sft",
    },
}

RUNWARE_SEED = 12345
RUNWARE_OUTPUT_TYPE = "URL"
RUNWARE_OUTPUT_FORMAT = "MP3"
RUNWARE_TTL = 60
RUNWARE_AUDIO_SETTINGS = {
    "bitrate": 320,
    "sampleRate": 48000,
    "channels": 2,
}
RUNWARE_SFT_CFG_SCALE = 8
RUNWARE_SFT_CFG_INTERVAL_START = 0
RUNWARE_SFT_CFG_INTERVAL_END = 1
RUNWARE_SFT_GUIDANCE_TYPE = "apg"


def generate(lyrics, model="runware:ace-step@v1.5-xl-turbo", **kwargs):
    """Submit one Runware audio inference task.

    Args:
        lyrics: Required. Song lyrics for the selected model.
        model: Optional. Accepted values:
            - "runware:ace-step@v1.5-turbo": ACE-Step Turbo.
            - "runware:ace-step@v1.5-xl-base": ACE-Step XL Base.
            - "runware:ace-step@v1.5-xl-turbo": ACE-Step XL Turbo.
            - "runware:ace-step@v1.5-xl-sft": ACE-Step XL SFT.
        **kwargs: Optional provider parameters:
            - `prompt`: Required. Sent as `positivePrompt`.
            - `negative_prompt`: Not supported by public music generation.
            - `duration`: ACE-Step duration in seconds. Missing or invalid
              values use `60`. Numeric values are clamped to `30..300`.
            - `steps`: ACE-Step inference steps.
            - `bpm`: ACE-Step tempo in beats per minute.
            - `key_scale`: ACE-Step musical key.
            - `time_signature`: ACE-Step time signature.
            - `vocal_language`: ACE-Step vocal language.

    Returns:
        A normalized generation dictionary.

    Raises:
        ValueError: If the model is unsupported, `prompt` is missing,
            parameters are invalid for the selected model, or kwargs include
            unsupported keys.
    """
    if model not in MODELS:
        raise ValueError(f"Unsupported model: {model}")
    prompt = kwargs.pop("prompt", None)
    reject_parameter_present(kwargs, "negative_prompt", "runware")
    duration = normalize_duration(kwargs.pop("duration", None), 30, 300, default=60)
    if "steps" not in kwargs:
        kwargs["steps"] = _default_steps(model)
    _validate_request(model, prompt, lyrics, kwargs)
    kwargs["duration"] = duration

    task_uuid = str(uuid.uuid4())
    response = request_json(
        "POST",
        MODELS[model]["endpoint"],
        headers=_headers(),
        json_payload=[_payload(model, task_uuid, prompt, lyrics, kwargs)],
        timeout=api_timeout(120),
    )
    result = _first_result(response, "submit")
    cost = normalize_cost(result.get("cost"))
    generation = standard_generation(
        provider="runware",
        model=model,
        request_id=_task_uuid(result, fallback=task_uuid),
        status=_standard_status(result),
        cost_usd=cost,
        cost_source="provider_response" if cost is not None else None,
        cost_is_estimated=False,
    )
    return generation


def get_status(generation):
    """Return an updated Runware audio task dictionary.

    Args:
        generation: Required. Dictionary returned by `generate()`.

    Returns:
        The updated generation dictionary.

    Raises:
        RuntimeError: If the provider reports a terminal failure.
    """
    try:
        result = _status_result(generation)
    except RuntimeError:
        generation["status"] = "failed"
        raise
    status = result.get("status")
    cost = normalize_cost(result.get("cost"))
    if cost is not None:
        apply_cost_metadata(
            generation,
            cost,
            source="provider_response",
            is_estimated=False,
        )
    if status == "success":
        generation["status"] = "completed"
    else:
        generation["status"] = "running"
    return generation


def download_result(generation):
    """Download a completed Runware result and return the generation dictionary.

    Args:
        generation: Required. Dictionary returned by `generate()`.

    Returns:
        The updated generation dictionary.

    Raises:
        RuntimeError: If the provider reports a terminal failure.
    """
    try:
        result = _status_result(generation)
    except RuntimeError:
        generation["status"] = "failed"
        raise
    status = result.get("status")
    cost = normalize_cost(result.get("cost"))
    if cost is not None:
        apply_cost_metadata(
            generation,
            cost,
            source="provider_response",
            is_estimated=False,
        )
    if status != "success":
        generation["status"] = "running"
        return generation
    try:
        audio_url = result.get("audioURL")
        if not audio_url:
            raise RuntimeError(
                f"runware completed response did not include audioURL: {_safe_detail(result)}"
            )
        return download_generation_audio(generation, "runware", audio_url, "mp3")
    except Exception:
        generation["status"] = "failed"
        raise


def _payload(model, task_uuid, prompt, lyrics, kwargs):
    payload = {
        "taskType": "audioInference",
        "taskUUID": task_uuid,
        "model": model,
        "deliveryMethod": "async",
        "outputType": RUNWARE_OUTPUT_TYPE,
        "outputFormat": RUNWARE_OUTPUT_FORMAT,
        "includeCost": True,
        "numberResults": 1,
        "ttl": RUNWARE_TTL,
        "audioSettings": RUNWARE_AUDIO_SETTINGS,
    }
    payload["positivePrompt"] = prompt

    if _is_ace_step(model):
        payload["seed"] = RUNWARE_SEED
        payload["duration"] = kwargs["duration"]
        if "steps" in kwargs:
            payload["steps"] = kwargs["steps"]
        if _is_sft(model):
            payload["CFGScale"] = RUNWARE_SFT_CFG_SCALE
        settings = {"lyrics": lyrics}
        _set_if_present(settings, "bpm", kwargs, "bpm")
        _set_if_present(settings, "keyScale", kwargs, "key_scale")
        _set_if_present(settings, "timeSignature", kwargs, "time_signature")
        _set_if_present(settings, "vocalLanguage", kwargs, "vocal_language")
        if _is_sft(model):
            settings["cfgIntervalStart"] = RUNWARE_SFT_CFG_INTERVAL_START
            settings["cfgIntervalEnd"] = RUNWARE_SFT_CFG_INTERVAL_END
            settings["guidanceType"] = RUNWARE_SFT_GUIDANCE_TYPE
        payload["settings"] = settings
    return payload


def _headers():
    headers = auth_header("RUNWARE_API_KEY", "bearer")
    headers["Content-Type"] = "application/json"
    return headers


def _validate_request(model, prompt, lyrics, kwargs):
    reject_unknown_kwargs(kwargs, _allowed_kwargs(model))

    if prompt is None:
        raise ValueError("prompt is required for runware")

    if _is_ace_step(model):
        _validate_ace_step(model, prompt, lyrics, kwargs)


def _validate_ace_step(model, prompt, lyrics, kwargs):
    if not lyrics or len(lyrics.strip()) < 10:
        raise ValueError("lyrics must be at least 10 characters for ACE-Step models")
    fields = {}
    prompt_limit = text_limit_field(prompt, 3000)
    lyrics_limit = text_limit_field(lyrics, 3000)
    if prompt_limit is not None:
        fields["positivePrompt"] = prompt_limit
    if lyrics_limit is not None:
        fields["settings.lyrics"] = lyrics_limit
    if fields:
        raise_input_limit_error("runware", model, fields)
    if "steps" in kwargs:
        _validate_range("steps", kwargs["steps"], 1, _max_steps(model))
    if "bpm" in kwargs:
        _validate_range("bpm", kwargs["bpm"], 30, 300)
    if "time_signature" in kwargs and kwargs["time_signature"] not in {2, 3, 4, 6}:
        raise ValueError("time_signature must be one of: 2, 3, 4, 6")
    if "vocal_language" in kwargs and kwargs["vocal_language"] not in _vocal_languages():
        raise ValueError("vocal_language must be a documented ISO 639-1 value or 'unknown'")


def _validate_range(name, value, minimum, maximum):
    validate_range(name, value, minimum, maximum)


def _allowed_kwargs(model):
    if _is_ace_step(model):
        return {
            "steps",
            "bpm",
            "key_scale",
            "time_signature",
            "vocal_language",
        }
    return set()


def _set_if_present(payload, provider_key, kwargs, kwarg_key):
    if kwarg_key in kwargs:
        payload[provider_key] = kwargs[kwarg_key]


def _first_result(response, stage="response"):
    if not isinstance(response, dict):
        raise RuntimeError(f"runware {stage} response was not a JSON object")

    _raise_response_error(response, stage)
    data = response.get("data")
    if data is None:
        raise RuntimeError(f"runware {stage} response did not include data")
    if not isinstance(data, list):
        raise RuntimeError(f"runware {stage} response data was not a list: {_safe_detail(data)}")
    if not data:
        raise RuntimeError(f"runware {stage} response did not include data")

    result = data[0]
    if not isinstance(result, dict):
        raise RuntimeError(
            f"runware {stage} response first data item was not an object: {_safe_detail(result)}"
        )
    if result.get("status") == "error" or result.get("error"):
        raise RuntimeError(_result_error_message(result, stage))
    return result


def _raise_response_error(response, stage):
    errors = response.get("errors")
    if errors:
        raise RuntimeError(_response_error_message(errors, stage))
    error = response.get("error")
    if error:
        raise RuntimeError(_response_error_message(error, stage))


def _response_error_message(error_value, stage):
    error = _first_error(error_value)
    status = error.get("status") or error.get("code") or "error"
    return f"runware generation failed during {stage} with status {status}: {_safe_detail(error)}"


def _result_error_message(result, stage):
    detail = {
        "status": result.get("status"),
        "taskUUID": result.get("taskUUID"),
        "code": result.get("code"),
        "message": result.get("message"),
        "error": result.get("error"),
    }
    status = result.get("status") or "error"
    return f"runware generation failed during {stage} with status {status}: {_safe_detail(detail)}"


def _first_error(error_value):
    if isinstance(error_value, list):
        if not error_value:
            return {"message": "empty errors list"}
        first = error_value[0]
        if isinstance(first, dict):
            return first
        return {"message": first}
    if isinstance(error_value, dict):
        return error_value
    return {"message": error_value}


def _task_uuid(result, fallback=None):
    task_uuid = result.get("taskUUID") or fallback
    if not task_uuid:
        raise RuntimeError(f"runware response did not include taskUUID: {_safe_detail(result)}")
    return str(task_uuid)


def _safe_detail(value):
    return json.dumps(sanitize(value), ensure_ascii=False)[:1200]


def _is_ace_step(model):
    return model.startswith("runware:ace-step@")


def _is_sft(model):
    return model == "runware:ace-step@v1.5-xl-sft"


def _max_steps(model):
    if model in {
        "runware:ace-step@v1.5-xl-base",
        "runware:ace-step@v1.5-xl-sft",
    }:
        return 300
    return 20


def _default_steps(model):
    if model == "runware:ace-step@v1.5-turbo":
        return 10
    if model == "runware:ace-step@v1.5-xl-turbo":
        return 8
    if model in {
        "runware:ace-step@v1.5-xl-base",
        "runware:ace-step@v1.5-xl-sft",
    }:
        return 100
    return 8


def _status_result(generation):
    response = request_json(
        "POST",
        MODELS[generation["model"]]["status_endpoint"],
        headers=_headers(),
        json_payload=[{"taskType": "getResponse", "taskUUID": generation["request_id"]}],
        timeout=api_timeout(120),
    )
    return _first_result(response, "status")


def _standard_status(result):
    status = result.get("status")
    if status == "success" or result.get("audioURL"):
        return "completed"
    if status == "error":
        return "failed"
    return "submitted"


def _vocal_languages():
    return {
        "unknown",
        "ar",
        "az",
        "bg",
        "bn",
        "ca",
        "cs",
        "da",
        "de",
        "el",
        "en",
        "es",
        "fa",
        "fi",
        "fr",
        "he",
        "hi",
        "hr",
        "ht",
        "hu",
        "id",
        "is",
        "it",
        "ja",
        "ko",
        "la",
        "lt",
        "ms",
        "ne",
        "nl",
        "no",
        "pa",
        "pl",
        "pt",
        "ro",
        "ru",
        "sa",
        "sk",
        "sr",
        "sv",
        "sw",
        "ta",
        "te",
        "th",
        "tl",
        "tr",
        "uk",
        "ur",
        "vi",
        "yue",
        "zh",
    }



