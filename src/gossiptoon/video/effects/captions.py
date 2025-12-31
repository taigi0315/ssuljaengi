"""Dynamic caption effect with word-level synchronization.

Syncs captions to Whisper word timestamps for frame-perfect timing.
Highly customizable styling and animation.
"""

import re
from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import Field

from gossiptoon.models.audio import WordTimestamp
from gossiptoon.video.effects.base import Effect, EffectConfig


class CaptionConfig(EffectConfig):
    """Configuration for caption effect.

    All visual parameters are tunable.
    """

    # Font styling
    font_family: str = Field(default="Arial", description="Font family name")
    font_size: int = Field(default=48, ge=20, le=100, description="Font size in pixels")
    font_color: str = Field(default="white", description="Font color (hex or name)")
    font_weight: Literal["normal", "bold"] = Field(default="bold", description="Font weight")

    # Outline/stroke
    outline_color: str = Field(default="black", description="Outline color")
    outline_width: int = Field(default=2, ge=0, le=10, description="Outline width")

    # Background box
    box_enabled: bool = Field(default=True, description="Enable background box")
    box_color: str = Field(default="black@0.6", description="Box color with alpha")
    box_padding: int = Field(default=10, ge=0, le=50, description="Box padding in pixels")

    # Position
    position_x: Literal["left", "center", "right"] = Field(
        default="center",
        description="Horizontal position",
    )
    position_y: Literal["top", "middle", "bottom"] = Field(
        default="bottom",
        description="Vertical position",
    )
    margin_x: int = Field(default=50, ge=0, description="Horizontal margin from edge")
    margin_y: int = Field(default=100, ge=0, description="Vertical margin from edge")

    # Animation
    fade_in_duration: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Fade in duration in seconds",
    )
    fade_out_duration: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Fade out duration in seconds",
    )

    # Word highlighting (optional)
    highlight_enabled: bool = Field(
        default=True,
        description="Highlight current word",
    )
    highlight_color: str = Field(default="yellow", description="Highlight color")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "enabled": True,
                "font_family": "Arial",
                "font_size": 48,
                "font_color": "white",
                "box_enabled": True,
                "box_color": "black@0.6",
                "position_y": "bottom",
                "margin_y": 100,
                "highlight_enabled": True,
            }
        }


