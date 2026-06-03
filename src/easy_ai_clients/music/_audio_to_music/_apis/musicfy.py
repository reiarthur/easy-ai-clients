from ..._common import cost_utils, env_utils, http_utils
from ..post_processing import build_result
from ..pre_processing import (
    add_prompt,
    apply_audio_reference,
    audio_to_multipart_file,
    prepare_audio_to_music,
    without_internal_kwargs,
)

PROVIDER = "musicfy"
ENV_NAME = "MUSICFY_API_KEY"
DEFAULT_MODEL = None
DEFAULT_ENDPOINT = "https://api.musicfy.lol/v1/audio-to-music"


def generate_audio_to_music(audio, prompt=None, output_path=None, sync=True, **kwargs):
    """Generate or transform music using Musicfy."""
    model = kwargs.pop("model", DEFAULT_MODEL)
    endpoint = kwargs.pop("endpoint", DEFAULT_ENDPOINT)
    timeout = kwargs.pop("timeout", 60)
    retries = kwargs.pop("retries", 2)
    multipart = kwargs.pop("multipart", False)
    headers = _headers()

    if multipart:
        data, files = _build_multipart_payload(audio, prompt=prompt, model=model, **kwargs)
        response = http_utils.multipart_request(
            "POST",
            endpoint,
            headers=headers,
            data=data,
            files=files,
            timeout=timeout,
            retries=retries,
        )
        raw_response = http_utils.response_json(response)
    else:
        payload = _build_payload(audio, prompt=prompt, model=model, **kwargs)
        raw_response = http_utils.request_json(
            "POST",
            endpoint,
            headers=headers,
            json=payload,
            timeout=timeout,
            retries=retries,
        )

    return build_result(PROVIDER, model, raw_response, output_path=output_path, cost=_cost(model=model))


def _build_payload(audio, prompt=None, model=None, **kwargs):
    """Build the Musicfy JSON payload."""
    prepare_audio_to_music(audio, prompt=prompt)
    payload = without_internal_kwargs(kwargs)
    add_prompt(payload, prompt, field_name=kwargs.get("prompt_field", "prompt"))
    if model is not None:
        payload.setdefault("model", model)
    apply_audio_reference(
        payload,
        audio,
        url_field=kwargs.get("url_field", "audio_url"),
        base64_field=kwargs.get("base64_field"),
        data_uri_field=kwargs.get("data_uri_field", "audio"),
        file_id_field=kwargs.get("file_id_field", "file_id"),
        prefer=kwargs.get("audio_format"),
        mime_type=kwargs.get("mime_type"),
    )
    return payload


def _build_multipart_payload(audio, prompt=None, model=None, **kwargs):
    """Build the Musicfy multipart payload."""
    data = without_internal_kwargs(kwargs)
    add_prompt(data, prompt, field_name=kwargs.get("prompt_field", "prompt"))
    if model is not None:
        data.setdefault("model", model)
    files = audio_to_multipart_file(
        audio,
        field_name=kwargs.get("file_field", "audio"),
        filename=kwargs.get("filename"),
        mime_type=kwargs.get("mime_type"),
        timeout=kwargs.get("timeout", 60),
    )
    return data, files


def _cost(model=None, **kwargs):
    """Return unavailable Musicfy cost metadata."""
    return cost_utils.unavailable_cost_metadata(
        source="musicfy_minutes",
        details={"model": model, **kwargs},
    )


def _headers():
    api_key = env_utils.require_env_var(ENV_NAME)
    return {"Authorization": f"Bearer {api_key}"}
