"""ElevenLabs TTS client implementation."""

import logging
from pathlib import Path
from typing import Optional

from gossiptoon.audio.base import TTSClient
from gossiptoon.core.constants import EMOTION_VOICE_SETTINGS, EmotionTone
from gossiptoon.core.exceptions import ElevenLabsAPIError
from gossiptoon.utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)


class ElevenLabsClient(TTSClient):
    """ElevenLabs Text-to-Speech client."""

    def __init__(self, api_key: str) -> None:
        """Initialize ElevenLabs client.

        Args:
            api_key: ElevenLabs API key
        """
        self.api_key = api_key
        self._client: Optional[any] = None

    def _init_client(self) -> any:
        """Initialize ElevenLabs SDK client (lazy loading).

        Returns:
            ElevenLabs client instance

        Raises:
            ElevenLabsAPIError: If initialization fails
        """
        if self._client is not None:
            return self._client

        try:
            from elevenlabs.client import ElevenLabs

            self._client = ElevenLabs(api_key=self.api_key)
            logger.info("ElevenLabs client initialized")
            return self._client
        except ImportError:
            raise ElevenLabsAPIError(
                "ElevenLabs package not installed. Install with: pip install elevenlabs"
            )
        except Exception as e:
            raise ElevenLabsAPIError(f"Failed to initialize ElevenLabs client: {e}") from e

    @retry_with_backoff(max_retries=3, exceptions=(ElevenLabsAPIError,))
    async def generate_speech(
        self,
        text: str,
        voice_id: str,
        emotion: Optional[EmotionTone] = None,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate speech from text using ElevenLabs.

        Args:
            text: Text to convert to speech
            voice_id: ElevenLabs voice ID
            emotion: Optional emotion tone for voice settings
            output_path: Optional path to save audio file

        Returns:
            Path to generated audio file

        Raises:
            ElevenLabsAPIError: If generation fails
        """
        try:
            client = self._init_client()

            # Get voice settings for emotion
            voice_settings = self._get_voice_settings(emotion)

            # Generate audio using ElevenLabs SDK v2
            logger.info(f"Generating speech: {len(text)} chars, voice={voice_id}, emotion={emotion}")

            # New SDK v2 uses text_to_speech.convert()
            from elevenlabs import VoiceSettings
            
            audio_generator = client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id="eleven_multilingual_v2",
                voice_settings=VoiceSettings(
                    stability=voice_settings.get("stability", 0.5),
                    similarity_boost=voice_settings.get("similarity_boost", 0.75),
                    style=voice_settings.get("style", 0.5),
                ),
            )

            # Save to file
            if output_path is None:
                output_path = Path(f"audio_{hash(text)}.mp3")

            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write audio bytes from generator
            with open(output_path, "wb") as f:
                for chunk in audio_generator:
                    f.write(chunk)

            logger.info(f"Audio saved to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"ElevenLabs speech generation failed: {e}")
            raise ElevenLabsAPIError(f"Speech generation failed: {e}") from e

    def _get_voice_settings(self, emotion: Optional[EmotionTone]) -> dict[str, float]:
        """Get voice settings for emotion tone.

        Args:
            emotion: Emotion tone

        Returns:
            Voice settings dict
        """
        if emotion and emotion in EMOTION_VOICE_SETTINGS:
            settings = EMOTION_VOICE_SETTINGS[emotion]
            logger.debug(f"Using emotion settings for {emotion}: {settings}")
            return settings

        # Default neutral settings
        return {"stability": 0.5, "similarity_boost": 0.75, "style": 0.5}

    def get_available_voices(self) -> list[dict[str, str]]:
        """Get list of available ElevenLabs voices.

        Returns:
            List of voice metadata
        """
        try:
            client = self._init_client()
            voices = client.voices.get_all()

            return [
                {
                    "id": voice.voice_id,
                    "name": voice.name,
                    "category": voice.category,
                    "description": voice.description or "",
                }
                for voice in voices.voices
            ]
        except Exception as e:
            logger.error(f"Failed to get voices: {e}")
            return []

    def estimate_duration(self, text: str, voice_id: str) -> float:
        """Estimate audio duration for text.

        Args:
            text: Input text
            voice_id: Voice identifier

        Returns:
            Estimated duration in seconds
        """
        # Rough estimate: ~150 words per minute = 2.5 words per second
        word_count = len(text.split())
        duration = word_count / 2.5

        # Add small buffer for pauses
        return duration * 1.1
