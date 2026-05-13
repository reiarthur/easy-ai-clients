"""Common image lip-sync input preparation."""

from .._shared import clean_text, media_reference, normalize_output_path


def prepare_image_lipsync(image_path=None, image_url=None, audio_path=None, audio_url=None, text=None, output_path=None, allow_text=False, allow_preset=False, preset_value=None):
    image = media_reference(image_path, image_url, "image_path", "image_url")
    if not image and not (allow_preset and preset_value):
        raise ValueError("Image lip sync requires image_path, image_url, or a supported provider preset avatar.")
    audio = media_reference(audio_path, audio_url, "audio_path", "audio_url")
    speech_text = None
    if text is not None:
        speech_text = clean_text(text, "text")
    if not audio and not (allow_text and speech_text):
        raise ValueError("Image lip sync requires audio_path, audio_url, or supported text input.")
    if audio and speech_text:
        raise ValueError("Provide audio_path/audio_url or text, not both.")
    return {
        "image": image,
        "audio": audio,
        "text": speech_text,
        "preset": preset_value,
        "output_path": normalize_output_path(output_path),
    }
