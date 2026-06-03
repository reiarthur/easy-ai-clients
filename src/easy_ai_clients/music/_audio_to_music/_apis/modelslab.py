from ..._common import cost_utils, env_utils, http_utils
from ..post_processing import build_result, wait_for_result
from ..pre_processing import (
    add_prompt,
    apply_audio_reference,
    prepare_audio_to_music,
    without_internal_kwargs,
)

PROVIDER = "modelslab"
ENV_NAME = "MODELSLAB_API_KEY"
DEFAULT_MODEL = "musicgen"
DEFAULT_ENDPOINT = "https://modelslab.com/api/v6/voice/music_gen"


def generate_audio_to_music(audio, prompt=None, output_path=None, sync=True, **kwargs):
    """Generate audio-guided music with ModelsLab MusicGen."""
    model = kwargs.pop("model", DEFAULT_MODEL)
    endpoint = kwargs.pop("endpoint", DEFAULT_ENDPOINT)
    timeout = kwargs.pop("timeout", 60)
    retries = kwargs.pop("retries", 2)
    payload = _build_payload(audio, prompt=prompt, model=model, **kwargs)
    payload["key"] = env_utils.require_env_var(ENV_NAME)
    raw_response = http_utils.request_json(
        "POST",
        endpoint,
        json=payload,
        timeout=timeout,
        retries=retries,
    )
    if not sync or result_urls_available(raw_response):
        return build_result(PROVIDER, model, raw_response, output_path=output_path, cost=_cost(model=model))

    fetch_url = _fetch_url(raw_response)
    if not fetch_url:
        return build_result(
            PROVIDER,
            model,
            raw_response,
            output_path=output_path,
            status="submitted",
            request_id=_request_id(raw_response),
            cost=_cost(model=model),
        )

    final_response = wait_for_result(
        lambda: _fetch_result(fetch_url, timeout=timeout, retries=retries),
        max_wait_seconds=kwargs.get("max_wait_seconds", 600),
        poll_interval=kwargs.get("poll_interval", 5),
    )
    return build_result(PROVIDER, model, final_response, output_path=output_path, cost=_cost(model=model))


def get_generation_result(request_id, output_path=None, model=None, **kwargs):
    """Fetch a ModelsLab result from a fetch URL."""
    if not request_id.startswith("http"):
        raise RuntimeError("ModelsLab get_generation_result requires a fetch_result URL.")
    response = _fetch_result(
        request_id,
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
    )
    return build_result(PROVIDER, model or DEFAULT_MODEL, response, output_path=output_path)


def _build_payload(audio, prompt=None, model=None, **kwargs):
    """Build the ModelsLab MusicGen payload."""
    prepare_audio_to_music(audio, prompt=prompt)
    payload = without_internal_kwargs(kwargs)
    add_prompt(payload, prompt, field_name=kwargs.get("prompt_field", "prompt"))
    if model is not None:
        payload.setdefault("model", model)
    field = apply_audio_reference(
        payload,
        audio,
        url_field=kwargs.get("url_field", "init_audio"),
        base64_field=kwargs.get("base64_field", "init_audio"),
        file_id_field=kwargs.get("file_id_field"),
        prefer=kwargs.get("audio_format"),
        mime_type=kwargs.get("mime_type"),
    )
    if field == "init_audio" and not str(payload[field]).startswith("http"):
        payload.setdefault("base64", True)
    return payload


def _cost(model=None, **kwargs):
    """Return unavailable ModelsLab cost metadata."""
    return cost_utils.unavailable_cost_metadata(
        source="modelslab_credits",
        details={"model": model, **kwargs},
    )


def _fetch_result(fetch_url, timeout=60, retries=2):
    return http_utils.request_json(
        "POST",
        fetch_url,
        json={"key": env_utils.require_env_var(ENV_NAME)},
        timeout=timeout,
        retries=retries,
    )


def _fetch_url(response):
    if isinstance(response, dict):
        return response.get("fetch_result") or response.get("fetchResult")
    return None


def _request_id(response):
    if isinstance(response, dict):
        return response.get("id") or response.get("request_id") or response.get("task_id")
    return None


def result_urls_available(response):
    return isinstance(response, dict) and bool(response.get("output") or response.get("audio_url"))
