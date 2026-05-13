"""Video dispatcher.

Exposes prompt, image, motion-control, and lip-sync video generation through a
single operation-aware dispatcher. The provider is selected via the ``api``
keyword argument and must match the file name (without ``.py``) of an internal
provider module.

Last updated: 2026-05-13
"""

from __future__ import annotations

import importlib
from typing import Any

__all__ = [
    "generate",
    "text_to_video",
    "image_to_video",
    "motion_control",
    "image_lipsync",
    "video_lipsync",
    "get_status",
    "get_result",
    "download",
    "available_apis",
    "available_text_to_video_apis",
    "available_image_to_video_apis",
    "available_motion_control_apis",
    "available_image_lipsync_apis",
    "available_video_lipsync_apis",
]


_TEXT_TO_VIDEO_APIS = ("falai", "google", "runway")
_IMAGE_TO_VIDEO_APIS = ("falai", "google", "runway")
_MOTION_CONTROL_APIS = ("falai", "runway")
_IMAGE_LIPSYNC_APIS = ("falai",)
_VIDEO_LIPSYNC_APIS = ("falai",)

_OPERATION_APIS = {
    "text_to_video": _TEXT_TO_VIDEO_APIS,
    "image_to_video": _IMAGE_TO_VIDEO_APIS,
    "motion_control": _MOTION_CONTROL_APIS,
    "image_lipsync": _IMAGE_LIPSYNC_APIS,
    "video_lipsync": _VIDEO_LIPSYNC_APIS,
}

_OPERATION_FUNCTIONS = {
    "text_to_video": "generate_text_to_video",
    "image_to_video": "generate_image_to_video",
    "motion_control": "generate_motion_control",
    "image_lipsync": "generate_image_lipsync",
    "video_lipsync": "generate_video_lipsync",
}


def available_apis():
    """Return the tuple of supported prompt-to-video provider identifiers."""

    return _TEXT_TO_VIDEO_APIS


def available_text_to_video_apis():
    """Return the tuple of supported text-to-video provider identifiers."""

    return _TEXT_TO_VIDEO_APIS


def available_image_to_video_apis():
    """Return the tuple of supported image-to-video provider identifiers."""

    return _IMAGE_TO_VIDEO_APIS


def available_motion_control_apis():
    """Return the tuple of supported motion-control provider identifiers."""

    return _MOTION_CONTROL_APIS


def available_image_lipsync_apis():
    """Return the tuple of supported image lip-sync provider identifiers."""

    return _IMAGE_LIPSYNC_APIS


def available_video_lipsync_apis():
    """Return the tuple of supported video lip-sync provider identifiers."""

    return _VIDEO_LIPSYNC_APIS


def _operation_names():
    return tuple(_OPERATION_APIS)


def _load_module(operation, api):
    if operation not in _OPERATION_APIS:
        raise ValueError(
            "video operation must be one of: " f"{', '.join(_operation_names())}."
        )

    allowed = _OPERATION_APIS[operation]
    if not isinstance(api, str) or not api:
        raise ValueError(
            f"video.{operation}(...) requires the keyword argument 'api'. "
            f"Available APIs: {', '.join(allowed)}."
        )
    if api not in allowed:
        raise ValueError(
            f"Unknown video {operation} API '{api}'. Available APIs: "
            f"{', '.join(allowed)}."
        )
    return importlib.import_module(f"._{operation}._apis.{api}", __name__)


def _arguments_with_model(model, kwargs):
    arguments: dict[str, Any] = dict(kwargs)
    if model is not None:
        arguments["model"] = model
    return arguments


def _is_remote_or_data(value):
    if not isinstance(value, str):
        return False
    normalized = value.strip().lower()
    return normalized.startswith(("http://", "https://", "data:"))


def _apply_media_argument(arguments, value, path_name, url_name, public_name):
    if value is None:
        return
    if arguments.get(path_name) is not None or arguments.get(url_name) is not None:
        raise ValueError(
            f"Provide either {public_name} or {path_name}/{url_name}, not both."
        )
    if _is_remote_or_data(value):
        arguments[url_name] = value
    else:
        arguments[path_name] = value


