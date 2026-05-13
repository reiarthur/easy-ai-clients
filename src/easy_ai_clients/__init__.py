"""easy-ai-clients: a unified Python client for multimodal multi-provider AI.

Importing :mod:`easy_ai_clients` exposes four ergonomic submodules:

- :mod:`easy_ai_clients.text` - text-in / text-out generation.
- :mod:`easy_ai_clients.audio` - speech synthesis (`generate`) and speech
  recognition (`transcribe`).
- :mod:`easy_ai_clients.image` - image generation, editing, remixing, and
  vision/multimodal analysis.
- :mod:`easy_ai_clients.video` - text-to-video, image-to-video, motion control,
  and lip-sync generation.

Each operation accepts an ``api`` keyword argument identifying the provider to
use. The string must match the file name (without ``.py``) of the internal
provider module shipped with the library.

Example::

    from easy_ai_clients import text, audio, image, video

    text.generate("hello", api="openai")
    audio.generate("hello world", api="openai")
    audio.transcribe("audio.mp3", api="deepgram")
    image.analyze("describe this", "photo.png", api="openai")
    image.edit("make it night", "photo.png", api="openai")
    image.generate("a corgi", api="openai")
    image.remix("studio ghibli", ["ref1.png", "ref2.png"], api="openai")
    video.generate("a corgi surfing", api="google")
"""

from __future__ import annotations

from . import audio, image, text, video

__all__ = ["text", "audio", "image", "video", "__version__"]

__version__ = "0.6.0"
