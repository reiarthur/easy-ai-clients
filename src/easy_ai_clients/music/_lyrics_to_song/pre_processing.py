from .._common import media_utils, provider_utils


def prepare_lyrics_to_song(lyrics, prompt=None):
    """Prepare common lyrics-to-song inputs.

    Args:
        lyrics: Required. Lyrics or song structure.
        prompt: Optional. Style or generation prompt.

    Returns:
        A small prepared input dictionary.
    """
    prepared = {"lyrics": media_utils.clean_required_text(lyrics, "lyrics")}
    return provider_utils.add_optional(prepared, prompt=prompt)
