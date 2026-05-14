"""Video dispatcher.

Exposes prompt, image, video, motion-control, avatar, and lip-sync video
generation through a single operation-aware dispatcher. The provider is selected via the ``api``
keyword argument and must match the file name (without ``.py``) of an internal
provider module.

Last updated: 2026-05-14
"""

from __future__ import annotations

import importlib
from typing import Any

from .._error_utils import attach_error, error_message

__all__ = [
    "generate",
    "text_to_video",
    "image_to_video",
    "video_to_video",
    "motion_control",
    "avatar_video",
    "video_with_audio",
    "create_avatar",
    "image_lipsync",
    "video_lipsync",
    "get_status",
    "get_result",
    "download",
    "available_apis",
    "available_text_to_video_apis",
    "available_image_to_video_apis",
    "available_video_to_video_apis",
    "available_motion_control_apis",
    "available_avatar_video_apis",
    "available_video_with_audio_apis",
    "available_create_avatar_apis",
    "available_image_lipsync_apis",
    "available_video_lipsync_apis",
]


_TEXT_TO_VIDEO_APIS = ("falai", "google", "hedra", "runway")
_IMAGE_TO_VIDEO_APIS = ("falai", "google", "hedra", "runway")
_VIDEO_TO_VIDEO_APIS = ("falai", "google", "hedra", "runway")
_MOTION_CONTROL_APIS = ("falai", "hedra", "runway")
_AVATAR_VIDEO_APIS = ("falai", "hedra", "runway")
_VIDEO_WITH_AUDIO_APIS = ("hedra",)
_CREATE_AVATAR_APIS = ("runway",)
_IMAGE_LIPSYNC_APIS = ("falai",)
_VIDEO_LIPSYNC_APIS = ("falai",)

_OPERATION_APIS = {
    "text_to_video": _TEXT_TO_VIDEO_APIS,
    "image_to_video": _IMAGE_TO_VIDEO_APIS,
    "video_to_video": _VIDEO_TO_VIDEO_APIS,
    "motion_control": _MOTION_CONTROL_APIS,
    "avatar_video": _AVATAR_VIDEO_APIS,
    "video_with_audio": _VIDEO_WITH_AUDIO_APIS,
    "create_avatar": _CREATE_AVATAR_APIS,
    "image_lipsync": _IMAGE_LIPSYNC_APIS,
    "video_lipsync": _VIDEO_LIPSYNC_APIS,
}