class CaptionEffect(Effect):
    """Caption effect with word-level timing.

    Technical approach:
    - Generates subtitle file (ASS format) with precise timing
    - Uses FFmpeg's subtitles filter
    - Supports word-level highlighting
    """

    def __init__(self, config: CaptionConfig) -> None:
        """Initialize caption effect.

        Args:
            config: Caption configuration
        """
        super().__init__(config)
        self.config: CaptionConfig = config

    def get_filter_string(
        self,
        input_label: str,
        output_label: str,
        **context: Any,
    ) -> str:
        """Generate subtitles filter string.

        Args:
            input_label: Input stream label
            output_label: Output stream label
            **context: Must contain 'subtitle_file' (path to ASS file)

        Returns:
            FFmpeg subtitles filter string

        Example:
            "[v0]subtitles=captions.ass[v1]"
        """
        subtitle_file = context.get("subtitle_file")

        if not subtitle_file:
            # No subtitles - pass through
            return f"{input_label}copy{output_label}"

        # Escape path for FFmpeg (Windows compatibility)
        escaped_path = self._escape_ffmpeg_path(str(subtitle_file))

        filter_str = f"{input_label}subtitles={escaped_path}{output_label}"

        return filter_str

    def generate_subtitle_file(
        self,
        word_timestamps: list[WordTimestamp],
        output_path: Path,
        video_width: int = 1080,
        video_height: int = 1920,
    ) -> Path:
        """Generate ASS subtitle file from word timestamps.

        Args:
            word_timestamps: List of word timestamps from Whisper
            output_path: Path to save subtitle file
            video_width: Video width for positioning
            video_height: Video height for positioning

        Returns:
            Path to generated subtitle file
        """
        # Build ASS file content
        ass_content = self._build_ass_header(video_width, video_height)

        # Group words into caption lines (every 5-8 words or by timing)
        caption_lines = self._group_words_into_lines(word_timestamps)

        # Generate events for each caption line
        for line in caption_lines:
            event = self._create_caption_event(line)
            ass_content += event

        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(ass_content)

        return output_path

    def _build_ass_header(self, video_width: int, video_height: int) -> str:
        """Build ASS file header with styling.

        Args:
            video_width: Video width
            video_height: Video height

        Returns:
            ASS header string
        """
        # Calculate position based on config
        if self.config.position_x == "left":
            align_x = 1  # Left
        elif self.config.position_x == "right":
            align_x = 3  # Right
        else:
            align_x = 2  # Center

        if self.config.position_y == "top":
            align_y = 1
        elif self.config.position_y == "middle":
            align_y = 2
        else:
            align_y = 3  # Bottom

        alignment = align_x + (align_y - 1) * 3

        # Calculate margin
        margin_v = self.config.margin_y
        margin_l = self.config.margin_x
        margin_r = self.config.margin_x

        # Convert colors to ASS format (&HAABBGGRR)
        font_color = self._color_to_ass(self.config.font_color)
        outline_color = self._color_to_ass(self.config.outline_color)

        header = f"""[Script Info]
Title: GossipToon Captions
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{self.config.font_family},{self.config.font_size},{font_color},&H00FFFFFF,{outline_color},&H80000000,{1 if self.config.font_weight == 'bold' else 0},0,0,0,100,100,0,0,{'3' if self.config.box_enabled else '1'},{self.config.outline_width},0,{alignment},{margin_l},{margin_r},{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        return header

    def _group_words_into_lines(
        self,
        word_timestamps: list[WordTimestamp],
        max_words_per_line: int = 6,
        max_line_duration: float = 3.0,
    ) -> list[list[WordTimestamp]]:
        """Group words into caption lines.

        Args:
            word_timestamps: List of word timestamps
            max_words_per_line: Maximum words per line
            max_line_duration: Maximum line duration in seconds

        Returns:
            List of caption lines (each line is list of words)
        """
        if not word_timestamps:
            return []

        lines = []
        current_line = []
        line_start_time = word_timestamps[0].start

        for word in word_timestamps:
            # Check if we should start new line
            should_break = (
                len(current_line) >= max_words_per_line
                or (word.start - line_start_time) >= max_line_duration
            )

            if should_break and current_line:
                lines.append(current_line)
                current_line = []
                line_start_time = word.start

            current_line.append(word)

        # Add remaining words
        if current_line:
            lines.append(current_line)

        return lines

    def _create_caption_event(self, words: list[WordTimestamp]) -> str:
        """Create ASS event for caption line.

        Args:
            words: List of words in this caption

        Returns:
            ASS event string
        """
        if not words:
            return ""

        start_time = words[0].start
        end_time = words[-1].end

        # Build caption text
        if self.config.highlight_enabled:
            # With word-level highlighting
            text_parts = []
            for i, word in enumerate(words):
                # Calculate relative timing within line
                word_start = word.start - start_time
                word_end = word.end - start_time

                # Highlight effect (color change)
                highlight_start = int(word_start * 100)  # Centiseconds
                highlight_end = int(word_end * 100)

                highlighted = (
                    f"{{\\t({highlight_start},{highlight_end},"
                    f"\\c&H{self._color_to_ass(self.config.highlight_color)}&)}}"
                    f"{word.word}"
                )
                text_parts.append(highlighted)

            caption_text = " ".join(text_parts)
        else:
            # Simple text without highlighting
            caption_text = " ".join(w.word for w in words)

        # Format timestamps for ASS (H:MM:SS.SS)
        start_formatted = self._format_ass_time(start_time)
        end_formatted = self._format_ass_time(end_time)

        # Create event
        event = f"Dialogue: 0,{start_formatted},{end_formatted},Default,,0,0,0,,{caption_text}\n"

        return event

    def _format_ass_time(self, seconds: float) -> str:
        """Format time for ASS subtitle format.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time (H:MM:SS.CS)
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int((seconds % 1) * 100)

        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"

    def _color_to_ass(self, color: str) -> str:
        """Convert color to ASS format.

        Args:
            color: Color name or hex

        Returns:
            ASS color format (&HAABBGGRR)
        """
        # Simple color mapping
        color_map = {
            "white": "&H00FFFFFF",
            "black": "&H00000000",
            "yellow": "&H0000FFFF",
            "red": "&H000000FF",
            "green": "&H0000FF00",
            "blue": "&H00FF0000",
        }

        if color in color_map:
            return color_map[color]

        # For hex colors, convert #RRGGBB to &H00BBGGRR
        if color.startswith("#") and len(color) == 7:
            r = color[1:3]
            g = color[3:5]
            b = color[5:7]
            return f"&H00{b}{g}{r}"

        # Default to white
        return "&H00FFFFFF"

    def _escape_ffmpeg_path(self, path: str) -> str:
        """Escape file path for FFmpeg.

        Args:
            path: File path

        Returns:
            Escaped path
        """
        # Escape special characters for FFmpeg
        # Windows: backslashes and colons
        # Unix: just escape colons
        escaped = path.replace("\\", "/")  # Normalize to forward slashes
        escaped = escaped.replace(":", "\\:")  # Escape colons
        return escaped

    def get_effect_name(self) -> str:
        """Get effect name.

        Returns:
            Effect name
        """
        return f"Captions(font:{self.config.font_family}/{self.config.font_size}, pos:{self.config.position_y})"

    def get_tunable_params(self) -> dict[str, Any]:
        """Get tunable parameters.

        Returns:
            Dictionary of tunable parameters
        """
        return {
            "font_size": self.config.font_size,
            "font_color": self.config.font_color,
            "position_y": self.config.position_y,
            "margin_y": self.config.margin_y,
            "box_enabled": self.config.box_enabled,
            "highlight_enabled": self.config.highlight_enabled,
        }
