from .._common import media_utils, provider_utils


def prepare_media_to_music(media, prompt=None):
    """Prepare common media-to-music inputs.

    Args:
        media: Required. Media reference.
        prompt: Optional. Style or generation prompt.

    Returns:
        A small prepared input dictionary.
    """
    prepared = {
        "media": media,
        "media_metadata": media_utils.describe_media(media),
    }
    return provider_utils.add_optional(prepared, prompt=prompt)
