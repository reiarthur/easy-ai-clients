"""Common video-to-video input preparation."""

from .._shared import media_reference, normalize_output_path


def prepare_video_to_video(
    prompt=None,
    video_path=None,
    video_url=None,
    image_path=None,
    image_url=None,
    reference_path=None,
    reference_url=None,
    output_path=None,
):
    video = media_reference(video_path, video_url, "video_path", "video_url")
    if not video:
        raise ValueError("Video-to-video requires video_path, video_url, or video.")
    image = media_reference(image_path, image_url, "image_path", "image_url")
    reference = media_reference(reference_path, reference_url, "reference_path", "reference_url")
    return {
        "prompt": str(prompt).strip() if prompt is not None else None,
        "video": video,
        "image": image,
        "reference": reference,
        "output_path": normalize_output_path(output_path),
    }
