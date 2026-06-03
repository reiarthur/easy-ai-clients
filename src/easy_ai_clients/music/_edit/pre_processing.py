from .._common import media_utils, provider_utils


def prepare_edit(audio, prompt=None):
    """Prepare common music edit inputs.

    Args:
        audio: Required. Source audio reference.
        prompt: Optional. Edit instruction.

    Returns:
        A small prepared input dictionary.
    """
    prepared = {
        "audio": audio,
        "media_metadata": media_utils.describe_media(audio),
    }
    return provider_utils.add_optional(prepared, prompt=prompt)
