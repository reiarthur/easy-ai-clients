"""HeyGen v3 video resource-management adapter."""

from __future__ import annotations

from .... import _heygen
from ..._heygen_common import media_union


def _result(raw):
    return {"provider": "heygen", "data": _heygen.data(raw), "raw_response": raw}


def _params(kwargs):
    return {key: value for key, value in kwargs.items() if key != "timeout_seconds"}


def _payload(kwargs):
    return {key: value for key, value in kwargs.items() if key != "timeout_seconds"}


def _delete(path: str, *, confirm: bool, timeout_seconds: float | None = None):
    if confirm is not True:
        raise ValueError("Set confirm=True to execute destructive HeyGen delete operations.")
    return _result(_heygen.request_json("DELETE", path, timeout_seconds=timeout_seconds))


def list_videos(**kwargs):
    return _result(_heygen.request_json("GET", "/v3/videos", params=_params(kwargs), timeout_seconds=kwargs.get("timeout_seconds")))


def get_video(video_id, **kwargs):
    return _result(_heygen.request_json("GET", f"/v3/videos/{_heygen.quote_path(video_id)}", params=_params(kwargs), timeout_seconds=kwargs.get("timeout_seconds")))


def delete_video(video_id, *, confirm=False, **kwargs):
    return _delete(f"/v3/videos/{_heygen.quote_path(video_id)}", confirm=confirm, timeout_seconds=kwargs.get("timeout_seconds"))


def list_lipsyncs(**kwargs):
    return _result(_heygen.request_json("GET", "/v3/lipsyncs", params=_params(kwargs), timeout_seconds=kwargs.get("timeout_seconds")))


def get_lipsync(lipsync_id, **kwargs):
    return _result(_heygen.request_json("GET", f"/v3/lipsyncs/{_heygen.quote_path(lipsync_id)}", params=_params(kwargs), timeout_seconds=kwargs.get("timeout_seconds")))


def update_lipsync(lipsync_id, **kwargs):
    payload = {"title": kwargs.pop("title", None), **_payload(kwargs)}
    return _result(_heygen.request_json("PATCH", f"/v3/lipsyncs/{_heygen.quote_path(lipsync_id)}", payload=payload, timeout_seconds=kwargs.get("timeout_seconds")))


def delete_lipsync(lipsync_id, *, confirm=False, **kwargs):
    return _delete(f"/v3/lipsyncs/{_heygen.quote_path(lipsync_id)}", confirm=confirm, timeout_seconds=kwargs.get("timeout_seconds"))


def list_translations(**kwargs):
    return _result(_heygen.request_json("GET", "/v3/video-translations", params=_params(kwargs), timeout_seconds=kwargs.get("timeout_seconds")))


def get_translation(video_translation_id, **kwargs):
    return _result(_heygen.request_json("GET", f"/v3/video-translations/{_heygen.quote_path(video_translation_id)}", params=_params(kwargs), timeout_seconds=kwargs.get("timeout_seconds")))


def update_translation(video_translation_id, **kwargs):
    payload = {"title": kwargs.pop("title", None), **_payload(kwargs)}
    return _result(_heygen.request_json("PATCH", f"/v3/video-translations/{_heygen.quote_path(video_translation_id)}", payload=payload, timeout_seconds=kwargs.get("timeout_seconds")))


def delete_translation(video_translation_id, *, confirm=False, **kwargs):
    return _delete(f"/v3/video-translations/{_heygen.quote_path(video_translation_id)}", confirm=confirm, timeout_seconds=kwargs.get("timeout_seconds"))


def get_translation_caption(video_translation_id, **kwargs):
    params = _params(kwargs)
    return _result(_heygen.request_json("GET", f"/v3/video-translations/{_heygen.quote_path(video_translation_id)}/caption", params=params, timeout_seconds=kwargs.get("timeout_seconds")))


def list_translation_languages(**kwargs):
    return _result(_heygen.request_json("GET", "/v3/video-translations/languages", params=_params(kwargs), timeout_seconds=kwargs.get("timeout_seconds")))


def create_proofread(video=None, output_languages=None, title=None, **kwargs):
    languages = output_languages if output_languages is not None else kwargs.pop("output_languages", None)
    if isinstance(languages, str):
        languages = [languages]
    payload = {
        "video": media_union(
            kwargs.pop("video_path", None) or video,
            kwargs.pop("video_url", None),
            kwargs.pop("video_asset_id", None),
            field_name="video",
        ),
        "output_languages": languages,
        "title": title,
        **_payload(kwargs),
    }
    return _result(_heygen.request_json("POST", "/v3/video-translations/proofreads", payload=payload, timeout_seconds=kwargs.get("timeout_seconds")))


def get_proofread(proofread_id, **kwargs):
    return _result(_heygen.request_json("GET", f"/v3/video-translations/proofreads/{_heygen.quote_path(proofread_id)}", params=_params(kwargs), timeout_seconds=kwargs.get("timeout_seconds")))


