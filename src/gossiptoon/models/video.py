"""Video data models for rendering and effects."""

from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from gossiptoon.core.constants import (
    DEFAULT_AUDIO_CODEC,
    DEFAULT_VIDEO_CODEC,
    DEFAULT_VIDEO_FPS,
    DEFAULT_VIDEO_PRESET,
    DEFAULT_VIDEO_RESOLUTION,
    CameraEffectType,
)


class EffectConfig(BaseModel):
    """Configuration for a video effect."""

    effect_type: CameraEffectType = Field(..., description="Type of effect")
    params: dict[str, Any] = Field(default_factory=dict, description="Effect parameters")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "effect_type": "ken_burns",
                "params": {
                    "zoom_start": 1.0,
                    "zoom_end": 1.2,
                    "direction": "in",
                },
            }
        }


class TimelineSegment(BaseModel):
    """A segment on the video timeline."""

    scene_id: str = Field(..., description="Reference to scene")
    start_time: float = Field(ge=0, description="Start time in seconds")
    end_time: float = Field(ge=0, description="End time in seconds")
    visual_asset_path: Path = Field(..., description="Path to image/video asset")
    audio_segment_path: Path = Field(..., description="Path to audio file")
    effects: list[EffectConfig] = Field(default_factory=list, description="Effects to apply")

    @property
    def duration(self) -> float:
        """Get segment duration.

        Returns:
            Duration in seconds
        """
        return self.end_time - self.start_time

    @field_validator("end_time")
    @classmethod
    def validate_end_after_start(cls, v: float, info: object) -> float:
        """Ensure end time is after start time.

        Args:
            v: End time
            info: Validation info

        Returns:
            Validated end time

        Raises:
            ValueError: If end time is not after start time
        """
        if hasattr(info, "data") and "start_time" in info.data:
            start_time = info.data["start_time"]
            if v <= start_time:
                raise ValueError(f"End time ({v}) must be after start time ({start_time})")
        return v

    def has_effect(self, effect_type: CameraEffectType) -> bool:
        """Check if segment has specific effect type.

        Args:
            effect_type: Effect type to check

        Returns:
            True if effect is present
        """
        return any(e.effect_type == effect_type for e in self.effects)

    def get_effect(self, effect_type: CameraEffectType) -> Optional[EffectConfig]:
        """Get effect configuration by type.

        Args:
            effect_type: Effect type to find

        Returns:
            EffectConfig if found, None otherwise
        """
        return next((e for e in self.effects if e.effect_type == effect_type), None)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "scene_id": "scene_hook_01",
                "start_time": 0.0,
                "end_time": 4.5,
                "visual_asset_path": "/outputs/images/scene_hook_01.png",
                "audio_segment_path": "/outputs/audio/scene_hook_01.mp3",
            }
        }


class CaptionSegment(BaseModel):
    """Caption with timing information."""

    text: str = Field(..., min_length=1, description="Caption text")
    start_time: float = Field(ge=0, description="Start time in seconds")
    end_time: float = Field(ge=0, description="End time in seconds")
    style: dict[str, Any] = Field(
        default_factory=lambda: {
            "fontsize": 48,
            "fontcolor": "white",
            "font": "Arial-Bold",
            "box": 1,
            "boxcolor": "black@0.5",
            "boxborderw": 5,
        },
        description="Caption styling parameters",
    )
    position: str = Field(default="bottom", description="Caption position (top/middle/bottom)")

    @property
    def duration(self) -> float:
        """Get caption duration.

        Returns:
            Duration in seconds
        """
        return self.end_time - self.start_time

    @field_validator("text")
    @classmethod
    def escape_special_chars(cls, v: str) -> str:
        """Escape special characters for FFmpeg.

        Args:
            v: Caption text

        Returns:
            Escaped text
        """
        # FFmpeg requires escaping of certain characters in drawtext filter
        # This will be done in the FFmpeg builder, but we validate here
        return v

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "text": "You won't believe",
                "start_time": 0.5,
                "end_time": 1.2,
                "position": "bottom",
            }
        }


