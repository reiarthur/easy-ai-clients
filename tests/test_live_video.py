"""Gated live video smoke tests.

These tests call paid provider APIs only when EASY_AI_CLIENTS_LIVE_VIDEO=1 is
set by the caller. They intentionally avoid downloads and validate only the
normalized result contract.
"""

from __future__ import annotations

import os

import pytest

MAX_LIVE_VIDEO_COST_USD = 1.00
ESTIMATED_LIVE_VIDEO_COST_USD = {
    "google": 0.20,
    "falai": 0.08,
    "runway": 0.24,
}


def _require_live_video_enabled():
    if os.getenv("EASY_AI_CLIENTS_LIVE_VIDEO") != "1":
        pytest.skip("Set EASY_AI_CLIENTS_LIVE_VIDEO=1 to run paid video smoke tests.")


def _guard_budget():
    total = sum(ESTIMATED_LIVE_VIDEO_COST_USD.values())
    if total > MAX_LIVE_VIDEO_COST_USD:
        pytest.skip(
            "Estimated live video smoke cost exceeds "
            f"US$ {MAX_LIVE_VIDEO_COST_USD:.2f}: US$ {total:.2f}."
        )


def _require_env(name):
    if not os.getenv(name):
        pytest.skip(f"{name} is not configured for live video smoke tests.")


def _assert_live_video_result(result, provider):
    assert result["provider"] == provider
    assert result["status"] == "completed"
    assert result["request_id"]
    assert result["video_url"]
    assert result["output_path"] is None
    assert result["cost_usd"] is not None
    assert result["cost_is_estimated"] is True
    assert result["cost_source"]
    assert result["raw_response"]


def test_live_google_veo_text_to_video_smoke():
    from easy_ai_clients import video

    _require_live_video_enabled()
    _guard_budget()
    _require_env("GOOGLE_API_KEY")

    result = video.generate(
        "A four second static studio shot of a white coffee mug on a wooden table.",
        api="google",
        model="veo-3.1-lite-generate-preview",
        duration_seconds=4,
        resolution="720p",
        sync=True,
        timeout_seconds=900,
        poll_interval_seconds=10,
    )

    _assert_live_video_result(result, "google")
    assert result["cost_usd"] <= ESTIMATED_LIVE_VIDEO_COST_USD["google"] + 0.001


def test_live_falai_text_to_video_smoke():
    from easy_ai_clients import video

    _require_live_video_enabled()
    _guard_budget()
    _require_env("FAL_KEY")

    result = video.generate(
        "A simple short product clip of a notebook opening on a desk.",
        api="falai",
        sync=True,
        timeout_seconds=900,
        poll_interval_seconds=10,
    )

    _assert_live_video_result(result, "falai")
    assert result["cost_usd"] <= ESTIMATED_LIVE_VIDEO_COST_USD["falai"] + 0.001


def test_live_runway_text_to_video_smoke():
    from easy_ai_clients import video

    _require_live_video_enabled()
    _guard_budget()
    _require_env("RUNWAYML_API_SECRET")

    result = video.generate(
        "A calm two second shot of a glass paperweight on a clean desk.",
        api="runway",
        model="gen4.5",
        duration=2,
        ratio="1280:720",
        sync=True,
        timeout_seconds=900,
        poll_interval_seconds=10,
    )

    _assert_live_video_result(result, "runway")
    assert result["cost_usd"] <= ESTIMATED_LIVE_VIDEO_COST_USD["runway"] + 0.001
