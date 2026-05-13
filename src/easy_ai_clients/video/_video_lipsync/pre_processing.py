"""Common video lip-sync input preparation."""

from .._shared import clean_text, media_reference, normalize_output_path


def prepare_video_lipsync(video_path=None, video_url=None, audio_path=None, audio_url=None, text=None, output_path=None, allow_text=False):
    video = media_reference(video_path, video_url, "video_path", "video_url")
    if not video:
        raise ValueError("Video lip sync requires video_path or video_url.")
    audio = media_reference(audio_path, audio_url, "audio_path", "audio_url")
    speech_text = None
    if text is not None:
        speech_text = clean_text(text, "text")
    if not audio and not (allow_text and speech_text):
        raise ValueError("Video lip sync requires audio_path or audio_url for this provider.")
    if audio and speech_text:
        raise ValueError("Provide audio_path/audio_url or text, not both.")
    return {
        "video": video,
        "audio": audio,
        "text": speech_text,
        "output_path": normalize_output_path(output_path),
    }
