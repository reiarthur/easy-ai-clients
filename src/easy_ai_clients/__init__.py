"""Exports públicos do pacote easy-ai-clients.

Última atualização: 2026-04-19
"""

from ._core.config import VERSION
from .client import EasyAiClient
from .exceptions import (
    ConfigurationError,
    EasyAiClientError,
    IncompatibleParameterError,
    InvalidParameterError,
    InvalidProviderResponseError,
    JobFailedError,
    MissingCredentialError,
    PricingUnavailableError,
    ProviderTimeoutError,
    TemporaryDownloadError,
    UnsupportedModelError,
    UnsupportedProviderError,
)
from .models import (
    ImageCompositionRequest,
    ImageEditRequest,
    ImageGenerationRequest,
    ImageResult,
    ImageTransformationRequest,
    LipSyncRequest,
    MusicGenerationRequest,
    MusicGenerationResult,
    SpeakerSegment,
    SpeechSynthesisRequest,
    SpeechSynthesisResult,
    SpeechTranscriptionRequest,
    SpeechTranscriptionResult,
    TextGenerationRequest,
    TextGenerationResult,
    VideoGenerationRequest,
    VideoResult,
    WordTiming,
)

__all__ = [
    "ConfigurationError",
    "EasyAiClient",
    "EasyAiClientError",
    "ImageCompositionRequest",
    "ImageEditRequest",
    "ImageGenerationRequest",
    "ImageResult",
    "ImageTransformationRequest",
    "IncompatibleParameterError",
    "InvalidParameterError",
    "InvalidProviderResponseError",
    "JobFailedError",
    "LipSyncRequest",
    "MissingCredentialError",
    "MusicGenerationRequest",
    "MusicGenerationResult",
    "PricingUnavailableError",
    "ProviderTimeoutError",
    "SpeakerSegment",
    "SpeechSynthesisRequest",
    "SpeechSynthesisResult",
    "SpeechTranscriptionRequest",
    "SpeechTranscriptionResult",
    "TemporaryDownloadError",
    "TextGenerationRequest",
    "TextGenerationResult",
    "UnsupportedModelError",
    "UnsupportedProviderError",
    "VideoGenerationRequest",
    "VideoResult",
    "WordTiming",
]

__version__ = VERSION