def generate(prompt, model=None, *, api, **kwargs):
    """Generate video from a text prompt.

    This is an alias for :func:`text_to_video`, matching the package convention
    that ``generate`` is the simplest creation path for a modality.
    """

    return text_to_video(prompt, model=model, api=api, **kwargs)


def text_to_video(prompt, model=None, *, api, **kwargs):
    """Generate video from a text prompt with the selected provider."""

    module = _load_module("text_to_video", api)
    function = getattr(module, _OPERATION_FUNCTIONS["text_to_video"])
    return function(prompt, **_arguments_with_model(model, kwargs))


def image_to_video(prompt, image=None, model=None, *, api, **kwargs):
    """Generate video from a prompt and source image."""

    module = _load_module("image_to_video", api)
    function = getattr(module, _OPERATION_FUNCTIONS["image_to_video"])
    arguments = _arguments_with_model(model, kwargs)
    _apply_media_argument(arguments, image, "image_path", "image_url", "image")
    return function(prompt, **arguments)


def motion_control(
    prompt=None,
    image=None,
    video=None,
    reference=None,
    model=None,
    *,
    api,
    **kwargs,
):
    """Generate video by applying a motion reference or performance source."""

    module = _load_module("motion_control", api)
    function = getattr(module, _OPERATION_FUNCTIONS["motion_control"])
    arguments = _arguments_with_model(model, kwargs)
    _apply_media_argument(arguments, image, "image_path", "image_url", "image")
    _apply_media_argument(arguments, video, "video_path", "video_url", "video")
    _apply_media_argument(
        arguments,
        reference,
        "reference_path",
        "reference_url",
        "reference",
    )
    return function(prompt=prompt, **arguments)


def image_lipsync(image=None, audio=None, text=None, model=None, *, api, **kwargs):
    """Generate a lip-synced video from a source image and audio."""

    module = _load_module("image_lipsync", api)
    function = getattr(module, _OPERATION_FUNCTIONS["image_lipsync"])
    arguments = _arguments_with_model(model, kwargs)
    _apply_media_argument(arguments, image, "image_path", "image_url", "image")
    _apply_media_argument(arguments, audio, "audio_path", "audio_url", "audio")
    return function(text=text, **arguments)


def video_lipsync(video=None, audio=None, text=None, model=None, *, api, **kwargs):
    """Generate a lip-synced video from a source video and audio."""

    module = _load_module("video_lipsync", api)
    function = getattr(module, _OPERATION_FUNCTIONS["video_lipsync"])
    arguments = _arguments_with_model(model, kwargs)
    _apply_media_argument(arguments, video, "video_path", "video_url", "video")
    _apply_media_argument(arguments, audio, "audio_path", "audio_url", "audio")
    return function(text=text, **arguments)


def get_status(operation, request_id, model=None, *, api, **kwargs):
    """Fetch provider status for an async video generation request."""

    module = _load_module(str(operation or "").strip(), api)
    if not hasattr(module, "get_generation_status"):
        raise NotImplementedError(
            f"video.get_status is not implemented for operation='{operation}' "
            f"and api='{api}'."
        )
    return module.get_generation_status(request_id, **_arguments_with_model(model, kwargs))


def get_result(operation, request_id, output_path=None, model=None, *, api, **kwargs):
    """Fetch a completed async video generation result."""

    module = _load_module(str(operation or "").strip(), api)
    if not hasattr(module, "get_generation_result"):
        raise NotImplementedError(
            f"video.get_result is not implemented for operation='{operation}' "
            f"and api='{api}'."
        )
    return module.get_generation_result(
        request_id,
        output_path=output_path,
        **_arguments_with_model(model, kwargs),
    )


def download(operation, request_id=None, video_url=None, output_path=None, model=None, *, api, **kwargs):
    """Download a generated video by request ID or direct provider URL."""

    module = _load_module(str(operation or "").strip(), api)
    if not hasattr(module, "download_generation"):
        raise NotImplementedError(
            f"video.download is not implemented for operation='{operation}' "
            f"and api='{api}'."
        )
    return module.download_generation(
        request_id=request_id,
        video_url=video_url,
        output_path=output_path,
        **_arguments_with_model(model, kwargs),
    )
