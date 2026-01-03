"""Subtitle generator for hybrid subtitles (ASS format).

Supports two modes:
- Rapid: Word-by-word with random pastel colors (intense moments)
- Sentence: Full sentence with white color (calm narration)
"""

import logging
import random
from pathlib import Path

from gossiptoon.core.constants import EmotionTone
from gossiptoon.core.utils import format_timestamp_ass
from gossiptoon.models.audio import AudioProject, AudioSegment, WordTimestamp

logger = logging.getLogger(__name__)


class SubtitleGenerator:
    """Generates hybrid subtitles in ASS format.
    
    Supports two modes based on emotion:
    - Rapid: Word-by-word for intense moments
    - Sentence: Full sentence for calm narration
    """

    # Pastel color palette for rapid mode (RGB Hex)
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
    
    # High arousal emotions trigger rapid mode
    INTENSE_EMOTIONS = {
        EmotionTone.ANGRY,
        EmotionTone.EXCITED,
        EmotionTone.SHOCKED,
        EmotionTone.SUSPENSEFUL,
        EmotionTone.DRAMATIC,
    }

    def __init__(
        self,
        font_name: str = "Arial",
        rapid_font_size: int = 80,
        sentence_font_size: int = 64,
    ) -> None:
        """Initialize subtitle generator.

        Args:
            font_name: Font family to use
            rapid_font_size: Font size for rapid mode
            sentence_font_size: Font size for sentence mode
        """
        self.font_name = font_name
        self.rapid_font_size = rapid_font_size
        self.sentence_font_size = sentence_font_size

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

        # Generate events for each segment (emotion-based mode switching)
        header = self._generate_header(video_width, video_height)
        events = self._generate_events_hybrid(audio_project, video_height)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(header)
            f.write("\n")
            f.write(events)

        logger.info(f"Generated hybrid subtitles for {len(audio_project.segments)} segments")
        return output_path

    def _generate_header(self, width: int, height: int) -> str:
        """Generate ASS file header with dual styles.

        Args:
            width: Video resolution width
            height: Video resolution height

        Returns:
            Header string
        """
        # Rapid mode: 70% from top = 30% from bottom
        rapid_margin_v = int(height * 0.3)
        # Sentence mode: 10% from bottom
        sentence_margin_v = int(height * 0.1)
        
        return f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: RapidWord,{self.font_name},{self.rapid_font_size},&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,3,0,2,10,10,{rapid_margin_v},1
Style: SentenceMode,{self.font_name},{self.sentence_font_size},&H0000FFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,{sentence_margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"""

    def _generate_events_hybrid(self, audio_project: AudioProject, video_height: int) -> str:
        """Generate events with emotion-based mode switching.

        Args:
            audio_project: Audio project with segments
            video_height: Video height for positioning

        Returns:
            Events string
        """
        events = []
        current_time = 0.0

        for segment in audio_project.segments:
            if self._is_intense_segment(segment):
                # Rapid mode: word-by-word with pastel colors
                segment_events = self._generate_rapid_events(segment, current_time)
            else:
                # Sentence mode: full sentence with white color
                segment_events = self._generate_sentence_events(segment, current_time)
            
            events.extend(segment_events)
            current_time += segment.duration_seconds

        return "\n".join(events)
    
    def _is_intense_segment(self, segment: AudioSegment) -> bool:
        """Check if segment should use rapid mode.

        Args:
            segment: Audio segment

        Returns:
            True if intense (use rapid mode)
        """
        # Check emotion
        if segment.emotion in self.INTENSE_EMOTIONS:
            return True
        
        # Fallback: text analysis (exclamation marks, short punchy text)
        text = segment.get_text()
        if "!" in text or "?!" in text:
            return True
        
        # Short, punchy sentences
        if len(text.split()) <= 5:
            return True
        
        return False
    
    def _generate_rapid_events(self, segment: AudioSegment, offset: float) -> list[str]:
        """Generate rapid word-by-word events with high-impact styling.

        Args:
            segment: Audio segment
            offset: Time offset for this segment

        Returns:
            List of event strings
        """
        events = []
        from gossiptoon.video.text_analyzer import TextAnalyzer, TextStyle

        for ts in segment.timestamps:
            # Use actual audio timestamps for perfect sync
            start_str = format_timestamp_ass(ts.start + offset)
            end_str = format_timestamp_ass(ts.end + offset)

            # Analyze word for style
            style = TextAnalyzer.analyze_word(ts.word)
            
            # Base text with style tags
            tags = TextAnalyzer.get_ass_tags(style)
            
            if style == TextStyle.HIGH_IMPACT:
                # Add random high-impact color
                color = TextAnalyzer.get_high_impact_color()
                tags += f"\\c{color}"
                # Add slight shake for high impact (optional)
                # tags += r"\t(0,200,\fscx110\fscy110)" # Pulse example
            else:
                # Normal words in rapid mode: standard color (White) or Pastel?
                # Ticket says "Normal Subtitles... White text with black outline"
                # User feedback: "white doesn't work... maybe white doesn't need any?"
                # Rely on default style (Style: RapidWord) which should be defined as white
                pass

            # FIX: Use single braces for ASS format (not triple braces which escape to double)
            text = "{" + tags + "}" + ts.word

            events.append(
                f"Dialogue: 0,{start_str},{end_str},RapidWord,,0,0,0,,{text}"
            )

        return events
    
    def _generate_sentence_events(self, segment: AudioSegment, offset: float) -> list[str]:
        """Generate sentence-mode events.

        Args:
            segment: Audio segment
            offset: Time offset for this segment

        Returns:
            List of event strings (typically one)
        """
        if not segment.timestamps:
            return []
        
        # Get full text
        text = segment.get_text()
        
        # Use first and last timestamp
        start_str = format_timestamp_ass(segment.timestamps[0].start + offset)
        end_str = format_timestamp_ass(segment.timestamps[-1].end + offset)
        
        # White/yellow color for sentence mode (no color tag = use style default)
        return [
            f"Dialogue: 0,{start_str},{end_str},SentenceMode,,0,0,0,,{text}"
        ]
