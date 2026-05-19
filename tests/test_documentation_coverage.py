"""Documentation coverage checks for public provider dispatchers."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _assert_doc(provider_doc: Path, providers_markdown: str) -> None:
    assert provider_doc.exists(), f"Missing provider doc: {provider_doc.relative_to(ROOT)}"
    relative = provider_doc.relative_to(DOCS).as_posix()
    assert relative in providers_markdown, f"docs/providers.md does not link {relative}"


def test_provider_docs_cover_public_dispatcher_matrices():
    from easy_ai_clients import account, audio, image, media, text, video, webhooks

    providers_markdown = (DOCS / "providers.md").read_text(encoding="utf-8")

    matrix = [
        *(("text", "", api) for api in text.available_apis()),
        *(("audio", "generate", api) for api in audio.available_synthesize_apis()),
        *(("audio", "transcribe", api) for api in audio.available_transcribe_apis()),
        *(("audio", "voices", api) for api in audio.available_voice_apis()),
        *(("image", "generate", api) for api in image.available_generate_apis()),
        *(("image", "edit", api) for api in image.available_edit_apis()),
        *(("image", "remix", api) for api in image.available_remix_apis()),
        *(("image", "analyze", api) for api in image.available_analyze_apis()),
        *(("video", "text_to_video", api) for api in video.available_text_to_video_apis()),
        *(("video", "image_to_video", api) for api in video.available_image_to_video_apis()),
        *(("video", "video_to_video", api) for api in video.available_video_to_video_apis()),
        *(("video", "motion_control", api) for api in video.available_motion_control_apis()),
        *(("video", "avatar_video", api) for api in video.available_avatar_video_apis()),
        *(("video", "video_with_audio", api) for api in video.available_video_with_audio_apis()),
        *(("video", "create_avatar", api) for api in video.available_create_avatar_apis()),
        *(("video", "image_lipsync", api) for api in video.available_image_lipsync_apis()),
        *(("video", "video_lipsync", api) for api in video.available_video_lipsync_apis()),
        *(("video", "agent_video", api) for api in video.available_agent_video_apis()),
        *(("video", "translate", api) for api in video.available_translate_apis()),
        *(("video", "resources", api) for api in video.available_video_resource_apis()),
        *(("media", "", api) for api in media.available_apis()),
        *(("webhooks", "", api) for api in webhooks.available_apis()),
        *(("account", "", api) for api in account.available_apis()),
    ]

    for category, operation, api in matrix:
        if operation:
            provider_doc = DOCS / category / operation / f"{api}.md"
        else:
            provider_doc = DOCS / category / f"{api}.md"
        _assert_doc(provider_doc, providers_markdown)


def test_cross_cutting_docs_include_all_helper_categories():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    usage = (DOCS / "usage.md").read_text(encoding="utf-8")
    examples = (DOCS / "operation_examples.md").read_text(encoding="utf-8")

    for token in (
        "audio.list_voices",
        "video.agent_video",
        "video.translate",
        "media.upload_asset",
        "webhooks.create_endpoint",
        "account.get_current_user",
    ):
        assert token in readme or token in usage
        assert token in examples

