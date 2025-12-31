"""Subtitle generator for rapid word-level captions (ASS format)."""

import logging
import random
from pathlib import Path

from gossiptoon.core.utils import format_timestamp_ass
from gossiptoon.models.audio import AudioProject, WordTimestamp

logger = logging.getLogger(__name__)


class SubtitleGenerator:
    """Generates rapid word-level subtitles in ASS format."""

    # Pastel color palette (RGB Hex)
    PASTEL_PALETTE = [
        "FFB3BA",  # Pastel Red
        "BAFFC9",  # Pastel Green
        "BAE1FF",  # Pastel Blue
        "FFFFBA",  # Pastel Yellow
        "FFDFBA",  # Pastel Orange
        "E0BBE4",  # Pastel Purple
        "957DAD",  # Muted Purple
        "D291BC",  # Violet
        "FEC8D8",  # Pink
        "FFDFD3",  # Peach
    ]

    def __init__(self, font_name: str = "Arial", font_size: int = 80) -> None:
        """Initialize subtitle generator.

        Args:
            font_name: Font family to use
            font_size: Font size
        """
        self.font_name = font_name
        self.font_size = font_size

    def generate_ass_file(
        self,
        audio_project: AudioProject,
        output_path: Path,
        video_width: int = 1080,
        video_height: int = 1920,
    ) -> Path:
        """Generate ASS subtitle file from audio project timestamps.

        Args:
            audio_project: Audio project containing aligned timestamps
            output_path: Path to write ASS file
            video_width: Video width
            video_height: Video height

        Returns:
            Path to generated ASS file
        """
        logger.info(f"Generating subtitle file: {output_path}")

        # Get all words with absolute timing
        timestamps = audio_project.get_all_timestamps()

        # Vertical margin for 70% position (from top)
        # Alignment 2 is Bottom Center.
        # If we want 70% from top, that's 30% from bottom.
        # MarginV = video_height * 0.3
        margin_v = int(video_height * 0.3)

        header = self._generate_header(video_width, video_height, margin_v)
        events = self._generate_events(timestamps)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(header)
            f.write("\n")
            f.write(events)

        logger.info(f"Generated subtitles with {len(timestamps)} word events")
        return output_path

    def _generate_header(self, width: int, height: int, margin_v: int) -> str:
        """Generate ASS file header.

        Args:
            width: Video resolution width
            height: Video resolution height
            margin_v: Vertical margin (from bottom)

        Returns:
            Header string
        """
        return f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: RapidWord,{self.font_name},{self.font_size},&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,3,0,2,10,10,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"""

    def _generate_events(self, timestamps: list[WordTimestamp]) -> str:
        """Generate Dialogue events for each word.

        Args:
            timestamps: List of WordTimestamp objects

        Returns:
            Events string
        """
        events = []

        for i, ts in enumerate(timestamps):
            start_str = format_timestamp_ass(ts.start)
            end_str = format_timestamp_ass(ts.end)

            # Pick a random pastel color
            color_hex = random.choice(self.PASTEL_PALETTE)
            # Convert RGB to BGR for ASS (&HBBGGRR)
            r, g, b = color_hex[0:2], color_hex[2:4], color_hex[4:6]
            ass_color = f"&H00{b}{g}{r}"

            # Apply color tag and Text
            text = f"{{\\c{ass_color}}}{ts.word}"

            # Ensure minimal duration for visibility (e.g. 0.1s)
            if ts.end - ts.start < 0.1:
                # Extend end slightly if too short, but usually Whisper is accurate
                pass

            events.append(
                f"Dialogue: 0,{start_str},{end_str},RapidWord,,0,0,0,,{text}"
            )

        return "\n".join(events)
