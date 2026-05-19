"""xAI image-to-video wrapper."""

from ... import _xai_video_common as common

DEFAULT_MODEL = common.DEFAULT_MODEL


def generate_image_to_video(prompt, image_path=None, image_url=None, output_path=None, sync=True, **kwargs):
    model = kwargs.pop("model", DEFAULT_MODEL)
    body = common.payload(model, prompt, kwargs)
    image = common.media_object(image_path, image_url, "image_path", "image_url")
    if not image:
        raise ValueError("xAI image_to_video requires image_path or image_url.")
    body["image"] = image
    return common.finalize(
        endpoint="/videos/generations",
        model=model,
        payload_value=body,
        output_path=output_path,
        sync=bool(sync),
        timeout_seconds=kwargs.get("timeout_seconds"),
        poll_interval_seconds=kwargs.get("poll_interval_seconds"),
    )


def get_generation_status(request_id, **kwargs):
    model = kwargs.get("model", DEFAULT_MODEL)
    raw = common.get_video(request_id, timeout_seconds=kwargs.get("timeout_seconds"))
    return {"provider": common.PROVIDER, "model": model, "request_id": request_id, "status": common.status(raw.get("status")), "raw_response": raw}


def get_generation_result(request_id, output_path=None, **kwargs):
    from ..._shared import extract_video_url, normalize_output_path, normalize_result

    model = kwargs.get("model", DEFAULT_MODEL)
    raw = common.get_video(request_id, timeout_seconds=kwargs.get("timeout_seconds"))
    pricing = common.cost(model, kwargs)
    return normalize_result(common.PROVIDER, model, common.status(raw.get("status")), request_id, extract_video_url(raw), normalize_output_path(output_path), pricing["cost_usd"], pricing["cost_is_estimated"], pricing["cost_source"], raw, {"cost_details": pricing["cost_details"]})


def download_generation(request_id=None, video_url=None, output_path=None, **kwargs):
    from ..._shared import download_file, normalize_output_path

    if video_url:
        return download_file(video_url, normalize_output_path(output_path))
    return get_generation_result(request_id, output_path=output_path, **kwargs)


__all__ = ["DEFAULT_MODEL", "download_generation", "generate_image_to_video", "get_generation_result", "get_generation_status"]