class RenderConfig(BaseModel):
    """Video rendering configuration."""

    resolution: str = Field(default=DEFAULT_VIDEO_RESOLUTION, description="Video resolution")
    fps: int = Field(default=DEFAULT_VIDEO_FPS, ge=24, le=60, description="Frames per second")
    video_codec: str = Field(default=DEFAULT_VIDEO_CODEC, description="Video codec")
    audio_codec: str = Field(default=DEFAULT_AUDIO_CODEC, description="Audio codec")
    bitrate: str = Field(default="5M", description="Video bitrate")
    preset: str = Field(default=DEFAULT_VIDEO_PRESET, description="FFmpeg preset")
    output_format: str = Field(default="mp4", description="Output file format")
    pixel_format: str = Field(default="yuv420p", description="Pixel format")

    @field_validator("resolution")
    @classmethod
    def validate_resolution(cls, v: str) -> str:
        """Validate resolution format.

        Args:
            v: Resolution string

        Returns:
            Validated resolution

        Raises:
            ValueError: If resolution format is invalid
        """
        if "x" not in v:
            raise ValueError("Resolution must be in format WIDTHxHEIGHT")
        try:
            width, height = map(int, v.split("x"))
            if width <= 0 or height <= 0:
                raise ValueError("Resolution dimensions must be positive")
        except ValueError as e:
            raise ValueError(f"Invalid resolution format: {v}") from e
        return v

    @field_validator("preset")
    @classmethod
    def validate_preset(cls, v: str) -> str:
        """Validate FFmpeg preset.

        Args:
            v: Preset name

        Returns:
            Validated preset
        """
        valid_presets = [
            "ultrafast",
            "superfast",
            "veryfast",
            "faster",
            "fast",
            "medium",
            "slow",
            "slower",
            "veryslow",
        ]
        if v not in valid_presets:
            raise ValueError(f"Preset must be one of {valid_presets}")
        return v

    def get_width_height(self) -> tuple[int, int]:
        """Parse resolution into width and height.

        Returns:
            Tuple of (width, height)
        """
        width, height = map(int, self.resolution.split("x"))
        return width, height

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "resolution": "1080x1920",
                "fps": 30,
                "video_codec": "libx264",
                "preset": "medium",
            }
        }


class VideoProject(BaseModel):
    """Complete video project for rendering."""

    project_id: str = Field(..., description="Unique project identifier")
    script_id: str = Field(..., description="Reference to script")
    timeline: list[TimelineSegment] = Field(..., description="Timeline segments")
    captions: list[CaptionSegment] = Field(
        default_factory=list, description="Caption segments"
    )
    render_config: RenderConfig = Field(
        default_factory=RenderConfig, description="Rendering configuration"
    )
    output_path: Optional[Path] = Field(None, description="Path to rendered video")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Project metadata")

    @property
    def total_duration(self) -> float:
        """Calculate total video duration from timeline.

        Returns:
            Total duration in seconds
        """
        if not self.timeline:
            return 0.0
        return max(seg.end_time for seg in self.timeline)

    def get_segment_at_time(self, time: float) -> Optional[TimelineSegment]:
        """Get timeline segment at specific time.

        Args:
            time: Time in seconds

        Returns:
            TimelineSegment if found, None otherwise
        """
        for segment in self.timeline:
            if segment.start_time <= time < segment.end_time:
                return segment
        return None

    def get_captions_at_time(self, time: float) -> list[CaptionSegment]:
        """Get all captions active at specific time.

        Args:
            time: Time in seconds

        Returns:
            List of active captions
        """
        return [
            cap
            for cap in self.captions
            if cap.start_time <= time < cap.end_time
        ]

    def get_segment_by_scene(self, scene_id: str) -> Optional[TimelineSegment]:
        """Get timeline segment for specific scene.

        Args:
            scene_id: Scene identifier

        Returns:
            TimelineSegment if found, None otherwise
        """
        return next((seg for seg in self.timeline if seg.scene_id == scene_id), None)

    def validate_timeline_continuity(self) -> bool:
        """Check if timeline segments are continuous without gaps.

        Returns:
            True if timeline is continuous
        """
        if not self.timeline:
            return True

        sorted_timeline = sorted(self.timeline, key=lambda s: s.start_time)
        for i in range(len(sorted_timeline) - 1):
            current = sorted_timeline[i]
            next_seg = sorted_timeline[i + 1]
            if abs(current.end_time - next_seg.start_time) > 0.01:  # Allow small floating point errors
                return False
        return True

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "project_id": "project_20250101_abc123",
                "script_id": "script_20250101_abc123",
                "output_path": "/outputs/videos/final_20250101_abc123.mp4",
            }
        }
