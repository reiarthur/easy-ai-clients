"""HeyGen text-to-video adapter backed by Video Agent v3."""

from ..._agent_video._apis.heygen import (
    download_generation,
    generate_agent_video,
    generate_agent_video_result,
    get_generation_result,
    get_generation_status,
)


def generate_text_to_video(prompt, output_path=None, sync=True, **kwargs):
    return generate_agent_video(prompt, output_path=output_path, sync=sync, **kwargs)


__all__ = [
    "download_generation",
    "generate_agent_video_result",
    "generate_text_to_video",
    "get_generation_result",
    "get_generation_status",
]

