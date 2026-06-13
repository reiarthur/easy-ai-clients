"""Music lyrics prompt builder tests."""

from __future__ import annotations

import inspect

import pytest


def test_public_signature_and_main_surface():
    from easy_ai_clients import music

    signature = inspect.signature(music.build_lyrics_prompt)

    assert str(signature) == "(duration_seconds, reference_text=None, lyrics_text=None)"
    assert not hasattr(music, "PROVIDERS")
    assert not hasattr(music, "_run_cli")


def test_reference_text_only_builds_original_lyrics_request():
    from easy_ai_clients import music

    result = music.build_lyrics_prompt(
        45,
        reference_text="Brazilian Portuguese gospel pop, hopeful mood, strong chorus.",
    )

    assert set(result) == {"system_prompt", "prompt"}
    assert "duration_seconds: 45" in result["prompt"]
    assert "Brazilian Portuguese gospel pop" in result["prompt"]
    assert "Generate an original lyric based on reference_text" in result["prompt"]
    assert "Return only the final lyric string" in result["system_prompt"]


def test_lyrics_text_only_builds_adaptation_request():
    from easy_ai_clients.music._lyrics_prompt import build_lyrics_prompt

    lyrics = "  [Verse]\neu caminho pela fe\n[Chorus]\na luz me guia  "

    result = build_lyrics_prompt(60, lyrics_text=lyrics)

    assert set(result) == {"system_prompt", "prompt"}
    assert "duration_seconds: 60" in result["prompt"]
    assert "[Verse]\neu caminho pela fe" in result["prompt"]
    assert "Preserve the original language" in result["prompt"]
    assert "Correct typos and awkward phrasing" in result["prompt"]
    assert "  [Verse]" not in result["prompt"]


def test_reference_text_and_lyrics_text_build_combined_request():
    from easy_ai_clients.music._lyrics_prompt import build_lyrics_prompt

    result = build_lyrics_prompt(
        120,
        reference_text="Add 1980s synth pop tone and a bigger final chorus.",
        lyrics_text="[Verse]\nThe city lights are fading\n[Chorus]\nWe keep running",
    )

    assert set(result) == {"system_prompt", "prompt"}
    assert "duration_seconds: 120" in result["prompt"]
    assert "Add 1980s synth pop tone" in result["prompt"]
    assert "The city lights are fading" in result["prompt"]
    assert "Use lyrics_text as the primary lyrical source" in result["prompt"]
    assert "unless reference_text explicitly requests a language change" in result["prompt"]


def test_missing_optional_inputs_are_rejected():
    from easy_ai_clients.music._lyrics_prompt import build_lyrics_prompt

    with pytest.raises(ValueError, match="reference_text or lyrics_text is required"):
        build_lyrics_prompt(30)


def test_empty_optional_inputs_count_as_absent():
    from easy_ai_clients.music._lyrics_prompt import build_lyrics_prompt

    with pytest.raises(ValueError, match="reference_text or lyrics_text is required"):
        build_lyrics_prompt(30, reference_text="   ", lyrics_text="\n\t")


def test_invalid_duration_is_rejected():
    from easy_ai_clients.music._lyrics_prompt import build_lyrics_prompt

    invalid_values = [0, -1, None, "60", True]

    for duration_seconds in invalid_values:
        with pytest.raises(ValueError, match="duration_seconds must be a positive number"):
            build_lyrics_prompt(
                duration_seconds,
                reference_text="Write a short chorus.",
            )


def test_optional_text_must_be_string_when_present():
    from easy_ai_clients.music._lyrics_prompt import build_lyrics_prompt

    with pytest.raises(ValueError, match="reference_text must be a string"):
        build_lyrics_prompt(30, reference_text=["gospel"])

    with pytest.raises(ValueError, match="lyrics_text must be a string"):
        build_lyrics_prompt(30, lyrics_text={"lyrics": "text"})


def test_destination_output_restrictions_are_present():
    from easy_ai_clients.music._lyrics_prompt import build_lyrics_prompt

    result = build_lyrics_prompt(75, reference_text="Rock song about starting again.")
    combined_prompt = f"{result['system_prompt']}\n{result['prompt']}"

    assert "Return only the final lyric string" in combined_prompt
    assert "Do not return JSON" in combined_prompt
    assert "Markdown fences" in combined_prompt
    assert "comments, analysis, explanations, metadata" in combined_prompt
    assert "Do not include a title unless" in combined_prompt
    assert "provider settings" in combined_prompt


def test_lyrics_contract_guidance_is_present():
    from easy_ai_clients.music._lyrics_prompt import build_lyrics_prompt

    result = build_lyrics_prompt(90, reference_text="Soul ballad in English.")

    assert "[Verse]" in result["prompt"]
    assert "[Pre Chorus]" in result["prompt"]
    assert "[Final Chorus]" in result["prompt"]
    assert "Treat tags as part of the lyric text" in result["prompt"]
    assert "at least 10 non-whitespace characters" in result["prompt"]

