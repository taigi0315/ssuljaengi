"""Engagement overlay generator for viewer participation hooks.

Renders engagement hooks as top-positioned text overlays in ASS format.
"""

import logging
import re
from pathlib import Path

from gossiptoon.core.utils import format_timestamp_ass
from gossiptoon.models.audio import AudioProject
from gossiptoon.models.engagement import EngagementProject, EngagementStyle
from gossiptoon.models.script import Script

logger = logging.getLogger(__name__)


class EngagementOverlayGenerator:
    """Generates engagement hook overlays in ASS format."""

    # Style-based colors (BGR format for ASS)
    STYLE_COLORS = {
        EngagementStyle.QUESTION: "00FFFF",      # Yellow - questions
        EngagementStyle.COMMENT: "FF8C00",       # Dark Orange - comments
        EngagementStyle.REACTION: "FF69B4",      # Hot Pink - polls
        EngagementStyle.SYMPATHY: "87CEEB",      # Sky Blue - sympathy
        EngagementStyle.CONFLICT: "0000FF",      # Red - conflict
    }

    def __init__(
        self,
        font_name: str = "Arial",
        font_size: int = 72,
    ) -> None:
        """Initialize engagement overlay generator.

        Args:
            font_name: Font family to use
            font_size: Font size for overlays
        """
        self.font_name = font_name
        self.font_size = font_size

    def generate_ass_file(
        self,
        engagement_project: EngagementProject,
        script: Script,
        audio_project: AudioProject,
        output_path: Path,
        video_width: int = 1080,
        video_height: int = 1920,
    ) -> Path:
        """Generate ASS overlay file for engagement hooks.

        Args:
            engagement_project: Engagement hooks to render
            script: Script with scene information
            audio_project: Audio timing information
            output_path: Path to write ASS file
            video_width: Video width
            video_height: Video height

        Returns:
            Path to generated ASS file
        """
        logger.info(f"Generating engagement overlay file: {output_path}")

        # Generate header and events
        header = self._generate_header(video_width, video_height)
        events = self._generate_events(
            engagement_project, script, audio_project
        )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(header)
            f.write("\n")
            f.write(events)

        logger.info(
            f"Generated {len(engagement_project.hooks)} engagement overlays"
        )
        return output_path

    def _generate_header(self, width: int, height: int) -> str:
        """Generate ASS file header with engagement styles.

        Args:
            width: Video width
            height: Video height

        Returns:
            ASS header string
        """
        header = f"""[Script Info]
Title: Engagement Overlays
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
"""

        # Add style for each engagement type
        for style_type, color in self.STYLE_COLORS.items():
            # ASS color format: &H00BBGGRR (with alpha)
            primary_color = f"&H00{color}"
            outline_color = "&H00000000"  # Black outline
            back_color = "&H80000000"  # Semi-transparent black background

            style_line = (
                f"Style: {style_type.value},"
                f"{self.font_name},"
                f"{self.font_size},"
                f"{primary_color},"  # Primary color
                f"&H000000FF,"  # Secondary (unused)
                f"{outline_color},"  # Outline
                f"{back_color},"  # Background
                "1,"  # Bold
                "0,"  # Italic
                "0,"  # Underline
                "0,"  # StrikeOut
                "100,"  # ScaleX
                "100,"  # ScaleY
                "1,"  # Spacing
                "0,"  # Angle
                "1,"  # BorderStyle
                "3,"  # Outline thickness
                "2,"  # Shadow
                "8,"  # Alignment (top center)
                "50,"  # MarginL
                "50,"  # MarginR
                f"{int(height * 0.1)},"  # MarginV (10% from top)
                "1"  # Encoding
            )
            header += style_line + "\n"

        header += "\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        return header

    def _sanitize_text(self, text: str) -> str:
        """Remove emojis and unsupported characters.
        
        Args:
            text: Input text
            
        Returns:
            Sanitized text safe for ASS rendering
        """
        # Remove characters in Supplementary Planes (emojis)
        # matches range U+10000 to U+10FFFF
        return re.sub(r'[\U00010000-\U0010ffff]', '', text).strip()

    def _generate_events(
        self,
        engagement_project: EngagementProject,
        script: Script,
        audio_project: AudioProject,
    ) -> str:
        """Generate ASS events for engagement hooks.

        Args:
            engagement_project: Engagement hooks
            script: Script with scenes
            audio_project: Audio timing

        Returns:
            ASS events string
        """
        events = []
        all_scenes = script.get_all_scenes()

        # Build scene timing map
        scene_timings = {}
        current_offset = 0.0
        for scene, audio_segment in zip(all_scenes, audio_project.segments):
            scene_timings[scene.scene_id] = {
                "start": current_offset,
                "duration": audio_segment.duration_seconds,
            }
            current_offset += audio_segment.duration_seconds

        # Generate event for each hook
        for hook in engagement_project.hooks:
            if hook.scene_id not in scene_timings:
                logger.warning(
                    f"Scene {hook.scene_id} not found for hook {hook.hook_id}"
                )
                continue

            scene_timing = scene_timings[hook.scene_id]
            scene_start = scene_timing["start"]
            scene_duration = scene_timing["duration"]

            # Calculate absolute start time based on relative timing
            hook_start = scene_start + (hook.timing * scene_duration)
            hook_end = hook_start + 3.0  # Display for 3 seconds

            # Format timestamps
            start_time = format_timestamp_ass(hook_start)
            end_time = format_timestamp_ass(hook_end)

            # Create dialogue line
            # Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
            event_line = (
                f"Dialogue: 0,"
                f"{start_time},"
                f"{end_time},"
                f"{hook.style.value},"  # Style name
                f"engagement,"  # Name
                "0,0,0,"  # Margins (use style defaults)
                ","  # Effect (none)
                f"{self._sanitize_text(hook.text)}"  # Text
            )
            events.append(event_line)

        return "\n".join(events)