def generate_proofread(proofread_id, **kwargs):
    return _result(_heygen.request_json("POST", f"/v3/video-translations/proofreads/{_heygen.quote_path(proofread_id)}/generate", payload=_payload(kwargs), timeout_seconds=kwargs.get("timeout_seconds")))


def get_proofread_srt(proofread_id, **kwargs):
    return _result(_heygen.request_json("GET", f"/v3/video-translations/proofreads/{_heygen.quote_path(proofread_id)}/srt", params=_params(kwargs), timeout_seconds=kwargs.get("timeout_seconds")))


def update_proofread_srt(proofread_id, srt=None, **kwargs):
    payload = {
        "srt": media_union(
            kwargs.pop("srt_path", None) or srt,
            kwargs.pop("srt_url", None),
            kwargs.pop("srt_asset_id", None),
            field_name="srt",
        ),
        **_payload(kwargs),
    }
    return _result(_heygen.request_json("PUT", f"/v3/video-translations/proofreads/{_heygen.quote_path(proofread_id)}/srt", payload=payload, timeout_seconds=kwargs.get("timeout_seconds")))


def list_avatars(**kwargs):
    return _result(_heygen.request_json("GET", "/v3/avatars", params=_params(kwargs), timeout_seconds=kwargs.get("timeout_seconds")))


def get_avatar(group_id, **kwargs):
    return _result(_heygen.request_json("GET", f"/v3/avatars/{_heygen.quote_path(group_id)}", params=_params(kwargs), timeout_seconds=kwargs.get("timeout_seconds")))


def delete_avatar(group_id, *, confirm=False, **kwargs):
    return _delete(f"/v3/avatars/{_heygen.quote_path(group_id)}", confirm=confirm, timeout_seconds=kwargs.get("timeout_seconds"))


def create_avatar_consent(group_id, **kwargs):
    return _result(_heygen.request_json("POST", f"/v3/avatars/{_heygen.quote_path(group_id)}/consent", payload=_payload(kwargs), timeout_seconds=kwargs.get("timeout_seconds")))


def list_avatar_looks(**kwargs):
    return _result(_heygen.request_json("GET", "/v3/avatars/looks", params=_params(kwargs), timeout_seconds=kwargs.get("timeout_seconds")))


def get_avatar_look(look_id, **kwargs):
    return _result(_heygen.request_json("GET", f"/v3/avatars/looks/{_heygen.quote_path(look_id)}", params=_params(kwargs), timeout_seconds=kwargs.get("timeout_seconds")))


def update_avatar_look(look_id, **kwargs):
    return _result(_heygen.request_json("PATCH", f"/v3/avatars/looks/{_heygen.quote_path(look_id)}", payload=_payload(kwargs), timeout_seconds=kwargs.get("timeout_seconds")))


def delete_avatar_look(look_id, *, confirm=False, **kwargs):
    return _delete(f"/v3/avatars/looks/{_heygen.quote_path(look_id)}", confirm=confirm, timeout_seconds=kwargs.get("timeout_seconds"))


def list_brand_kits(**kwargs):
    return _result(_heygen.request_json("GET", "/v3/brand-kits", params=_params(kwargs), timeout_seconds=kwargs.get("timeout_seconds")))


def list_agent_sessions(**kwargs):
    return _result(_heygen.request_json("GET", "/v3/video-agents", params=_params(kwargs), timeout_seconds=kwargs.get("timeout_seconds")))


def get_agent_session(session_id, **kwargs):
    return _result(_heygen.request_json("GET", f"/v3/video-agents/{_heygen.quote_path(session_id)}", params=_params(kwargs), timeout_seconds=kwargs.get("timeout_seconds")))


def send_agent_message(session_id, message, **kwargs):
    payload = {"message": message, **_payload(kwargs)}
    return _result(_heygen.request_json("POST", f"/v3/video-agents/{_heygen.quote_path(session_id)}", payload=payload, timeout_seconds=kwargs.get("timeout_seconds")))


def stop_agent_session(session_id, **kwargs):
    return _result(_heygen.request_json("POST", f"/v3/video-agents/{_heygen.quote_path(session_id)}/stop", payload={}, timeout_seconds=kwargs.get("timeout_seconds")))


def list_agent_styles(**kwargs):
    return _result(_heygen.request_json("GET", "/v3/video-agents/styles", params=_params(kwargs), timeout_seconds=kwargs.get("timeout_seconds")))


def get_agent_resource(session_id, resource_id, **kwargs):
    return _result(_heygen.request_json("GET", f"/v3/video-agents/{_heygen.quote_path(session_id)}/resources/{_heygen.quote_path(resource_id)}", params=_params(kwargs), timeout_seconds=kwargs.get("timeout_seconds")))


def list_agent_videos(session_id, **kwargs):
    return _result(_heygen.request_json("GET", f"/v3/video-agents/{_heygen.quote_path(session_id)}/videos", params=_params(kwargs), timeout_seconds=kwargs.get("timeout_seconds")))
