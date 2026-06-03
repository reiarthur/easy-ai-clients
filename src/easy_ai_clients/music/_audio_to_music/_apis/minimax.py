from ..._common import cost_utils, env_utils, http_utils
from ..post_processing import audio_from_hex, build_result
from ..pre_processing import apply_audio_reference, prepare_audio_to_music, without_internal_kwargs

PROVIDER = "minimax"
ENV_NAME = "MINIMAX_API_KEY"
DEFAULT_MODEL = "music-cover"
DEFAULT_ENDPOINT = "https://api.minimax.io/v1/music_generation"


def generate_audio_to_music(audio, prompt=None, output_path=None, sync=True, **kwargs):
    """Generate a MiniMax cover or audio-to-audio music result."""
    model = kwargs.pop("model", DEFAULT_MODEL)
    endpoint = kwargs.pop("endpoint", DEFAULT_ENDPOINT)
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
    audio = _audio_from_response(raw_response)
    return build_result(
        PROVIDER,
        model,
        raw_response,
        output_path=output_path,
        audio=audio,
        cost=_cost(model=model),
    )


def _build_payload(audio, prompt=None, model=None, **kwargs):
    """Build the MiniMax music-cover payload."""
    prepare_audio_to_music(audio, prompt=prompt)
    payload = without_internal_kwargs(kwargs)
    payload.setdefault("model", model or DEFAULT_MODEL)
    if prompt is not None:
        payload["prompt"] = prompt
    payload.setdefault("output_format", kwargs.get("output_format", "url"))
    apply_audio_reference(
        payload,
        audio,
        url_field=kwargs.get("url_field", "audio_url"),
        base64_field=kwargs.get("base64_field", "audio_base64"),
        file_id_field=kwargs.get("file_id_field", "refer_voice_id"),
        prefer=kwargs.get("audio_format"),
        mime_type=kwargs.get("mime_type"),
    )
    return payload


def _cost(model=None, **kwargs):
    """Return unavailable MiniMax cost metadata."""
    return cost_utils.unavailable_cost_metadata(
        source="minimax_music_pricing",
        details={"model": model, **kwargs},
    )


def _headers():
    api_key = env_utils.require_env_var(ENV_NAME)
    return {"Authorization": f"Bearer {api_key}"}


def _audio_from_response(response):
    if isinstance(response, dict):
        for key in ("hex", "audio_hex", "audioHex"):
            value = response.get(key)
            if isinstance(value, str):
                return audio_from_hex(value)
    return None
