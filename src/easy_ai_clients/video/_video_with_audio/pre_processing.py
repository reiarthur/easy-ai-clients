"""Common video-with-audio input preparation."""

from .._shared import normalize_output_path


def prepare_video_with_audio(prompt=None, video_path=None, video_url=None, output_path=None):
    if video_path and video_url:
        raise ValueError("Provide either video_path or video_url, not both.")
    return {
        "prompt": str(prompt).strip() if prompt is not None else None,
        "video_path": video_path,
        "video_url": video_url,
        "output_path": normalize_output_path(output_path),
    }
