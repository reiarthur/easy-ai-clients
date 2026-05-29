"""Hugging Face text-to-video wrapper."""

from pathlib import Path

from ....image._common.http_utils import request
from ....image._common.provider_utils import response_json
from ..._shared import clean_text, normalize_output_path, normalize_result, require_env

DEFAULT_MODEL = "Wan-AI/Wan2.1-T2V-1.3B"
API_URL_TEMPLATE = "https://api-inference.huggingface.co/models/{model}"


def generate_text_to_video(prompt, output_path=None, sync=True, **kwargs):
    model = kwargs.pop("model", DEFAULT_MODEL)
    timeout_seconds = int(kwargs.pop("timeout_seconds", 900))
    payload = {"inputs": clean_text(prompt, "prompt"), "parameters": kwargs}
    response = request(
        "POST",
        API_URL_TEMPLATE.format(model=model),
        headers={
            "Authorization": f"Bearer {require_env('HUGGINGFACE_API_KEY', 'Hugging Face')}",
            "Accept": "video/mp4",
        },
        json=payload,
        timeout_seconds=timeout_seconds,
    )
    request_id = response.headers.get("x-request-id")
    target = normalize_output_path(output_path)
    video_url = None
    raw = {}
    if response.headers.get("content-type", "").startswith("application/json"):
        raw = response_json(response)
        from ..._shared import extract_video_url

        video_url = extract_video_url(raw)
    elif target:
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        Path(target).write_bytes(response.content)
    extra = {"cost_details": {"model": model}}
    if sync is False:
        extra["warnings"] = (
            "Hugging Face text-to-video is synchronous in this wrapper; "
            "sync=False is accepted for signature compatibility and does not create an async job."
        )
    return normalize_result(
        "huggingface",
        model,
        "completed",
        request_id,
        video_url,
        target,
        0.0,
        False,
        "unavailable",
        raw or {"bytes": len(response.content or b"")},
        extra,
    )


__all__ = ["API_URL_TEMPLATE", "DEFAULT_MODEL", "generate_text_to_video"]
