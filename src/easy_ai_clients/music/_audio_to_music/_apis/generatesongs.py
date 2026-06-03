from ..._common import cost_utils, env_utils, http_utils
from ..post_processing import build_result, wait_for_result
from ..pre_processing import (
    add_prompt,
    audio_to_multipart_file,
    describe_audio,
    prepare_audio_to_music,
    without_internal_kwargs,
)

PROVIDER = "generatesongs"
ENV_NAME = "GENERATESONGS_API_KEY"
DEFAULT_MODEL = None
DEFAULT_BASE_URL = "https://generatesongs.ai/api/v1"
DEFAULT_ENDPOINT = f"{DEFAULT_BASE_URL}/songs/generate"
DEFAULT_UPLOAD_ENDPOINT = f"{DEFAULT_BASE_URL}/files/upload"

_PURPOSE_FIELDS = {
    "reference": "referenceFileId",
    "vocal": "vocalFileId",
    "melody": "melodyFileId",
}


def generate_audio_to_music(audio, prompt=None, output_path=None, sync=True, **kwargs):
    """Generate a song from GenerateSongs.ai reference file IDs."""
    model = kwargs.pop("model", DEFAULT_MODEL)
    endpoint = kwargs.pop("endpoint", DEFAULT_ENDPOINT)
    timeout = kwargs.pop("timeout", 60)
    retries = kwargs.pop("retries", 2)
    _prepare_audio_file_id(audio, kwargs, timeout=timeout, retries=retries)
    payload = _build_payload(audio, prompt=prompt, model=model, timeout=timeout, **kwargs)
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
        completed_statuses=("completed",),
    )
    return build_result(PROVIDER, model, final_response, output_path=output_path, cost=_cost(model=model))


def get_generation_status(request_id, model=None, **kwargs):
    """Fetch a GenerateSongs.ai song task."""
    base_url = kwargs.get("base_url", DEFAULT_BASE_URL)
    return http_utils.request_json(
        "GET",
        f"{base_url}/songs/{request_id}",
        headers=_headers(),
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
    )


def get_generation_result(request_id, output_path=None, model=None, **kwargs):
    """Fetch a GenerateSongs.ai song result."""
    response = get_generation_status(request_id, model=model, **kwargs)
    return build_result(PROVIDER, model, response, output_path=output_path)


def _build_payload(audio, prompt=None, model=None, **kwargs):
    """Build the GenerateSongs.ai payload."""
    prepare_audio_to_music(audio, prompt=prompt)
    payload = without_internal_kwargs(kwargs)
    add_prompt(payload, prompt, field_name=kwargs.get("prompt_field", "style"))
    if model is not None:
        payload.setdefault("model", model)
    _apply_file_id(payload, audio, **kwargs)
    return payload


def _apply_file_id(payload, audio, **kwargs):
    purpose = kwargs.get("purpose") or kwargs.get("reference_type") or "reference"
    field = kwargs.get("file_id_field") or _PURPOSE_FIELDS.get(purpose, "referenceFileId")
    explicit_fields = {
        "referenceFileId": kwargs.get("referenceFileId") or kwargs.get("reference_file_id"),
        "vocalFileId": kwargs.get("vocalFileId") or kwargs.get("vocal_file_id"),
        "melodyFileId": kwargs.get("melodyFileId") or kwargs.get("melody_file_id"),
    }
    explicit_fields = {
        key: value
        for key, value in explicit_fields.items()
        if value is not None
    }
    if explicit_fields:
        payload.update(explicit_fields)
        return
    if describe_audio(audio)["kind"] == "file_id":
        payload[field] = audio
        return

    raise ValueError("GenerateSongs.ai requires a provider file ID for _build_payload.")


def _prepare_audio_file_id(audio, kwargs, timeout=60, retries=2):
    explicit = (
        kwargs.get("referenceFileId")
        or kwargs.get("reference_file_id")
        or kwargs.get("vocalFileId")
        or kwargs.get("vocal_file_id")
        or kwargs.get("melodyFileId")
        or kwargs.get("melody_file_id")
    )
    if explicit or describe_audio(audio)["kind"] == "file_id":
        return

    purpose = kwargs.get("purpose") or kwargs.get("reference_type") or "reference"
    field = _PURPOSE_FIELDS.get(purpose, "referenceFileId")
    file_id = _upload_audio(audio, purpose=purpose, timeout=timeout, retries=retries, **kwargs)
    kwargs[field] = file_id


def _upload_audio(audio, purpose="reference", **kwargs):
    endpoint = kwargs.get("upload_endpoint", DEFAULT_UPLOAD_ENDPOINT)
    data = {"purpose": purpose}
    files = audio_to_multipart_file(
        audio,
        field_name=kwargs.get("file_field", "file"),
        filename=kwargs.get("filename"),
        mime_type=kwargs.get("mime_type"),
        timeout=kwargs.get("timeout", 60),
    )
    response = http_utils.multipart_request(
        "POST",
        endpoint,
        headers=_headers(),
        data=data,
        files=files,
        timeout=kwargs.get("timeout", 60),
        retries=kwargs.get("retries", 2),
    )
    raw_response = http_utils.response_json(response)
    data = raw_response.get("data")
    nested_id = data.get("id") if isinstance(data, dict) else None
    file_id = (
        raw_response.get("id")
        or raw_response.get("fileId")
        or raw_response.get("file_id")
        or nested_id
    )
    if not file_id:
        raise RuntimeError("GenerateSongs.ai upload did not return a file ID.")
    return file_id


def _cost(model=None, **kwargs):
    """Return GenerateSongs.ai credit cost metadata."""
    return cost_utils.unavailable_cost_metadata(
        source="generatesongs_credits",
        details={"credits": 1, "model": model, **kwargs},
    )


def _headers():
    api_key = env_utils.require_env_var(ENV_NAME)
    return {"Authorization": f"Bearer {api_key}"}


def _request_id(response):
    if isinstance(response, dict):
        return response.get("songId") or response.get("song_id") or response.get("id")
    return None
