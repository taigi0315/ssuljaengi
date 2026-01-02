"""Google TTS 2.5 Flash client implementation using Gemini API."""

import logging
import wave
from pathlib import Path
from typing import Optional

from gossiptoon.audio.base import TTSClient
from gossiptoon.core.constants import EmotionTone
from gossiptoon.core.exceptions import AudioGenerationError
from gossiptoon.utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)


# Emotion to Google TTS style directive mapping
# Using the "Director" method for expressive, dramatic narration
EMOTION_STYLE_DIRECTIVES = {
    EmotionTone.EXCITED: "infectious, cheerful vocal smile with rising energy and enthusiasm",
    EmotionTone.SHOCKED: "sudden gasp with wide-eyed surprise, sharp intake of breath, and disbelief",
    EmotionTone.SYMPATHETIC: "warm, gentle tone with soft empathy and understanding",
    EmotionTone.DRAMATIC: "theatrical, sweeping delivery with dramatic pauses and intensity",
    EmotionTone.ANGRY: "sharp, forceful tone with rising volume and controlled fury",
    EmotionTone.HAPPY: "bright, uplifting tone with a natural smile in the voice",
    EmotionTone.SAD: "slow, melancholic delivery with a heavy, sorrowful tone",
    EmotionTone.NEUTRAL: "clear, balanced delivery with professional composure",
    EmotionTone.SUSPENSEFUL: "hushed, tense whisper with building anticipation and mystery",
    EmotionTone.SARCASTIC: "dry, ironic tone with subtle eye-roll energy and wit",
    EmotionTone.FRUSTRATED: "exasperated tone with barely contained irritation",
    EmotionTone.DETERMINED: "firm, resolute delivery with unwavering confidence",
    EmotionTone.RELIEVED: "exhaling tension with a warm, grateful release",
    EmotionTone.EXASPERATED: "fed-up, exhausted patience with a deep sigh",
}


# Google TTS prebuilt voices - Complete list with gender and characteristics
# Source: Google AI Studio voice documentation
GOOGLE_TTS_VOICE_METADATA = {
    # Female Voices
    "Achernar": {
        "gender": "female",
        "style": "soft",
        "description": "Clear, mid-range tone; friendly and engaging",
    },
    "Aoede": {
        "gender": "female",
        "style": "breezy",
        "description": "Clear, conversational, intelligent, and articulate",
    },
    "Autonoe": {
        "gender": "female",
        "style": "bright",
        "description": "Mature and resonant with a calm, measured pace",
    },
    "Callirrhoe": {
        "gender": "female",
        "style": "easy-going",
        "description": "Confident and professional; projects energy",
    },
    "Despina": {
        "gender": "female",
        "style": "smooth",
        "description": "Warm, inviting, and trustworthy",
    },
    "Erinome": {
        "gender": "female",
        "style": "clear",
        "description": "Professional, articulate, and sophisticated",
    },
    "Gacrux": {
        "gender": "female",
        "style": "mature",
        "description": "Smooth, confident, and authoritative",
    },
    "Kore": {"gender": "female", "style": "firm", "description": "Energetic, youthful, and perky"},
    "Laomedeia": {
        "gender": "female",
        "style": "upbeat",
        "description": "Clear and inquisitive with energy",
    },
    "Leda": {
        "gender": "female",
        "style": "youthful",
        "description": "Composed, articulate, and professional",
    },
    "Pulcherrima": {
        "gender": "female",
        "style": "forward",
        "description": "Bright, energetic, and highly upbeat",
    },
    "Sulafat": {
        "gender": "female",
        "style": "warm",
        "description": "Warm, confident, and persuasive",
    },
    "Vindemiatrix": {
        "gender": "female",
        "style": "gentle",
        "description": "Calm, mature, and composed",
    },
    "Zephyr": {
        "gender": "female",
        "style": "bright",
        "description": "Energetic and perky; youthful and positive",
    },
    # Male Voices
    "Achird": {
        "gender": "male",
        "style": "friendly",
        "description": "Youthful and clear with inquisitive quality",
    },
    "Algenib": {
        "gender": "male",
        "style": "gravelly",
        "description": "Warm and confident with friendly authority",
    },
    "Algieba": {"gender": "male", "style": "smooth", "description": "Smooth delivery"},
    "Alnilam": {
        "gender": "male",
        "style": "firm",
        "description": "Energetic with mid-to-low pitch",
    },
    "Charon": {
        "gender": "male",
        "style": "informative",
        "description": "Smooth and conversational; trustworthy",
    },
    "Enceladus": {
        "gender": "male",
        "style": "breathy",
        "description": "Energetic and enthusiastic",
    },
    "Fenrir": {
        "gender": "male",
        "style": "excitable",
        "description": "Friendly and conversational",
    },
    "Iapetus": {
        "gender": "male",
        "style": "clear",
        "description": "Friendly with casual, everyman quality",
    },
    "Orus": {
        "gender": "male",
        "style": "firm",
        "description": "Mature, deeper, and resonant; wise elder",
    },
    "Puck": {"gender": "male", "style": "upbeat", "description": "Clear, direct, and approachable"},
    "Rasalgethi": {
        "gender": "male",
        "style": "informative",
        "description": "Conversational with inquisitive quality",
    },
    "Sadachbia": {
        "gender": "male",
        "style": "lively",
        "description": "Deeper voice with slight rasp; cool authority",
    },
    "Sadaltager": {
        "gender": "male",
        "style": "knowledgeable",
        "description": "Friendly and enthusiastic; professional",
    },
    "Schedar": {
        "gender": "male",
        "style": "even",
        "description": "Friendly and informal; down-to-earth",
    },
    "Umbriel": {"gender": "male", "style": "easy-going", "description": "Smooth and knowledgeable"},
    "Zubenelgenubi": {
        "gender": "male",
        "style": "casual",
        "description": "Deep and resonant; strong authority",
    },
}

