"""FFmpeg command builder for video assembly.

Builds clean, readable FFmpeg commands with composable effects.
Handles complex filter graphs while keeping code maintainable.
"""

import logging
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

from gossiptoon.video.effects.base import Effect

logger = logging.getLogger(__name__)


class VideoSegment(BaseModel):
    """Represents a single video segment (image + duration).

    Each segment corresponds to one scene.
    """

    image_path: Path = Field(..., description="Path to image file")
    duration: float = Field(..., ge=0.1, description="Duration in seconds")
    audio_path: Optional[Path] = Field(None, description="Optional audio for this segment")
    effects: list[Effect] = Field(default_factory=list, description="Effects to apply")

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True  # Allow Effect objects


class FFmpegCommand(BaseModel):
    """Represents a complete FFmpeg command.

    Makes command construction readable and debuggable.
    """

    inputs: list[str] = Field(default_factory=list, description="Input file arguments")
    filter_complex: Optional[str] = Field(None, description="Filter complex graph")
    maps: list[str] = Field(default_factory=list, description="Stream mapping")
    output_options: list[str] = Field(default_factory=list, description="Output options")
    output_file: Path = Field(..., description="Output file path")

    def to_list(self) -> list[str]:
        """Convert to FFmpeg command list.

        Returns:
            List of command arguments
        """
        cmd = ["ffmpeg", "-y"]  # -y to overwrite

        # Add inputs
        cmd.extend(self.inputs)

        # Add filter complex
        if self.filter_complex:
            cmd.extend(["-filter_complex", self.filter_complex])

        # Add maps
        for map_arg in self.maps:
            cmd.extend(["-map", map_arg])

        # Add output options
        cmd.extend(self.output_options)

        # Add output file
        cmd.append(str(self.output_file))

        return cmd

    def to_string(self) -> str:
        """Convert to readable command string.

        Returns:
            Command string (for logging/debugging)
        """
        return " ".join(self.to_list())

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class FFmpegBuilder:
    """Builder for FFmpeg commands with effect composition.

    Makes complex FFmpeg commands readable and maintainable.
    """

    def __init__(
        self,
        fps: int = 30,
        output_width: int = 1080,
        output_height: int = 1920,
    ) -> None:
        """Initialize FFmpeg builder.

        Args:
            fps: Frames per second
            output_width: Output video width
            output_height: Output video height
        """
        self.fps = fps
        self.output_width = output_width
        self.output_height = output_height

    def build_video_command(
        self,
        segments: list[VideoSegment],
        master_audio: Path,
        output_file: Path,
        **options: Any,
    ) -> FFmpegCommand:
        """Build complete video assembly command.

        Args:
            segments: List of video segments
            master_audio: Path to master audio file
            output_file: Output video file path
            **options: Additional options (codec, bitrate, etc.)

        Returns:
            FFmpegCommand ready to execute
        """
        logger.info(f"Building FFmpeg command for {len(segments)} segments")

        # Build inputs
        inputs = self._build_inputs(segments, master_audio)

        # Build filter complex
        filter_complex = self._build_filter_complex(segments, **options)

        # Build maps
        maps = ["[outv]",  # Video output from filter
                f"{len(segments)}:a"]  # Audio from master audio file

        # Build output options
        output_options = self._build_output_options(**options)

        command = FFmpegCommand(
            inputs=inputs,
            filter_complex=filter_complex,
            maps=maps,
            output_options=output_options,
            output_file=output_file,
        )

        logger.info(f"FFmpeg command: {command.to_string()}")

        return command

    def _build_inputs(
        self,
        segments: list[VideoSegment],
        master_audio: Path,
    ) -> list[str]:
        """Build input file arguments.

        Args:
            segments: Video segments
            master_audio: Master audio file

        Returns:
            List of input arguments
        """
        inputs = []

        for segment in segments:
            # Loop image for duration
            inputs.extend([
                "-loop", "1",
                "-framerate", str(self.fps),
                "-t", str(segment.duration),
                "-i", str(segment.image_path),
            ])

        # Add master audio
        inputs.extend(["-i", str(master_audio)])

        return inputs

    def _build_filter_complex(self, segments: list[VideoSegment], **options: Any) -> str:
        """Build filter complex graph.

        This is where effects are applied and segments are concatenated.

        Args:
            segments: Video segments with effects

        Returns:
            Filter complex string
        """
        filter_parts = []

        # Process each segment with effects
        for i, segment in enumerate(segments):
            input_label = f"[{i}:v]"
            output_label = f"[v{i}]"

            if segment.effects:
                # Apply effects to this segment
                # Use strict intermediate labels to enforce property standardization
                effect_out_label = f"[tmp_eff_{i}]"
                
                segment_filter = self._apply_effects(
                    input_label,
                    effect_out_label,
                    segment.effects,
                    unique_id=str(i),
                    duration=segment.duration,
                    fps=self.fps,
                )
                
                # Log effect timing
                logger.info(f"Applied effect to segment {i}: Duration={segment.duration:.3f}s, FPS={self.fps}")
                filter_parts.append(segment_filter)
                
                # Enforce consistent properties + resolution (Scale & Pad)
                # This ensures that even if an effect (like static CameraEffect) didn't scale, we force it here.
                standardize_input = effect_out_label
            else:
                # No effects - input comes directly from source
                standardize_input = input_label

            # Universal standardization filter (Trim + Scale + Pad + SAR + Format + FPS)
            # 1. trim: Enforce EXACT duration (prevents zoompan drift)
            # 2. scale/pad: Enforce resolution (fixes mismatch)
            # 3. setsar/format/fps: Enforce encoding properties
            standardize_filter = (
                f"{standardize_input}"
                f"trim=duration={segment.duration},"
                f"scale={self.output_width}:{self.output_height}:"
                f"force_original_aspect_ratio=decrease,"
                f"pad={self.output_width}:{self.output_height}:-1:-1:color=black,"
                f"setsar=1,"
                f"format=yuv420p,"
                f"fps={self.fps}"
                f"{output_label}"
            )
            filter_parts.append(standardize_filter)

        # Concatenate all segments
        concat_inputs = "".join(f"[v{i}]" for i in range(len(segments)))
        
        # If subtitles provided, concat output is intermediate
        final_video_label = "[outv]" if not options.get("subtitles_path") else "[v_concat]"
        
        concat_filter = (
            f"{concat_inputs}concat=n={len(segments)}:v=1:a=0{final_video_label}"
        )
        filter_parts.append(concat_filter)

        # Apply subtitles if provided
        if options.get("subtitles_path"):
            # Escape path for FFmpeg filter
            sub_path = str(options["subtitles_path"]).replace(":", "\\:").replace("'", "\\'")
            subtitle_filter = f"[v_concat]subtitles='{sub_path}'[outv]"
            filter_parts.append(subtitle_filter)

        # Join all filters
        filter_complex = ";".join(filter_parts)

        return filter_complex

    def _apply_effects(
        self,
        input_label: str,
        output_label: str,
        effects: list[Effect],
        unique_id: str = "0",
        **context: Any,
    ) -> str:
        """Apply effects to a segment.

        Args:
            input_label: Input stream label
            output_label: Output stream label
            effects: List of effects to apply
            unique_id: Unique identifier for this chain (to prevent label collisions)
            **context: Context for effects (duration, fps, etc.)

        Returns:
            Filter string with effects applied
        """
        if not effects:
            return f"{input_label}copy{output_label}"

        # Chain effects
        current_input = input_label
        effect_filters = []

        for i, effect in enumerate(effects):
            if not effect.is_enabled():
                continue

            # Last effect uses final output label
            if i == len(effects) - 1:
                current_output = output_label
            else:
                current_output = f"[tmp_{unique_id}_{i}]"

            effect_filter = effect.get_filter_string(
                current_input,
                current_output,
                **context,
            )
            effect_filters.append(effect_filter)
            current_input = current_output

        return ";".join(effect_filters)

    def _build_output_options(self, **options: Any) -> list[str]:
        """Build output encoding options.

        Args:
            **options: Custom options

        Returns:
            List of output option arguments
        """
        # Default high-quality options for YouTube Shorts
        output_opts = [
            "-c:v", options.get("video_codec", "libx264"),
            "-preset", options.get("preset", "medium"),
            "-crf", str(options.get("crf", 23)),
            "-pix_fmt", "yuv420p",
            "-c:a", options.get("audio_codec", "aac"),
            "-b:a", options.get("audio_bitrate", "192k"),
            "-ar", str(options.get("sample_rate", 44100)),
            "-r", str(self.fps),
            "-shortest",  # Stop encoding when the shortest stream (audio) ends
        ]

        # Keys that are handled specially and should NOT become FFmpeg flags
        excluded_keys = [
            "video_codec", "preset", "crf", "audio_codec", 
            "audio_bitrate", "sample_rate", "subtitle_file", "subtitles_path"
        ]

        # Add custom options
        for key, value in options.items():
            if key not in excluded_keys:
                output_opts.extend([f"-{key}", str(value)])

        return output_opts

    def build_simple_concat_command(
        self,
        image_files: list[Path],
        durations: list[float],
        audio_file: Path,
        output_file: Path,
    ) -> FFmpegCommand:
        """Build simple concatenation command without effects.

        Useful for quick previews.

        Args:
            image_files: List of image files
            durations: Duration for each image
            audio_file: Audio file
            output_file: Output file

        Returns:
            Simple FFmpeg command
        """
        segments = [
            VideoSegment(image_path=img, duration=dur)
            for img, dur in zip(image_files, durations)
        ]

        return self.build_video_command(
            segments=segments,
            master_audio=audio_file,
            output_file=output_file,
        )

    def estimate_render_time(self, segments: list[VideoSegment]) -> float:
        """Estimate render time based on segments and effects.

        Args:
            segments: Video segments

        Returns:
            Estimated render time in seconds
        """
        total_duration = sum(s.duration for s in segments)

        # Base render time (roughly 2x real-time for medium preset)
        base_time = total_duration * 2

        # Add overhead for effects
        effect_overhead = 0
        for segment in segments:
            if segment.effects:
                # Effects add ~1.5x overhead
                effect_overhead += segment.duration * 1.5

        estimated = base_time + effect_overhead

        return estimated
