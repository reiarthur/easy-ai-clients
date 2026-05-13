"""Common motion-control input preparation."""

from .._shared import media_reference, normalize_output_path


def prepare_motion_control(prompt=None, image_path=None, image_url=None, video_path=None, video_url=None, reference_path=None, reference_url=None, output_path=None):
    image = media_reference(image_path, image_url, "image_path", "image_url")
    video = media_reference(video_path, video_url, "video_path", "video_url")
    reference = media_reference(reference_path, reference_url, "reference_path", "reference_url")
    return {
        "prompt": str(prompt).strip() if prompt is not None else None,
        "image": image,
        "video": video,
        "reference": reference,
        "output_path": normalize_output_path(output_path),
    }
