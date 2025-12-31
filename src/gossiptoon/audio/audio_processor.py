"""Audio processing utilities for concatenation and normalization."""

import logging
from pathlib import Path
from typing import Optional

from gossiptoon.core.exceptions import AudioGenerationError

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Utility class for audio processing operations."""

    def __init__(self) -> None:
        """Initialize audio processor."""
        self._pydub_available = self._check_pydub()

    def _check_pydub(self) -> bool:
        """Check if pydub is available.

        Returns:
            True if pydub is available
        """
        try:
            import pydub  # noqa: F401

            return True
        except ImportError:
            logger.warning("pydub not available. Install with: pip install pydub")
            return False

    async def concatenate_audio_files(
        self, audio_paths: list[Path], output_path: Path, crossfade_ms: int = 0
    ) -> Path:
        """Concatenate multiple audio files into one.

        Args:
            audio_paths: List of paths to audio files
            output_path: Path for output file
            crossfade_ms: Crossfade duration in milliseconds

        Returns:
            Path to concatenated audio file

        Raises:
            AudioGenerationError: If concatenation fails
        """
        if not self._pydub_available:
            # Fallback to FFmpeg
            return await self._concatenate_with_ffmpeg(audio_paths, output_path)

        try:
            from pydub import AudioSegment

            logger.info(f"Concatenating {len(audio_paths)} audio files")

            # Load first audio file
            combined = AudioSegment.from_file(audio_paths[0])

            # Append remaining files
            for audio_path in audio_paths[1:]:
                audio = AudioSegment.from_file(audio_path)

                if crossfade_ms > 0:
                    combined = combined.append(audio, crossfade=crossfade_ms)
                else:
                    combined = combined + audio

            # Export combined audio
            output_path.parent.mkdir(parents=True, exist_ok=True)
            combined.export(output_path, format="mp3")

            logger.info(f"Audio concatenated to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Audio concatenation failed: {e}")
            raise AudioGenerationError(f"Failed to concatenate audio: {e}") from e

    async def _concatenate_with_ffmpeg(
        self, audio_paths: list[Path], output_path: Path
    ) -> Path:
        """Concatenate audio files using FFmpeg.

        Args:
            audio_paths: List of paths to audio files
            output_path: Path for output file

        Returns:
            Path to concatenated audio file

        Raises:
            AudioGenerationError: If concatenation fails
        """
        import subprocess
        import tempfile

        try:
            # Create concat file for FFmpeg
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                concat_file = Path(f.name)
                for audio_path in audio_paths:
                    f.write(f"file '{audio_path.absolute()}'\n")

            # Run FFmpeg concat
            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                "-c",
                "copy",
                str(output_path),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Clean up temp file
            concat_file.unlink()

            logger.info(f"Audio concatenated with FFmpeg to {output_path}")
            return output_path

        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg concatenation failed: {e.stderr}")
            raise AudioGenerationError(f"FFmpeg concatenation failed: {e.stderr}") from e
        except Exception as e:
            logger.error(f"Audio concatenation failed: {e}")
            raise AudioGenerationError(f"Failed to concatenate audio: {e}") from e

    async def normalize_audio(
        self, audio_path: Path, output_path: Optional[Path] = None, target_dbfs: float = -20.0
    ) -> Path:
        """Normalize audio volume.

        Args:
            audio_path: Path to input audio file
            output_path: Optional path for output (defaults to overwrite)
            target_dbfs: Target volume in dBFS

        Returns:
            Path to normalized audio file

        Raises:
            AudioGenerationError: If normalization fails
        """
        if output_path is None:
            output_path = audio_path

        if not self._pydub_available:
            logger.warning("Pydub not available, skipping normalization")
            return audio_path

        try:
            from pydub import AudioSegment

            audio = AudioSegment.from_file(audio_path)

            # Calculate normalization
            change_in_dbfs = target_dbfs - audio.dBFS

            # Apply normalization
            normalized = audio.apply_gain(change_in_dbfs)

            # Export
            normalized.export(output_path, format="mp3")

            logger.info(f"Audio normalized: {audio.dBFS:.1f} dBFS -> {target_dbfs:.1f} dBFS")
            return output_path

        except Exception as e:
            logger.error(f"Audio normalization failed: {e}")
            raise AudioGenerationError(f"Failed to normalize audio: {e}") from e

    def get_audio_duration(self, audio_path: Path) -> float:
        """Get duration of audio file.

        Args:
            audio_path: Path to audio file

        Returns:
            Duration in seconds

        Raises:
            AudioGenerationError: If reading fails
        """
        if not self._pydub_available:
            return self._get_duration_with_ffmpeg(audio_path)

        try:
            from pydub import AudioSegment

            audio = AudioSegment.from_file(audio_path)
            duration = len(audio) / 1000.0  # Convert ms to seconds

            return duration

        except Exception as e:
            logger.error(f"Failed to get audio duration: {e}")
            raise AudioGenerationError(f"Failed to get duration: {e}") from e

    def _get_duration_with_ffmpeg(self, audio_path: Path) -> float:
        """Get audio duration using FFmpeg.

        Args:
            audio_path: Path to audio file

        Returns:
            Duration in seconds
        """
        import subprocess

        try:
            cmd = [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(audio_path),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            duration = float(result.stdout.strip())

            return duration

        except Exception as e:
            logger.error(f"FFprobe duration check failed: {e}")
            raise AudioGenerationError(f"Failed to get duration: {e}") from e

    async def change_speed(self, audio_path: Path, speed_factor: float) -> Path:
        """Change audio speed using FFmpeg atempo filter (preserves pitch).

        Args:
            audio_path: Path to input audio
            speed_factor: Speed multiplier (e.g., 1.1 = 10% faster)

        Returns:
            Path to new audio file
        """
        if speed_factor == 1.0:
            return audio_path

        import subprocess

        output_path = audio_path.with_name(f"{audio_path.stem}_speed_{speed_factor}{audio_path.suffix}")
        
        try:
            # chaining atempo filters if speed > 2.0 (atempo limits: 0.5 - 2.0)
            # For our use case (1.1), single filter is fine.
            filter_str = f"atempo={speed_factor}"

            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(audio_path),
                "-filter:a",
                filter_str,
                "-vn",
                str(output_path),
            ]

            logger.info(f"Changing audio speed: {speed_factor}x")
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            return output_path

        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg speed change failed: {e.stderr}")
            raise AudioGenerationError(f"Failed to change audio speed: {e.stderr}") from e
        except Exception as e:
            logger.error(f"Audio speed change failed: {e}")
            raise AudioGenerationError(f"Failed to change audio speed: {e}") from e
