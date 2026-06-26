"""Music lyrics prompt builder tests."""

from __future__ import annotations

import inspect

import pytest


def test_public_signature_and_main_surface():
    from easy_ai_clients import music

    signature = inspect.signature(music.build_lyrics_prompt)

    assert str(signature) == (
        "(prompt, lyrics_text=None, duration=None, style=None, "
        "gender=None, voice_description=None, api=None)"
    )
    assert not hasattr(music, "PROVIDERS")
    assert not hasattr(music, "_run_cli")


def test_prompt_only_builds_original_lyrics_request():
    from easy_ai_clients import music

    result = music.build_lyrics_prompt(
        "Brazilian Portuguese gospel pop, hopeful mood, strong chorus.",
        duration=45,
    )

    assert set(result) == {"system_prompt", "prompt"}
    assert "Target lyric duration: about 45 seconds" in result["prompt"]
    assert "Brazilian Portuguese gospel pop" in result["prompt"]
    assert "Generate an original lyric based on the user intent" in result["prompt"]
    assert "Return only the final lyric string" in result["system_prompt"]
    assert "duration_seconds" not in result["prompt"]


def test_lyrics_text_builds_adaptation_request():
    from easy_ai_clients.music._lyrics_prompt import build_lyrics_prompt

    lyrics = "  [Verse]\neu caminho pela fe\n[Chorus]\na luz me guia  "

    result = build_lyrics_prompt(
        "Improve this lyric while preserving Brazilian Portuguese.",
        lyrics_text=lyrics,
        duration=60,
    )

    assert set(result) == {"system_prompt", "prompt"}
    assert "Target lyric duration: about 1 minute" in result["prompt"]
    assert "[Verse]\neu caminho pela fe" in result["prompt"]
    assert "Use existing lyrics as the primary lyrical source" in result["prompt"]
    assert "Correct typos and awkward phrasing" in result["prompt"]
    assert "  [Verse]" not in result["prompt"]


def test_duration_formats_are_natural_or_omitted():
    from easy_ai_clients.music._lyrics_prompt import build_lyrics_prompt

    cases = [
        (15, "about 15 seconds"),
        (60, "about 1 minute"),
        (75, "about 1 minute and 15 seconds"),
        ("135.9", "about 2 minutes and 15 seconds"),
    ]

    for duration, phrase in cases:
        result = build_lyrics_prompt("Write a chorus in English.", duration=duration)
        assert phrase in result["prompt"]

    for duration in (None, "", "abc", True):
        result = build_lyrics_prompt("Write a chorus in English.", duration=duration)
        assert "Target lyric duration" not in result["prompt"]


def test_missing_or_invalid_prompt_is_rejected():
    from easy_ai_clients.music._lyrics_prompt import build_lyrics_prompt

    for value in (None, "", "   ", ["gospel"]):
        with pytest.raises(ValueError, match="prompt must be a non-empty string"):
            build_lyrics_prompt(value)


def test_optional_lyrics_text_must_be_string_when_present():
    from easy_ai_clients.music._lyrics_prompt import build_lyrics_prompt

    with pytest.raises(ValueError, match="lyrics_text must be a string"):
        build_lyrics_prompt("Write a song.", lyrics_text={"lyrics": "text"})


def test_style_voice_and_language_guidance_are_present():
    from easy_ai_clients.music._lyrics_prompt import build_lyrics_prompt

    result = build_lyrics_prompt(
        "Write in English about starting again.",
        style="sertanejo",
        gender="female",
    )

    prompt = result["prompt"]
    assert "Target language: English" in prompt
    assert "Brazilian sertanejo with acoustic guitar" in prompt
    assert "Use the `sertanejo` style as creative guidance" not in prompt
    assert "Two female lead voices" in prompt
    assert "voice_presets" not in prompt


def test_explicit_prompt_language_wins_over_lyrics_language():
    from easy_ai_clients.music._lyrics_prompt import build_lyrics_prompt

    result = build_lyrics_prompt(
        "Write in English while preserving the story.",
        lyrics_text="[Verso]\no coração volta pra casa",
    )

    assert "Target language: English" in result["prompt"]


def test_voice_description_overrides_preset_gender_voice():
    from easy_ai_clients.music._lyrics_prompt import build_lyrics_prompt

    result = build_lyrics_prompt(
        "Write a short lyric in Brazilian Portuguese.",
        style="sertanejo",
        gender="male",
        voice_description="Soft intimate baritone with close diction.",
    )

    prompt = result["prompt"]
    assert "Soft intimate baritone" in prompt
    assert "Two male lead voices" not in prompt


