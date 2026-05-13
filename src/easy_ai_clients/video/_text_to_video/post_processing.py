"""Common text-to-video result helpers."""

from .._shared import download_file, normalize_result


def build_result(provider, model, status, request_id, video_url, output_path, cost_usd, cost_is_estimated, cost_source, raw_response, extra=None, download_headers=None):
    saved_path = output_path
    if video_url and output_path and status == "completed":
        saved_path = download_file(video_url, output_path, headers=download_headers)
    return normalize_result(provider, model, status, request_id, video_url, saved_path, cost_usd, cost_is_estimated, cost_source, raw_response, extra)
