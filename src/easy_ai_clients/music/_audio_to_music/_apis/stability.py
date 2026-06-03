from ..._common import cost_utils, env_utils, http_utils
from ..post_processing import build_result
from ..pre_processing import (
    audio_to_multipart_file,
    prepare_audio_to_music,
    without_internal_kwargs,
)

PROVIDER = "stability"
ENV_NAME = "STABILITY_API_KEY"
DEFAULT_MODEL = "stable-audio-2.5"
DEFAULT_ENDPOINT = "https://api.stability.ai/v2beta/audio/stable-audio-2/audio-to-audio"

_MODE_ENDPOINTS = {
    "audio_to_audio": DEFAULT_ENDPOINT,
    "remix_variation": DEFAULT_ENDPOINT,
    "inpaint": "https://api.stability.ai/v2beta/audio/stable-audio-2/inpaint",
}


def generate_audio_to_music(audio, prompt=None, output_path=None, sync=True, **kwargs):
    """Generate or transform music using Stability Stable Audio."""
    model = kwargs.pop("model", DEFAULT_MODEL)
    endpoint = _endpoint(kwargs)
    timeout = kwargs.pop("timeout", 60)
    retries = kwargs.pop("retries", 2)
    headers = _headers()
    data, files = _build_payload(audio, prompt=prompt, model=model, **kwargs)

    response = http_utils.multipart_request(
        "POST",
        endpoint,
        headers=headers,
        data=data,
        files=files,
        timeout=timeout,
        retries=retries,
    )
    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        raw_response = http_utils.response_json(response)
        return build_result(PROVIDER, model, raw_response, output_path=output_path)

    return build_result(
        PROVIDER,
        model,
        {"status": "completed", "content_type": content_type},
        output_path=output_path,
        status="completed",
        audio=response.content,
        cost=_cost(model=model),
    )


def _build_payload(audio, prompt=None, model=None, **kwargs):
    """Build the Stability multipart payload."""
    prepare_audio_to_music(audio, prompt=prompt)
    timeout = kwargs.get("timeout", 60)
    data = without_internal_kwargs(kwargs)
    if prompt is not None:
        data["prompt"] = prompt
    if model is not None:
        data.setdefault("model", model)
    files = audio_to_multipart_file(
        audio,
        field_name=kwargs.get("file_field", "audio"),
        filename=kwargs.get("filename"),
        mime_type=kwargs.get("mime_type"),
        timeout=timeout,
    )
    return data, files


def _cost(model=None, **kwargs):
    """Return unavailable Stability cost metadata."""
    return cost_utils.unavailable_cost_metadata(
        source="stability_platform_credits",
        details={"model": model, **kwargs},
    )


def _endpoint(kwargs):
    endpoint = kwargs.pop("endpoint", None)
    if endpoint:
        return endpoint
    mode = kwargs.pop("mode", "audio_to_audio")
    return _MODE_ENDPOINTS.get(mode, DEFAULT_ENDPOINT)


def _headers():
    api_key = env_utils.require_env_var(ENV_NAME)
    return {
        "Authorization": f"Bearer {api_key}",
        "Accept": "audio/*,application/json",
    }
