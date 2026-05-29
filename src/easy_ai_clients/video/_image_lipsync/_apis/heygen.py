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


def get_generation_status(request_id, **kwargs):
    from ..._avatar_video._apis.heygen import get_generation_status as _get_generation_status

    return _get_generation_status(request_id, **kwargs)


def get_generation_result(request_id, output_path=None, **kwargs):
    from ..._avatar_video._apis.heygen import get_generation_result as _get_generation_result

    return _get_generation_result(request_id, output_path=output_path, **kwargs)


def download_generation(request_id=None, video_url=None, output_path=None, **kwargs):
    from ..._avatar_video._apis.heygen import download_generation as _download_generation

    return _download_generation(
        request_id=request_id,
        video_url=video_url,
        output_path=output_path,
        **kwargs,
    )
