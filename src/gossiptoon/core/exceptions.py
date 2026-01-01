"""Custom exceptions for the GossipToon engine."""


class GossipToonException(Exception):
    """Base exception for all GossipToon errors."""

    pass


class ConfigurationError(GossipToonException):
    """Raised when configuration is invalid or missing."""

    pass


class APIError(GossipToonException):
    """Base class for API-related errors."""

    pass


class OpenAIAPIError(APIError):
    """Raised when OpenAI API calls fail."""

    pass


class GeminiAPIError(APIError):
    """Raised when Gemini API calls fail."""

    pass


class ElevenLabsAPIError(APIError):
    """Raised when ElevenLabs API calls fail."""

    pass


class GoogleTTSError(APIError):
    """Raised when Google TTS API calls fail."""

    pass


class RedditAPIError(APIError):
    """Raised when Reddit API calls fail."""

    pass


class ValidationError(GossipToonException):
    """Raised when data validation fails."""

    pass


class ScriptGenerationError(GossipToonException):
    """Raised when script generation fails."""

    pass


class AudioGenerationError(GossipToonException):
    """Raised when audio generation fails."""

    pass


class ImageGenerationError(GossipToonException):
    """Raised when image generation fails."""

    pass


class VideoRenderingError(GossipToonException):
    """Raised when video rendering fails."""

    pass


class VideoAssemblyError(VideoRenderingError):
    """Raised when video assembly fails."""

    pass


class FFmpegError(VideoRenderingError):
    """Raised when FFmpeg operations fail."""

    pass


class WhisperError(AudioGenerationError):
    """Raised when Whisper timestamp extraction fails."""

    pass


class CheckpointError(GossipToonException):
    """Raised when checkpoint operations fail."""

    pass


class RetryExhaustedError(GossipToonException):
    """Raised when retry attempts are exhausted."""

    def __init__(self, operation: str, attempts: int) -> None:
        """Initialize retry exhausted error.

        Args:
            operation: The operation that failed
            attempts: Number of attempts made
        """
        super().__init__(f"{operation} failed after {attempts} attempts")
        self.operation = operation
        self.attempts = attempts