# Recommended voices by gender for character assignment
RECOMMENDED_FEMALE_VOICES = ["Aoede", "Kore", "Laomedeia", "Sulafat", "Despina"]
RECOMMENDED_MALE_VOICES = ["Puck", "Charon", "Fenrir", "Orus", "Umbriel"]


class GoogleTTSClient(TTSClient):
    """Google TTS 2.5 Flash client using Gemini API.

    This client uses the "Director" method for expressive TTS:
    - Audio Profile: Character identity
    - Scene: Environment/vibe
    - Director's Notes: Style, accent, pace
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-flash-preview-tts",
        default_voice: str = "Kore",
    ) -> None:
        """Initialize Google TTS client.

        Args:
            api_key: Google API key
            model: Google TTS model name
            default_voice: Default prebuilt voice name
        """
        self.api_key = api_key
        self.model = model
        self.default_voice = default_voice
        self._client: Optional[any] = None

    def _init_client(self) -> any:
        """Initialize Google GenAI client (lazy loading).

        Returns:
            Google GenAI client instance

        Raises:
            AudioGenerationError: If initialization fails
        """
        if self._client is not None:
            return self._client

        try:
            from google import genai

            self._client = genai.Client(api_key=self.api_key)
            logger.info("Google TTS client initialized")
            return self._client
        except ImportError:
            raise AudioGenerationError(
                "google-generativeai package not installed. "
                "Install with: pip install google-generativeai"
            )
        except Exception as e:
            raise AudioGenerationError(f"Failed to initialize Google TTS client: {e}") from e

    @retry_with_backoff(
        max_retries=3, 
        exceptions=(AudioGenerationError,),
        custom_intervals=[1.0, 20.0, 60.0],  # Wait longer for API quota recovery
    )
    async def generate_speech(
        self,
        text: str,
        voice_id: str,
        emotion: Optional[EmotionTone] = None,
        style_instruction: Optional[str] = None,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate speech from text using Google TTS.

        Args:
            text: Text to convert to speech
            voice_id: Voice name (Google prebuilt voice)
            emotion: Optional emotion tone (for backward compatibility, converted to style)
            style_instruction: Optional custom style instruction (e.g., "dramatic dialogue from a Sci-Fi video game")
                             Takes precedence over emotion if both provided
            output_path: Optional path to save audio file

        Returns:
            Path to generated audio file (WAV format)

        Raises:
            AudioGenerationError: If generation fails
        """
        try:
            from google.genai import types

            client = self._init_client()

            # Build styled prompt using the "Director" method
            # Priority: style_instruction > emotion > plain text
            if style_instruction:
                styled_prompt = self._build_custom_styled_prompt(text, style_instruction)
            elif emotion:
                styled_prompt = self._build_emotion_styled_prompt(text, emotion)
            else:
                styled_prompt = text

            # Use provided voice or default
            voice_name = voice_id if voice_id else self.default_voice

            logger.info(
                f"Generating speech: {len(text)} chars, voice={voice_name}, emotion={emotion}"
            )

            # Generate audio using Gemini API
            response = client.models.generate_content(
                model=self.model,
                contents=styled_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
                        )
                    ),
                ),
            )

            # Validate response
            if not response or not response.candidates:
                raise AudioGenerationError(
                    f"Empty response from Google TTS API. Text: '{text[:50]}...'"
                )
            
            candidate = response.candidates[0]
            if not candidate.content or not candidate.content.parts:
                raise AudioGenerationError(
                    f"No audio content in response. Text: '{text[:50]}...', "
                    f"Response: {response}"
                )

            # Extract audio data (PCM format)
            audio_data = candidate.content.parts[0].inline_data.data

            # Save as WAV (Google TTS returns PCM at 24kHz)
            if output_path is None:
                output_path = Path(f"audio_{hash(text)}.wav")

            # Ensure output path has .wav extension
            if output_path.suffix.lower() != ".wav":
                output_path = output_path.with_suffix(".wav")

            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save PCM data as WAV
            self._save_wave_file(output_path, audio_data)

            logger.info(f"Audio saved to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Google TTS speech generation failed: {e}")
            raise AudioGenerationError(f"Speech generation failed: {e}") from e

    def _build_emotion_styled_prompt(self, text: str, emotion: EmotionTone) -> str:
        """Build styled prompt from EmotionTone using the "Director" method.

        Args:
            text: Original text
            emotion: Emotion tone

        Returns:
            Styled prompt with director's notes
        """
        if emotion in EMOTION_STYLE_DIRECTIVES:
            style_directive = EMOTION_STYLE_DIRECTIVES[emotion]
            # Format: "Say in [style]: [text]"
            prompt = f"Say in a {style_directive}: {text}"
            logger.debug(f"Using emotion style for {emotion}: {style_directive}")
        else:
            # No matching emotion, just the text
            prompt = text

        return prompt

    def _build_custom_styled_prompt(self, text: str, style_instruction: str) -> str:
        """Build styled prompt from custom style instruction.

        Args:
            text: Original text
            style_instruction: Custom style instruction (e.g., "dramatic dialogue from a Sci-Fi video game")

        Returns:
            Styled prompt with custom instruction
        """
        # Format: "Say in [custom style]: [text]"
        prompt = f"Say in {style_instruction}: {text}"
        logger.debug(f"Using custom style: {style_instruction}")
        return prompt

    def _save_wave_file(self, filename: Path, pcm_data: bytes) -> None:
        """Save PCM data as WAV file.

        Args:
            filename: Output WAV file path
            pcm_data: PCM audio data
        """
        with wave.open(str(filename), "wb") as wf:
            wf.setnchannels(1)  # Mono
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(24000)  # 24kHz sample rate
            wf.writeframes(pcm_data)

    def get_available_voices(self) -> list[dict[str, str]]:
        """Get list of available Google TTS voices.

        Returns:
            List of voice metadata with gender and characteristics
        """
        return [
            {
                "id": voice_name,
                "name": voice_name,
                "gender": metadata["gender"],
                "style": metadata["style"],
                "description": metadata["description"],
                "category": "prebuilt",
            }
            for voice_name, metadata in GOOGLE_TTS_VOICE_METADATA.items()
        ]

    def get_voices_by_gender(self, gender: str) -> list[str]:
        """Get list of voice names filtered by gender.

        Args:
            gender: 'male' or 'female'

        Returns:
            List of voice names matching the gender
        """
        gender_lower = gender.lower()
        return [
            voice_name
            for voice_name, metadata in GOOGLE_TTS_VOICE_METADATA.items()
            if metadata["gender"] == gender_lower
        ]

    def get_recommended_voice_for_gender(self, gender: str, index: int = 0) -> str:
        """Get a recommended voice for a specific gender.

        Args:
            gender: 'male' or 'female'
            index: Index in the recommended list (for variety when multiple characters)

        Returns:
            Voice name
        """
        gender_lower = gender.lower()
        if gender_lower == "female":
            voices = RECOMMENDED_FEMALE_VOICES
        elif gender_lower == "male":
            voices = RECOMMENDED_MALE_VOICES
        else:
            # Default to female if gender not recognized
            voices = RECOMMENDED_FEMALE_VOICES

        # Use modulo to cycle through voices if index exceeds list length
        return voices[index % len(voices)]

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

        # Add small buffer for pauses and style
        return duration * 1.15
