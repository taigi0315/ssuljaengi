"""Audio data models for TTS and timestamp information."""

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from gossiptoon.core.constants import EmotionTone


class WordTimestamp(BaseModel):
    """Word-level timestamp from Whisper."""

    word: str = Field(..., description="Word text")
    start: float = Field(ge=0, description="Start time in seconds")
    end: float = Field(ge=0, description="End time in seconds")
    confidence: float = Field(ge=0, le=1, description="Whisper confidence score")

    @property
    def duration(self) -> float:
        """Get word duration.

        Returns:
            Duration in seconds
        """
        return self.end - self.start

    def overlaps_with(self, start: float, end: float) -> bool:
        """Check if timestamp overlaps with time range.

        Args:
            start: Range start time
            end: Range end time

        Returns:
            True if overlaps
        """
        return not (self.end <= start or self.start >= end)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "word": "Hello",
                "start": 0.5,
                "end": 0.9,
                "confidence": 0.95,
            }
        }


class AudioSegment(BaseModel):
    """Audio generated for a scene."""

    scene_id: str = Field(..., description="Reference to scene")
    file_path: Path = Field(..., description="Path to audio file")
    duration_seconds: float = Field(ge=0, description="Audio duration")
    emotion: EmotionTone = Field(..., description="Emotion tone used")
    voice_id: str = Field(..., description="ElevenLabs voice ID used")
    timestamps: list[WordTimestamp] = Field(
        default_factory=list, description="Word-level timestamps"
    )
    sample_rate: int = Field(default=44100, description="Audio sample rate")
    channels: int = Field(default=1, description="Number of audio channels (1=mono, 2=stereo)")

    def get_timestamps_in_range(self, start: float, end: float) -> list[WordTimestamp]:
        """Get timestamps within a time range.

        Args:
            start: Range start time
            end: Range end time

        Returns:
            List of timestamps in range
        """
        return [ts for ts in self.timestamps if ts.overlaps_with(start, end)]

    def get_word_at_time(self, time: float) -> Optional[WordTimestamp]:
        """Get word being spoken at specific time.

        Args:
            time: Time in seconds

        Returns:
            WordTimestamp if found, None otherwise
        """
        for ts in self.timestamps:
            if ts.start <= time < ts.end:
                return ts
        return None

    def get_text(self) -> str:
        """Get full text from timestamps.

        Returns:
            Complete text
        """
        return " ".join(ts.word for ts in self.timestamps)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "scene_id": "scene_hook_01",
                "file_path": "/outputs/audio/scene_hook_01.mp3",
                "duration_seconds": 4.5,
                "emotion": "shocked",
                "voice_id": "21m00Tcm4TlvDq8ikWAM",
            }
        }


class AudioProject(BaseModel):
    """Complete audio project for a script."""

    script_id: str = Field(..., description="Reference to script")
    segments: list[AudioSegment] = Field(..., description="Audio segments for each scene")
    total_duration: float = Field(ge=0, description="Total audio duration")
    master_audio_path: Optional[Path] = Field(
        None, description="Path to combined master audio file"
    )
    voice_id: str = Field(..., description="Primary voice ID used")

    def get_segment_by_scene(self, scene_id: str) -> Optional[AudioSegment]:
        """Retrieve segment for specific scene.

        Args:
            scene_id: Scene identifier

        Returns:
            AudioSegment if found, None otherwise
        """
        return next((s for s in self.segments if s.scene_id == scene_id), None)

    def get_all_timestamps(self) -> list[WordTimestamp]:
        """Get all timestamps across all segments.

        Returns:
            Flattened list of timestamps
        """
        all_timestamps = []
        current_time = 0.0

        for segment in self.segments:
            # Adjust timestamps relative to total timeline
            for ts in segment.timestamps:
                adjusted = WordTimestamp(
                    word=ts.word,
                    start=current_time + ts.start,
                    end=current_time + ts.end,
                    confidence=ts.confidence,
                )
                all_timestamps.append(adjusted)
            current_time += segment.duration_seconds

        return all_timestamps

    def get_segment_start_time(self, scene_id: str) -> float:
        """Get start time of a segment in the master timeline.

        Args:
            scene_id: Scene identifier

        Returns:
            Start time in seconds, or 0.0 if not found
        """
        start_time = 0.0
        for segment in self.segments:
            if segment.scene_id == scene_id:
                return start_time
            start_time += segment.duration_seconds
        return 0.0

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "script_id": "script_20250101_abc123",
                "total_duration": 55.5,
                "voice_id": "21m00Tcm4TlvDq8ikWAM",
                "master_audio_path": "/outputs/audio/script_20250101_abc123_master.mp3",
            }
        }
