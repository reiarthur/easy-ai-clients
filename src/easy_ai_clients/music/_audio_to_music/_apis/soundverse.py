from ..._common import cost_utils, env_utils, http_utils
from ..post_processing import build_result, wait_for_result
from ..pre_processing import (
    add_prompt,
    apply_audio_reference,
    prepare_audio_to_music,
    without_internal_kwargs,
)

PROVIDER = "soundverse"
ENV_NAME = "SOUNDVERSE_API_KEY"
DEFAULT_MODEL = None
DEFAULT_BASE_URL = "https://api.soundverse.ai"

_MODE_ENDPOINTS = {
    "music": "/v5/generate/music",
    "song": "/v5/generate/song",
    "song_sync": "/v5/generate/song/sync",
    "extend": "/v5/extend/song",
    "remix_variation": "/v5/generate/music",
    "audio_to_audio": "/v5/generate/music",
}


def generate_audio_to_music(audio, prompt=None, output_path=None, sync=True, **kwargs):
    """Submit a Soundverse audio-reference music task."""
    model = kwargs.pop("model", DEFAULT_MODEL)
    endpoint = _endpoint(kwargs)
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
    )
    return build_result(PROVIDER, model, final_response, output_path=output_path, cost=_cost(model=model))


def get_generation_status(request_id, model=None, **kwargs):
    """Fetch Soundverse status by message ID."""
    base_url = kwargs.get("base_url", DEFAULT_BASE_URL)
    return http_utils.request_json(
        "GET",
        f"{base_url}/v5/status",
        headers=_headers(),
        params={"message_id": request_id},
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
    )


def get_generation_result(request_id, output_path=None, model=None, **kwargs):
    """Fetch Soundverse status/result by message ID."""
    response = get_generation_status(request_id, model=model, **kwargs)
    return build_result(PROVIDER, model, response, output_path=output_path)


def _build_payload(audio, prompt=None, model=None, **kwargs):
    """Build the Soundverse payload."""
    prepare_audio_to_music(audio, prompt=prompt)
    payload = without_internal_kwargs(kwargs)
    add_prompt(payload, prompt, field_name=kwargs.get("prompt_field", "prompt"))
    if model is not None:
        payload.setdefault("model", model)
    reference_type = kwargs.get("reference_type") or kwargs.get("audio_type") or "reference"
    default_field = {
        "reference": "reference_url",
        "instrumental": "instrumental_url",
        "vocal": "vocal_url",
        "melody": "melody_url",
        "audio": "audio_url",
    }.get(reference_type, "reference_url")
    apply_audio_reference(
        payload,
        audio,
        url_field=kwargs.get("url_field", default_field),
        file_id_field=kwargs.get("file_id_field"),
        prefer=kwargs.get("audio_format", "url"),
        mime_type=kwargs.get("mime_type"),
    )
    return payload


def _cost(model=None, **kwargs):
    """Return unavailable Soundverse cost metadata."""
    return cost_utils.unavailable_cost_metadata(
        source="soundverse_billing",
        details={"model": model, **kwargs},
    )


def _endpoint(kwargs):
    endpoint = kwargs.pop("endpoint", None)
    if endpoint:
        return endpoint
    base_url = kwargs.pop("base_url", DEFAULT_BASE_URL)
    mode = kwargs.pop("mode", "music")
    return f"{base_url}{_MODE_ENDPOINTS.get(mode, _MODE_ENDPOINTS['music'])}"


def _headers():
    api_key = env_utils.require_env_var(ENV_NAME)
    return {"Authorization": f"Bearer {api_key}"}


def _request_id(response):
    if isinstance(response, dict):
        return response.get("message_id") or response.get("messageId") or response.get("id")
    return None
