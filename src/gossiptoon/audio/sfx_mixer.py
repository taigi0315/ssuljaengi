"""Audio SFX mixer for overlaying sound effects on narration.

Handles mixing SFX audio files with master narration at specific timestamps.
"""

import logging
from pathlib import Path
from typing import Optional

from pydub import AudioSegment

logger = logging.getLogger(__name__)


class AudioSFXMixer:
    """Mixes SFX sounds with narration audio."""

    def __init__(self, sfx_volume: float = 0.5):
        """Initialize SFX mixer.

        Args:
            sfx_volume: Relative volume for SFX (0.0-1.0, default 0.5 = 50%)
        """
        self.sfx_volume = sfx_volume

    def overlay_sfx(
        self,
        master_audio_path: Path,
        sfx_audio_path: Path,
        offset_seconds: float,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Overlay SFX on master audio at specific timestamp.

        Args:
            master_audio_path: Path to master/narration audio file
            sfx_audio_path: Path to SFX audio file
            offset_seconds: Time offset in seconds where SFX should start
            output_path: Optional output path (default: master_audio_path with _sfx suffix)

        Returns:
            Path to mixed audio file
        """
        logger.info(
            f"Overlaying SFX '{sfx_audio_path.name}' at {offset_seconds}s on {master_audio_path.name}"
        )

        # Load master audio
        master = AudioSegment.from_file(str(master_audio_path))

        # Load SFX audio
        sfx = AudioSegment.from_file(str(sfx_audio_path))

        # Adjust SFX volume
        # pydub uses dB scale: -20dB = 10% volume, 0dB = 100% volume
        # For 70% volume: approximately -3dB
        volume_adjustment_db = 20 * (self.sfx_volume - 1)  # At 0.7 → -6dB
        sfx = sfx + volume_adjustment_db

        # Overlay at offset (pydub uses milliseconds)
        offset_ms = int(offset_seconds * 1000)
        mixed = master.overlay(sfx, position=offset_ms)

        # Determine output path
        if output_path is None:
            output_path = master_audio_path.with_name(
                master_audio_path.stem + "_sfx" + master_audio_path.suffix
            )

        # Export mixed audio
        mixed.export(str(output_path), format="mp3")

        logger.info(f"Mixed audio saved to: {output_path}")
        return output_path

    def overlay_multiple_sfx(
        self,
        master_audio_path: Path,
        sfx_list: list[tuple[Path, float]],  # List of (sfx_path, offset_seconds)
        output_path: Optional[Path] = None,
    ) -> Path:
        """Overlay multiple SFX sounds on master audio.

        Args:
            master_audio_path: Path to master/narration audio file
            sfx_list: List of tuples (sfx_audio_path, offset_seconds)
            output_path: Optional output path

        Returns:
            Path to mixed audio file
        """
        logger.info(f"Overlaying {len(sfx_list)} SFX sounds on {master_audio_path.name}")

        # Load master audio
        mixed = AudioSegment.from_file(str(master_audio_path))

        # Overlay each SFX
        for sfx_path, offset_seconds in sfx_list:
            logger.info(f"  - {sfx_path.name} at {offset_seconds}s")

            # Load SFX
            sfx = AudioSegment.from_file(str(sfx_path))

            # Adjust volume
            volume_adjustment_db = 20 * (self.sfx_volume - 1)
            sfx = sfx + volume_adjustment_db

            # Overlay
            offset_ms = int(offset_seconds * 1000)
            mixed = mixed.overlay(sfx, position=offset_ms)

        # Determine output path
        if output_path is None:
            output_path = master_audio_path.with_name(
                master_audio_path.stem + "_sfx" + master_audio_path.suffix
            )

        # Export
        mixed.export(str(output_path), format="mp3")

        logger.info(f"Mixed audio with {len(sfx_list)} SFX saved to: {output_path}")
        return output_path
