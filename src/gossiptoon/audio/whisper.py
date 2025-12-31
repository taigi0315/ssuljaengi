"""Whisper timestamp extraction for precise audio-visual sync."""

import logging
from pathlib import Path
from typing import Optional

from gossiptoon.core.exceptions import WhisperError
from gossiptoon.models.audio import WordTimestamp

logger = logging.getLogger(__name__)


class WhisperTimestampExtractor:
    """Extract word-level timestamps from audio using Whisper.

    This is the MASTER CLOCK for the entire video pipeline.
    All visual timing is driven by these timestamps.
    """

    def __init__(self, model_name: str = "base") -> None:
        """Initialize Whisper timestamp extractor.

        Args:
            model_name: Whisper model size (tiny, base, small, medium, large)
        """
        self.model_name = model_name
        self._model: Optional[any] = None

    def _load_model(self) -> any:
        """Load Whisper model (lazy loading).

        Returns:
            Whisper model instance

        Raises:
            WhisperError: If model loading fails
        """
        if self._model is not None:
            return self._model

        try:
            import whisper

            logger.info(f"Loading Whisper model: {self.model_name}")
            self._model = whisper.load_model(self.model_name)
            logger.info("Whisper model loaded successfully")
            return self._model
        except ImportError:
            raise WhisperError(
                "Whisper package not installed. Install with: pip install openai-whisper"
            )
        except Exception as e:
            raise WhisperError(f"Failed to load Whisper model: {e}") from e

    async def extract_timestamps(
        self, audio_path: Path, language: str = "en"
    ) -> list[WordTimestamp]:
        """Extract word-level timestamps from audio file.

        Args:
            audio_path: Path to audio file
            language: Language code (default: "en")

        Returns:
            List of word timestamps

        Raises:
            WhisperError: If extraction fails
        """
        if not audio_path.exists():
            raise WhisperError(f"Audio file not found: {audio_path}")

        try:
            model = self._load_model()

            logger.info(f"Extracting timestamps from {audio_path}")

            # Transcribe with word-level timestamps
            result = model.transcribe(
                str(audio_path),
                language=language,
                word_timestamps=True,
                verbose=False,
            )

            # Extract word timestamps
            timestamps = []
            for segment in result.get("segments", []):
                for word_info in segment.get("words", []):
                    timestamp = WordTimestamp(
                        word=word_info["word"].strip(),
                        start=word_info["start"],
                        end=word_info["end"],
                        confidence=word_info.get("probability", 0.9),
                    )
                    timestamps.append(timestamp)

            logger.info(f"Extracted {len(timestamps)} word timestamps")
            return timestamps

        except Exception as e:
            logger.error(f"Whisper timestamp extraction failed: {e}")
            raise WhisperError(f"Failed to extract timestamps: {e}") from e

    def get_total_duration(self, timestamps: list[WordTimestamp]) -> float:
        """Get total audio duration from timestamps.

        Args:
            timestamps: List of word timestamps

        Returns:
            Total duration in seconds
        """
        if not timestamps:
            return 0.0
        return timestamps[-1].end

    def get_text(self, timestamps: list[WordTimestamp]) -> str:
        """Reconstruct text from timestamps.

        Args:
            timestamps: List of word timestamps

        Returns:
            Complete text
        """
        return " ".join(ts.word for ts in timestamps)

    def split_by_duration(
        self, timestamps: list[WordTimestamp], max_duration: float
    ) -> list[list[WordTimestamp]]:
        """Split timestamps into chunks by duration.

        Args:
            timestamps: List of word timestamps
            max_duration: Maximum duration per chunk

        Returns:
            List of timestamp chunks
        """
        if not timestamps:
            return []

        chunks = []
        current_chunk = []
        chunk_start = timestamps[0].start

        for ts in timestamps:
            # Check if adding this word would exceed max_duration
            if ts.end - chunk_start > max_duration and current_chunk:
                chunks.append(current_chunk)
                current_chunk = [ts]
                chunk_start = ts.start
            else:
                current_chunk.append(ts)

        # Add remaining chunk
        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def align_to_scenes(
        self,
        timestamps: list[WordTimestamp],
        scene_durations: list[float],
    ) -> list[list[WordTimestamp]]:
        """Align timestamps to scene boundaries.

        Args:
            timestamps: List of word timestamps
            scene_durations: List of scene durations

        Returns:
            List of timestamp groups per scene

        Raises:
            WhisperError: If alignment fails
        """
        if not timestamps:
            return [[] for _ in scene_durations]

        scene_timestamps = []
        current_time = 0.0
        timestamp_idx = 0

        for scene_duration in scene_durations:
            scene_end = current_time + scene_duration
            scene_words = []

            # Collect words that fall within this scene's time range
            while timestamp_idx < len(timestamps):
                ts = timestamps[timestamp_idx]

                # Word starts within this scene
                if ts.start < scene_end:
                    scene_words.append(ts)
                    timestamp_idx += 1
                else:
                    break

            scene_timestamps.append(scene_words)
            current_time = scene_end

        # Handle any remaining timestamps
        if timestamp_idx < len(timestamps):
            logger.warning(
                f"{len(timestamps) - timestamp_idx} timestamps not aligned to any scene"
            )

        return scene_timestamps
