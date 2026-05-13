"""Common image-to-video input preparation."""

from .._shared import clean_text, media_reference, normalize_output_path


def prepare_image_to_video(prompt, image_path=None, image_url=None, output_path=None):
    image = media_reference(image_path, image_url, "image_path", "image_url")
    if not image:
        raise ValueError("Image-to-video requires image_path, image_url, or image.")
    return {
        "prompt": clean_text(prompt, "prompt"),
        "image": image,
        "output_path": normalize_output_path(output_path),
    }
