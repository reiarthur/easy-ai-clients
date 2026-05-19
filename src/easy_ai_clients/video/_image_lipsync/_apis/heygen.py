"""HeyGen image lip-sync adapter backed by POST /v3/videos type=image."""

from ..._avatar_video._apis.heygen import generate_avatar_video


def generate_image_lipsync(image_path=None, image_url=None, audio_path=None, audio_url=None, text=None, output_path=None, sync=True, **kwargs):
    return generate_avatar_video(
        image_path=image_path,
        image_url=image_url,
        audio_path=audio_path,
        audio_url=audio_url,
        text=text,
        output_path=output_path,
        sync=sync,
        **kwargs,
    )
