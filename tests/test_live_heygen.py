"""Gated live HeyGen v3 smoke tests.

These tests call HeyGen only when EASY_AI_CLIENTS_LIVE_HEYGEN=1 is set by the
caller. The default path covers low-cost/free catalog, account, speech, and
asset flows. Video-generation smoke tests remain behind an extra paid-video
gate because even short jobs can consume meaningful account credit.
"""

from __future__ import annotations

import base64
import os
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pytest
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
LIVE_ENV = "EASY_AI_CLIENTS_LIVE_HEYGEN"
MAX_COST_ENV = "EASY_AI_CLIENTS_LIVE_HEYGEN_MAX_USD"
PAID_VIDEO_ENV = "EASY_AI_CLIENTS_LIVE_HEYGEN_PAID_VIDEO"
DEFAULT_MAX_USD = Decimal("8.50")
ESTIMATED_COSTS = {
    "speech": Decimal("0.05"),
    "asset": Decimal("0.00"),
    "video_agent": Decimal("1.50"),
}

ONE_PIXEL_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMC"
    "AO+/p9sAAAAASUVORK5CYII="
)


def _require_live_enabled():
    if os.getenv(LIVE_ENV) != "1":
        pytest.skip(f"Set {LIVE_ENV}=1 to run live HeyGen smoke tests.")


def _load_credentials():
    load_dotenv(ROOT / ".env", override=False)
    if not (os.getenv("HEYGEN_KEY") or os.getenv("HEYGEN_API_KEY")):
        pytest.skip("HEYGEN_KEY is not configured for live HeyGen smoke tests.")


def _max_cost() -> Decimal:
    value = os.getenv(MAX_COST_ENV)
    if not value:
        return DEFAULT_MAX_USD
    try:
        return Decimal(value)
    except InvalidOperation:
        pytest.skip(f"{MAX_COST_ENV} must be a decimal USD value.")


def _guard_budget(*names: str):
    total = sum((ESTIMATED_COSTS[name] for name in names), Decimal("0"))
    max_cost = _max_cost()
    if total > max_cost:
        pytest.skip(
            f"Estimated HeyGen smoke cost US$ {total:.2f} exceeds "
            f"{MAX_COST_ENV}=US$ {max_cost:.2f}."
        )


def _require_live_heygen_account():
    from easy_ai_clients import account

    _require_live_enabled()
    _load_credentials()
    result = account.get_current_user(api="heygen", timeout_seconds=30)
    if result.get("data") is None:
        pytest.fail(f"HeyGen account lookup failed: {result.get('warnings') or result.get('error')}")
    return result


def _first_voice_id(result):
    data = result.get("data")
    candidates = data if isinstance(data, list) else []
    if isinstance(data, dict):
        for key in ("voices", "items", "data", "results"):
            if isinstance(data.get(key), list):
                candidates = data[key]
                break
    for item in candidates:
        if isinstance(item, dict) and item.get("voice_id"):
            return str(item["voice_id"])
    return None


def _asset_id(result):
    data = result.get("data")
    if isinstance(data, dict):
        for key in ("asset_id", "id"):
            if data.get(key):
                return str(data[key])
    return None


def _skip_if_feature_blocked(result, feature: str):
    if result.get("status") == "failed" or result.get("data") is None and result.get("warnings"):
        warning = str(result.get("warnings") or result.get("error") or "")
        lowered = warning.lower()
        if "403" in lowered or "feature" in lowered or "unavailable" in lowered:
            pytest.skip(f"HeyGen {feature} is unavailable for this account: {warning}")


def test_live_heygen_free_catalog_smoke():
    from easy_ai_clients import audio, video, webhooks

    _require_live_heygen_account()

    voices = audio.list_voices(api="heygen", engine="starfish", limit=1, timeout_seconds=30)
    assert voices["provider"] == "heygen"
    assert voices["raw_response"]

    styles = video.list_agent_styles(api="heygen", timeout_seconds=30)
    _skip_if_feature_blocked(styles, "Video Agent styles")
    assert styles["provider"] == "heygen"
    assert styles["raw_response"]

    languages = video.list_translation_languages(api="heygen", timeout_seconds=30)
    _skip_if_feature_blocked(languages, "translation languages")
    assert languages["provider"] == "heygen"
    assert languages["raw_response"]

    event_types = webhooks.list_event_types(api="heygen", timeout_seconds=30)
    _skip_if_feature_blocked(event_types, "webhook event types")
    assert event_types["provider"] == "heygen"
    assert event_types["raw_response"]


def test_live_heygen_speech_and_asset_smoke(tmp_path):
    from easy_ai_clients import audio, media

    _require_live_heygen_account()
    _guard_budget("speech", "asset")

    voices = audio.list_voices(api="heygen", engine="starfish", limit=1, timeout_seconds=30)
    voice_id = _first_voice_id(voices)
    if not voice_id:
        pytest.skip("HeyGen returned no Starfish-compatible voice for live speech smoke.")

    speech = audio.generate("Hello.", api="heygen", voice=voice_id, timeout_seconds=60)
    assert speech["request_id"] or speech["raw_response"]
    assert speech["provider_metadata"]["provider"] == "heygen"
    assert speech["audio"].duration_seconds > 0

    asset_path = tmp_path / "easy-ai-clients-heygen-live.png"
    asset_path.write_bytes(base64.b64decode(ONE_PIXEL_PNG))
    uploaded = media.upload_asset(asset_path, api="heygen", timeout_seconds=60)
    assert uploaded["provider"] == "heygen"
    asset_id = _asset_id(uploaded)
    if asset_id:
        deleted = media.delete_asset(asset_id, api="heygen", confirm=True, timeout_seconds=60)
        assert deleted["provider"] == "heygen"
        assert "error" not in deleted


def test_live_heygen_paid_video_agent_smoke():
    from easy_ai_clients import video

    _require_live_heygen_account()
    if os.getenv(PAID_VIDEO_ENV) != "1":
        pytest.skip(f"Set {PAID_VIDEO_ENV}=1 to submit a paid HeyGen Video Agent job.")
    _guard_budget("video_agent")

    result = video.agent_video(
        "Create a very short landscape title-card video that says: HeyGen smoke test.",
        api="heygen",
        sync=False,
        mode="generate",
        orientation="landscape",
        estimated_cost_usd=float(ESTIMATED_COSTS["video_agent"]),
        timeout_seconds=60,
    )

    assert result["provider"] == "heygen"
    assert result["request_id"]
    assert result["status"] in {"queued", "processing", "completed"}