_OPERATION_FUNCTIONS = {
    "text_to_video": "generate_text_to_video",
    "image_to_video": "generate_image_to_video",
    "video_to_video": "generate_video_to_video",
    "motion_control": "generate_motion_control",
    "avatar_video": "generate_avatar_video",
    "video_with_audio": "generate_video_with_audio",
    "create_avatar": "create_avatar",
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


def available_video_to_video_apis():
    """Return the tuple of supported video-to-video provider identifiers."""

    return _VIDEO_TO_VIDEO_APIS


def available_motion_control_apis():
    """Return the tuple of supported motion-control provider identifiers."""

    return _MOTION_CONTROL_APIS


def available_avatar_video_apis():
    """Return the tuple of supported avatar-video provider identifiers."""

    return _AVATAR_VIDEO_APIS


def available_video_with_audio_apis():
    """Return the tuple of supported video-with-audio provider identifiers."""

    return _VIDEO_WITH_AUDIO_APIS


def available_create_avatar_apis():
    """Return the tuple of supported avatar-creation provider identifiers."""

    return _CREATE_AVATAR_APIS


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

    try:
        module = _load_module("text_to_video", api)
        function = getattr(module, _OPERATION_FUNCTIONS["text_to_video"])
        return function(prompt, **_arguments_with_model(model, kwargs))
    except Exception as exc:
        return _video_failure(exc, api=api, operation="text_to_video", model=model)


def image_to_video(prompt, image=None, model=None, *, api, **kwargs):
    """Generate video from a prompt and source image."""

    try:
        module = _load_module("image_to_video", api)
        function = getattr(module, _OPERATION_FUNCTIONS["image_to_video"])
        arguments = _arguments_with_model(model, kwargs)
        _apply_media_argument(arguments, image, "image_path", "image_url", "image")
        return function(prompt, **arguments)
    except Exception as exc:
        return _video_failure(exc, api=api, operation="image_to_video", model=model)


def video_to_video(
    prompt=None,
    video=None,
    image=None,
    reference=None,
    model=None,
    *,
    api,
    **kwargs,
):
    """Generate video from a source video, optional prompt, and optional references."""

    try:
        module = _load_module("video_to_video", api)
        function = getattr(module, _OPERATION_FUNCTIONS["video_to_video"])
        arguments = _arguments_with_model(model, kwargs)
        _apply_media_argument(arguments, video, "video_path", "video_url", "video")
        _apply_media_argument(arguments, image, "image_path", "image_url", "image")
        _apply_media_argument(
            arguments,
            reference,
            "reference_path",
            "reference_url",
            "reference",
        )
        return function(prompt=prompt, **arguments)
    except Exception as exc:
        return _video_failure(exc, api=api, operation="video_to_video", model=model)


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

    try:
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
    except Exception as exc:
        return _video_failure(exc, api=api, operation="motion_control", model=model)


def avatar_video(avatar=None, image=None, audio=None, text=None, model=None, *, api, **kwargs):
    """Generate an avatar or talking-video clip from an avatar/image and speech input."""

    try:
        module = _load_module("avatar_video", api)
        function = getattr(module, _OPERATION_FUNCTIONS["avatar_video"])
        arguments = _arguments_with_model(model, kwargs)
        _apply_media_argument(arguments, image, "image_path", "image_url", "image")
        _apply_media_argument(arguments, audio, "audio_path", "audio_url", "audio")
        if avatar is not None:
            arguments["avatar"] = avatar
        return function(text=text, **arguments)
    except Exception as exc:
        return _video_failure(exc, api=api, operation="avatar_video", model=model)


def video_with_audio(video=None, prompt=None, model=None, *, api, **kwargs):
    """Generate or add audio for a source video with the selected provider."""

    try:
        module = _load_module("video_with_audio", api)
        function = getattr(module, _OPERATION_FUNCTIONS["video_with_audio"])
        arguments = _arguments_with_model(model, kwargs)
        _apply_media_argument(arguments, video, "video_path", "video_url", "video")
        return function(prompt=prompt, **arguments)
    except Exception as exc:
        return _video_failure(exc, api=api, operation="video_with_audio", model=model)


def create_avatar(image=None, name=None, voice=None, *, api, **kwargs):
    """Create a provider avatar/persona from a source image."""

    try:
        module = _load_module("create_avatar", api)
        function = getattr(module, _OPERATION_FUNCTIONS["create_avatar"])
        arguments = dict(kwargs)
        _apply_media_argument(arguments, image, "image_path", "image_url", "image")
        return function(name=name, voice=voice, **arguments)
    except Exception as exc:
        return _video_failure(exc, api=api, operation="create_avatar", model=None)


def image_lipsync(image=None, audio=None, text=None, model=None, *, api, **kwargs):
    """Generate a lip-synced video from a source image and audio."""

    try:
        module = _load_module("image_lipsync", api)
        function = getattr(module, _OPERATION_FUNCTIONS["image_lipsync"])
        arguments = _arguments_with_model(model, kwargs)
        _apply_media_argument(arguments, image, "image_path", "image_url", "image")
        _apply_media_argument(arguments, audio, "audio_path", "audio_url", "audio")
        return function(text=text, **arguments)
    except Exception as exc:
        return _video_failure(exc, api=api, operation="image_lipsync", model=model)


def video_lipsync(video=None, audio=None, text=None, model=None, *, api, **kwargs):
    """Generate a lip-synced video from a source video and audio."""

    try:
        module = _load_module("video_lipsync", api)
        function = getattr(module, _OPERATION_FUNCTIONS["video_lipsync"])
        arguments = _arguments_with_model(model, kwargs)
        _apply_media_argument(arguments, video, "video_path", "video_url", "video")
        _apply_media_argument(arguments, audio, "audio_path", "audio_url", "audio")
        return function(text=text, **arguments)
    except Exception as exc:
        return _video_failure(exc, api=api, operation="video_lipsync", model=model)


def get_status(operation, request_id, model=None, *, api, **kwargs):
    """Fetch provider status for an async video generation request."""

    operation_name = str(operation or "").strip()
    try:
        module = _load_module(operation_name, api)
        if not hasattr(module, "get_generation_status"):
            raise NotImplementedError(
                f"video.get_status is not implemented for operation='{operation}' "
                f"and api='{api}'."
            )
        return module.get_generation_status(request_id, **_arguments_with_model(model, kwargs))
    except Exception as exc:
        return _video_failure(exc, api=api, operation=operation_name or "get_status", model=model)


def get_result(operation, request_id, output_path=None, model=None, *, api, **kwargs):
    """Fetch a completed async video generation result."""

    operation_name = str(operation or "").strip()
    try:
        module = _load_module(operation_name, api)
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
    except Exception as exc:
        return _video_failure(
            exc,
            api=api,
            operation=operation_name or "get_result",
            model=model,
            output_path=output_path,
        )


def download(operation, request_id=None, video_url=None, output_path=None, model=None, *, api, **kwargs):
    """Download a generated video by request ID or direct provider URL."""

    operation_name = str(operation or "").strip()
    try:
        module = _load_module(operation_name, api)
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
    except Exception as exc:
        return _video_failure(
            exc,
            api=api,
            operation=operation_name or "download",
            model=model,
            output_path=output_path,
        )


def _video_failure(exc, *, api, operation, model, output_path=None):
    message = error_message(exc)
    return attach_error(
        {
            "provider": api,
            "model": model,
            "status": "failed",
            "request_id": None,
            "video_url": None,
            "output_path": output_path,
            "cost_usd": 0.0,
            "cost_is_estimated": True,
            "cost_source": "unavailable",
            "raw_response": {},
            "warnings": message,
        },
        exc,
        provider=api,
        operation=operation,
        model=model,
    )