def test_gender_without_style_uses_generic_voice_guidance():
    from easy_ai_clients.music._lyrics_prompt import build_lyrics_prompt

    result = build_lyrics_prompt(
        "Write a hopeful lyric in English.",
        gender="male",
    )

    assert "Male lead vocal with clear diction" in result["prompt"]


def test_invalid_style_and_gender_are_rejected():
    from easy_ai_clients.music._lyrics_prompt import build_lyrics_prompt

    with pytest.raises(ValueError, match="Unknown style"):
        build_lyrics_prompt("Write a song.", style="Hip Hop Rap Trap")

    with pytest.raises(ValueError, match="gender must be one of"):
        build_lyrics_prompt("Write a song.", gender="duet")


def test_multi_voice_prompt_uses_section_tags_not_line_labels():
    from easy_ai_clients.music._lyrics_prompt import build_lyrics_prompt

    result = build_lyrics_prompt(
        "Write in English about two people reconciling.",
        gender="both",
    )
    combined_prompt = f"{result['system_prompt']}\n{result['prompt']}"

    assert "[Verse 1 - Male Lead]" in combined_prompt
    assert "[Verse 2 - Female Lead]" in combined_prompt
    assert "[Chorus - Duet]" in combined_prompt
    assert "Do not use line labels such as Male: or Female:" in combined_prompt


def test_elevenlabs_prompt_uses_music_safe_multi_voice_guidance():
    from easy_ai_clients.music._lyrics_prompt import build_lyrics_prompt

    result = build_lyrics_prompt(
        "Write an upbeat song in Brazilian Portuguese.",
        style="sertanejo",
        gender="both",
        duration=60,
        api="elevenlabs",
    )
    combined_prompt = f"{result['system_prompt']}\n{result['prompt']}"

    assert "ElevenLabs" not in combined_prompt
    assert "elevenlabs" not in combined_prompt.lower()
    assert "Brazilian sertanejo with acoustic guitar" in combined_prompt
    assert "Natural male sertanejo lead" in combined_prompt
    assert "Natural female sertanejo lead" in combined_prompt
    assert "[Verse 1 - Male Lead]" not in combined_prompt
    assert "[Verse 2 - Female Lead]" not in combined_prompt
    assert "[Chorus - Duet]" not in combined_prompt
    assert "Male:" not in combined_prompt
    assert "Female:" not in combined_prompt
    assert "Do not use vocal-role section tags" in combined_prompt
    assert "Write the lyric so two voices can share it naturally." in combined_prompt
    assert "Leave enough lyrical space" in combined_prompt


def test_non_elevenlabs_api_preserves_default_multi_voice_guidance():
    from easy_ai_clients.music._lyrics_prompt import build_lyrics_prompt

    result = build_lyrics_prompt(
        "Write in English about two people reconciling.",
        gender="both",
        api="google",
    )
    combined_prompt = f"{result['system_prompt']}\n{result['prompt']}"

    assert "[Verse 1 - Male Lead]" in combined_prompt
    assert "[Verse 2 - Female Lead]" in combined_prompt
    assert "[Chorus - Duet]" in combined_prompt


def test_destination_output_restrictions_are_present():
    from easy_ai_clients.music._lyrics_prompt import build_lyrics_prompt

    result = build_lyrics_prompt("Rock song about starting again.")
    combined_prompt = f"{result['system_prompt']}\n{result['prompt']}"

    assert "Return only the final lyric string" in combined_prompt
    assert "Do not return JSON" in combined_prompt
    assert "Markdown fences" in combined_prompt
    assert "comments, analysis, explanations, metadata" in combined_prompt
    assert "Do not include a title unless" in combined_prompt
    assert "provider settings" in combined_prompt


def test_lyrics_contract_guidance_is_present():
    from easy_ai_clients.music._lyrics_prompt import build_lyrics_prompt

    result = build_lyrics_prompt("Soul ballad in English.")

    assert "[Verse]" in result["prompt"]
    assert "[Pre Chorus]" in result["prompt"]
    assert "[Final Chorus]" in result["prompt"]
    assert "Treat tags as part of the lyric text" in result["prompt"]
    assert "at least 10 non-whitespace characters" in result["prompt"]
