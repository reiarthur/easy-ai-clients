from .._common import media_utils


def prepare_stem_separation(audio):
    """Prepare common stem separation inputs.

    Args:
        audio: Required. Source audio reference.

    Returns:
        A small prepared input dictionary.
    """
    return {
        "audio": audio,
        "media_metadata": media_utils.describe_media(audio),
    }
