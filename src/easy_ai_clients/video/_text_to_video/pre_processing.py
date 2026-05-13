"""Common text-to-video input preparation."""

from .._shared import clean_text, normalize_output_path


def prepare_text_to_video(prompt, output_path=None):
    return {
        "prompt": clean_text(prompt, "prompt"),
        "output_path": normalize_output_path(output_path),
    }
