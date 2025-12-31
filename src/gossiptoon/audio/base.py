"""Base interfaces for audio generation (modular TTS providers)."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from gossiptoon.core.constants import EmotionTone


class TTSClient(ABC):
    """Abstract base class for Text-to-Speech clients.

    This allows easy swapping between ElevenLabs, Google TTS, Azure TTS, etc.
    """

    @abstractmethod
    async def generate_speech(
        self,
        text: str,
        voice_id: str,
        emotion: Optional[EmotionTone] = None,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate speech from text.

        Args:
            text: Text to convert to speech
            voice_id: Voice identifier (provider-specific)
            emotion: Optional emotion tone for expressive TTS
            output_path: Optional path to save audio file

        Returns:
            Path to generated audio file

        Raises:
            AudioGenerationError: If generation fails
        """
        pass

    @abstractmethod
    def get_available_voices(self) -> list[dict[str, str]]:
        """Get list of available voices.

        Returns:
            List of voice metadata (id, name, language, etc.)
        """
        pass

    @abstractmethod
    def estimate_duration(self, text: str, voice_id: str) -> float:
        """Estimate audio duration for text.

        Args:
            text: Input text
            voice_id: Voice identifier

        Returns:
            Estimated duration in seconds
        """
        pass
