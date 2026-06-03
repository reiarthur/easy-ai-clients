from .._common import media_utils, provider_utils


def prepare_voice_conversion(audio, voice=None, prompt=None):
    """Prepare common voice conversion inputs.

    Args:
        audio: Required. Source audio reference.
        voice: Optional. Voice identifier or voice reference.
        prompt: Optional. Conversion instruction.

    Returns:
        A small prepared input dictionary.
    """
    prepared = {
        "audio": audio,
        "media_metadata": media_utils.describe_media(audio),
    }
    return provider_utils.add_optional(prepared, voice=voice, prompt=prompt)
