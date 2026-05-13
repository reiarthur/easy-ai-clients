"""Video integration contract tests that avoid real provider calls."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_video_docs_match_dispatcher_provider_matrix():
    from easy_ai_clients import video

    matrix = {
        "text_to_video": video.available_text_to_video_apis(),
        "image_to_video": video.available_image_to_video_apis(),
        "motion_control": video.available_motion_control_apis(),
        "image_lipsync": video.available_image_lipsync_apis(),
        "video_lipsync": video.available_video_lipsync_apis(),
    }
    providers_doc = (ROOT / "docs" / "providers.md").read_text(encoding="utf-8")

    for operation, apis in matrix.items():
        for api in apis:
            doc_path = ROOT / "docs" / "video" / operation / f"{api}.md"
            assert doc_path.exists(), f"Missing video docs for {operation}/{api}"
            assert f"video/{operation}/{api}.md" in providers_doc


def test_video_env_vars_are_documented_and_templated():
    env_example = (ROOT / ".env.example").read_text(encoding="utf-8")
    configuration = (ROOT / "docs" / "configuration.md").read_text(encoding="utf-8")
    providers = (ROOT / "docs" / "providers.md").read_text(encoding="utf-8")

    for name in ("FAL_KEY", "GOOGLE_API_KEY", "RUNWAYML_API_SECRET"):
        assert name in env_example
        assert name in configuration
        assert name in providers

    assert "HEDRA_API_KEY" in env_example
    assert "reserved" in configuration.lower()


def test_video_dispatcher_public_exports_do_not_expose_private_helpers():
    from easy_ai_clients import video

    expected = {
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
    }

    assert set(video.__all__) == expected
    assert all(not name.startswith("_") for name in video.__all__)


def test_google_text_to_video_payload_endpoint_and_cost(monkeypatch):
    from easy_ai_clients.video._text_to_video._apis import google as provider

    captured = {}

    def fake_http_json(method, url, headers=None, payload=None, timeout_seconds=None):
        captured.update(
            method=method,
            url=url,
            headers=headers,
            payload=payload,
            timeout_seconds=timeout_seconds,
        )
        return {"name": "operations/google-video-1"}

    monkeypatch.setenv("GOOGLE_API_KEY", "test-google")
    monkeypatch.setattr(provider, "http_json", fake_http_json)

    result = provider.generate_text_to_video(
        "A quiet product shot.",
        duration_seconds=4,
        resolution="720p",
        sync=False,
        timeout_seconds=30,
    )

    assert result["status"] == "submitted"
    assert result["request_id"] == "operations/google-video-1"
    assert result["cost_usd"] == pytest.approx(0.20)
    assert captured["method"] == "POST"
    assert captured["url"].endswith(
        "/models/veo-3.1-lite-generate-preview:predictLongRunning"
    )
    assert captured["headers"]["x-goog-api-key"] == "test-google"
    assert captured["payload"]["instances"] == [{"prompt": "A quiet product shot."}]
    assert captured["payload"]["parameters"]["durationSeconds"] == 4
    assert captured["payload"]["parameters"]["resolution"] == "720p"


def test_google_veo_official_pricing_snapshot_values():
    from easy_ai_clients.video._text_to_video._apis import google as provider

    fast_4k = provider._cost(  # noqa: SLF001
        "veo-3.1-fast-generate-preview",
        {"duration_seconds": 8, "resolution": "4k"},
    )
    veo2 = provider._cost(  # noqa: SLF001
        "veo-2.0-generate-001",
        {"duration_seconds": 5, "resolution": "720p", "number_of_videos": 2},
    )

    assert fast_4k["cost_usd"] == pytest.approx(2.40)
    assert veo2["cost_usd"] == pytest.approx(3.50)
    assert fast_4k["cost_is_estimated"] is True


def test_runway_text_to_video_payload_endpoint_and_cost(monkeypatch):
    from easy_ai_clients.video._text_to_video._apis import runway as provider

    captured = {}

    def fake_submit(endpoint, payload, api_key, timeout_seconds=None):
        captured.update(
            endpoint=endpoint,
            payload=payload,
            api_key=api_key,
            timeout_seconds=timeout_seconds,
        )
        return {"id": "runway-task-1"}

    monkeypatch.setenv("RUNWAYML_API_SECRET", "test-runway")
    monkeypatch.setattr(provider, "runway_submit", fake_submit)

    result = provider.generate_text_to_video(
        "A calm mountain landscape.",
        model="gen4.5",
        duration=2,
        ratio="1280:720",
        seed=123,
        sync=False,
    )

    assert result["status"] == "submitted"
    assert result["request_id"] == "runway-task-1"
    assert result["cost_usd"] == pytest.approx(0.24)
    assert result["cost_credits"] == pytest.approx(24)
    assert captured["endpoint"] == "/v1/text_to_video"
    assert captured["api_key"] == "test-runway"
    assert captured["payload"] == {
        "model": "gen4.5",
        "promptText": "A calm mountain landscape.",
        "ratio": "1280:720",
        "duration": 2,
        "seed": 123,
    }


def test_runway_model_specific_restrictions_and_audio_pricing():
    from easy_ai_clients.video._text_to_video._apis import runway as provider

    with pytest.raises(ValueError, match="audio is not supported"):
        provider._build_payload(  # noqa: SLF001
            "gen4.5",
            {"prompt": "A test.", "output_path": None},
            {"audio": True},
        )

    audio_cost = provider._cost(  # noqa: SLF001
        "veo3.1_fast",
        {"duration": 4, "audio": True},
    )
    assert audio_cost["cost_usd"] == pytest.approx(0.60)
    assert audio_cost["cost_credits"] == pytest.approx(60)

    default_audio_off_payload = provider._build_payload(  # noqa: SLF001
        "veo3.1_fast",
        {"prompt": "A test.", "output_path": None},
        {"duration": 4},
    )
    default_audio_off_cost = provider._cost(  # noqa: SLF001
        "veo3.1_fast",
        {"duration": 4},
    )
    assert default_audio_off_payload["audio"] is False
    assert default_audio_off_cost["cost_usd"] == pytest.approx(0.40)

    with pytest.raises(ValueError, match="integer"):
        provider._build_payload(  # noqa: SLF001
            "gen4.5",
            {"prompt": "A test.", "output_path": None},
            {"duration": 2.5},
        )


def test_falai_text_to_video_payload_endpoint_and_limits(monkeypatch):
    from easy_ai_clients.video._text_to_video._apis import falai as provider

    captured = {}

    def fake_submit(model, payload, api_key, timeout_seconds=None):
        captured.update(
            model=model,
            payload=payload,
            api_key=api_key,
            timeout_seconds=timeout_seconds,
        )
        return {"request_id": "fal-request-1"}

    monkeypatch.setenv("FAL_KEY", "test-fal")
    monkeypatch.setattr(provider, "fal_submit", fake_submit)

    result = provider.generate_text_to_video(
        "A short establishing shot.",
        num_frames=81,
        frames_per_second=16,
        seed=123,
        resolution="720p",
        sync=False,
    )

    assert result["status"] == "submitted"
    assert result["request_id"] == "fal-request-1"
    assert result["cost_usd"] == pytest.approx(0.08)
    assert captured["model"] == provider.DEFAULT_MODEL
    assert captured["api_key"] == "test-fal"
    assert captured["payload"]["prompt"] == "A short establishing shot."
    assert captured["payload"]["num_frames"] == 81
    assert captured["payload"]["frames_per_second"] == 16

    with pytest.raises(ValueError, match="17 to 161"):
        provider._build_payload(  # noqa: SLF001
            provider.DEFAULT_MODEL,
            {"prompt": "A test.", "output_path": None},
            {"num_frames": 162},
        )


def test_falai_media_payloads_and_cost_snapshots():
    from easy_ai_clients.video._image_lipsync._apis import falai as image_lipsync
    from easy_ai_clients.video._image_to_video._apis import falai as image_to_video
    from easy_ai_clients.video._motion_control._apis import falai as motion_control
    from easy_ai_clients.video._video_lipsync._apis import falai as video_lipsync

    image_payload = image_to_video._build_payload(  # noqa: SLF001
        image_to_video.DEFAULT_MODEL,
        {
            "prompt": "Animate this.",
            "image": "https://example.com/image.png",
            "output_path": None,
        },
        {
            "duration": 10,
            "aspect_ratio": "9:16",
            "static_mask_url": "https://example.com/static-mask.png",
            "dynamic_masks": [{"mask_url": "https://example.com/dynamic-mask.png"}],
        },
    )
    motion_payload = motion_control._build_payload(  # noqa: SLF001
        motion_control.DEFAULT_MODEL,
        {
            "prompt": None,
            "image": "https://example.com/character.png",
            "video": "https://example.com/motion.mp4",
            "reference": None,
            "output_path": None,
        },
        {"character_orientation": "image"},
    )
    lipsync_payload = image_lipsync._build_payload(  # noqa: SLF001
        image_lipsync.DEFAULT_MODEL,
        {
            "image": "https://example.com/avatar.png",
            "audio": "https://example.com/voice.wav",
            "output_path": None,
        },
        {"resolution": "720p", "num_segments": 2},
    )
    video_lipsync_payload = video_lipsync._build_payload(  # noqa: SLF001
        video_lipsync.DEFAULT_MODEL,
        {
            "video": "https://example.com/source.mp4",
            "audio": "https://example.com/voice.wav",
            "output_path": None,
        },
        {"num_frames": 145, "resolution": "480p"},
    )

    assert image_payload["duration"] == "10"
    assert image_payload["static_mask_url"] == "https://example.com/static-mask.png"
    assert image_payload["dynamic_masks"] == [
        {"mask_url": "https://example.com/dynamic-mask.png"}
    ]
    assert image_to_video._cost(image_to_video.DEFAULT_MODEL, {"duration": 10})[  # noqa: SLF001
        "cost_usd"
    ] == pytest.approx(0.98)
    assert motion_payload["image_url"] == "https://example.com/character.png"
    assert motion_payload["video_url"] == "https://example.com/motion.mp4"
    assert motion_control._cost(  # noqa: SLF001
        motion_control.DEFAULT_MODEL,
        {"duration_seconds": 5},
    )["cost_usd"] == pytest.approx(0.35)
    assert lipsync_payload["resolution"] == "720p"
    assert image_lipsync._cost(  # noqa: SLF001
        image_lipsync.DEFAULT_MODEL,
        {"resolution": "720p", "num_segments": 2},
    )["cost_usd"] == pytest.approx(6.48)
    assert video_lipsync_payload["num_frames"] == 145
    assert video_lipsync._cost(  # noqa: SLF001
        video_lipsync.DEFAULT_MODEL,
        {"num_frames": 145},
    )["cost_usd"] == pytest.approx(1.74)


def test_video_credentials_are_checked_before_network(monkeypatch):
    from easy_ai_clients.video._text_to_video._apis import google as provider

    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="GOOGLE_API_KEY"):
        provider.generate_text_to_video(
            "A short product shot.",
            duration_seconds=4,
            resolution="720p",
            sync=False,
        )


def test_video_result_extractors_accept_provider_shapes():
    from easy_ai_clients.video._shared import extract_video_url, google_extract_video_url
    from easy_ai_clients.video._text_to_video._apis import runway

    assert extract_video_url({"video": {"url": "https://example.com/fal.mp4"}}) == (
        "https://example.com/fal.mp4"
    )
    assert extract_video_url({"output": [{"url": "https://example.com/output.mp4"}]}) == (
        "https://example.com/output.mp4"
    )
    assert google_extract_video_url(
        {
            "response": {
                "generateVideoResponse": {
                    "generatedSamples": [
                        {"video": {"uri": "https://example.com/google.mp4"}}
                    ]
                }
            }
        }
    ) == "https://example.com/google.mp4"
    assert runway._video_url({"output": [{"url": "https://example.com/runway.mp4"}]}) == (  # noqa: SLF001
        "https://example.com/runway.mp4"
    )
