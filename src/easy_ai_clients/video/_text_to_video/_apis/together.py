"""Together AI text-to-video wrapper."""

from ... import _together_common as common

DEFAULT_MODEL = "Wan-AI/Wan2.2-T2V-A14B"


def generate_text_to_video(prompt, output_path=None, sync=True, **kwargs):
    model = kwargs.pop("model", DEFAULT_MODEL)
    payload = common.common_payload(model, prompt, kwargs)
    return common.finalize_or_submit(
        model=model,
        payload=payload,
        output_path=output_path,
        sync=bool(sync),
        timeout_seconds=kwargs.get("timeout_seconds"),
        poll_interval_seconds=kwargs.get("poll_interval_seconds"),
    )


def get_generation_status(request_id, **kwargs):
    model = kwargs.get("model", DEFAULT_MODEL)
    raw = common.get_video(request_id, timeout_seconds=kwargs.get("timeout_seconds"))
    return {"provider": common.PROVIDER, "model": model, "request_id": request_id, "status": common.normalize_status(raw.get("status")), "raw_response": raw}


def get_generation_result(request_id, output_path=None, **kwargs):
    model = kwargs.get("model", DEFAULT_MODEL)
    raw = common.get_video(request_id, timeout_seconds=kwargs.get("timeout_seconds"))
    return common.build_result(
        model=model,
        status=common.normalize_status(raw.get("status")),
        request_id_value=request_id,
        video_url=common.extract_video_url(raw) if hasattr(common, "extract_video_url") else None,
        output_path=output_path,
        raw=raw,
        cost_metadata=common.cost(model, kwargs),
    )


def download_generation(request_id=None, video_url=None, output_path=None, **kwargs):
    from ..._shared import download_file, normalize_output_path

    if video_url:
        return download_file(video_url, normalize_output_path(output_path))
    return get_generation_result(request_id, output_path=output_path, **kwargs)


__all__ = ["DEFAULT_MODEL", "download_generation", "generate_text_to_video", "get_generation_result", "get_generation_status"]
