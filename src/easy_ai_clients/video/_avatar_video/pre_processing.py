"""Common avatar-video input preparation."""

from .._shared import media_reference, normalize_output_path


def prepare_avatar_video(
    image_path=None,
    image_url=None,
    audio_path=None,
    audio_url=None,
    text=None,
    output_path=None,
):
    image = media_reference(image_path, image_url, "image_path", "image_url") if image_path or image_url else None
    audio = media_reference(audio_path, audio_url, "audio_path", "audio_url") if audio_path or audio_url else None
    prompt_text = str(text).strip() if text is not None else None
    return {
        "image": image,
        "audio": audio,
        "text": prompt_text,
        "output_path": normalize_output_path(output_path),
    }
