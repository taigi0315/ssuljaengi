"""Audio generator orchestrator - combines TTS and timestamp extraction."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from gossiptoon.audio.audio_processor import AudioProcessor
from gossiptoon.audio.base import TTSClient
from gossiptoon.audio.elevenlabs_client import ElevenLabsClient
from gossiptoon.audio.google_tts_client import GoogleTTSClient
from gossiptoon.audio.whisper import WhisperTimestampExtractor
from gossiptoon.core.config import ConfigManager
from gossiptoon.core.exceptions import AudioGenerationError
from gossiptoon.models.audio import AudioProject, AudioSegment
from gossiptoon.models.script import Script

logger = logging.getLogger(__name__)


class AudioGenerator:
    """Main audio generation orchestrator.

    Combines TTS generation and timestamp extraction to create
    the audio-first master clock for the video pipeline.
    """

    def __init__(
        self,
        config: ConfigManager,
        tts_client: Optional[TTSClient] = None,
    ) -> None:
        """Initialize audio generator.

        Args:
            config: Configuration manager
            tts_client: Optional TTS client (auto-selected based on config if not provided)
        """
        self.config = config

        # Auto-select TTS client based on configuration
        if tts_client:
            self.tts_client = tts_client
        elif config.audio.tts_provider == "google":
            logger.info("Using Google TTS 2.5 Flash")
            self.tts_client = GoogleTTSClient(
                api_key=config.api.google_api_key,
                model=config.audio.google_tts_model,
                default_voice=config.audio.google_tts_voice,
            )
        else:
            logger.info("Using ElevenLabs TTS")
            self.tts_client = ElevenLabsClient(api_key=config.api.elevenlabs_api_key)

        self.whisper = WhisperTimestampExtractor(model_name=config.audio.whisper_model)

        self.processor = AudioProcessor()

    async def generate_audio_project(
        self,
        script: Script,
        voice_id: Optional[str] = None,
    ) -> AudioProject:
        """Generate complete audio project for script.

        This is the CRITICAL PATH that creates the master clock.

        Args:
            script: Script to generate audio for
            voice_id: Optional voice ID (uses default if not provided)

        Returns:
            AudioProject with all segments and timestamps

        Raises:
            AudioGenerationError: If generation fails
        """
        if voice_id is None:
            voice_id = self.config.audio.default_voice_id

        logger.info(f"Generating audio project for script: {script.script_id}")
        logger.info(f"Voice: {voice_id}")

        try:
            # Generate audio for each scene
            segments = []
            for scene in script.get_all_scenes():
                segment = await self._generate_scene_audio(scene, voice_id)
                segments.append(segment)

            # Concatenate all segments into master audio
            master_audio_path = await self._create_master_audio(segments, script.script_id)

            # Calculate total duration
            total_duration = sum(seg.duration_seconds for seg in segments)

            # Create audio project
            audio_project = AudioProject(
                script_id=script.script_id,
                segments=segments,
                total_duration=total_duration,
                master_audio_path=master_audio_path,
                voice_id=voice_id,
            )

            # Save audio project
            self._save_audio_project(audio_project)

            logger.info(
                f"Audio project complete: {len(segments)} segments, {total_duration:.1f}s total"
            )

            return audio_project

        except Exception as e:
            logger.error(f"Audio project generation failed: {e}")
            raise AudioGenerationError(f"Failed to generate audio project: {e}") from e

    async def _generate_scene_audio(
        self,
        scene: any,  # Scene from script
        voice_id: str,
    ) -> AudioSegment:
        """Generate audio for a single scene.

        Args:
            scene: Scene object from script
            voice_id: Voice identifier

        Returns:
            AudioSegment with timestamps
        """
        logger.info(f"Generating audio for scene: {scene.scene_id}")

        # Generate speech with TTS
        output_path = self.config.audio_dir / f"{scene.scene_id}.mp3"

        audio_path = await self.tts_client.generate_speech(
            text=scene.narration,
            voice_id=voice_id,
            emotion=scene.emotion,
            output_path=output_path,
        )

        # Get actual audio duration
        duration = self.processor.get_audio_duration(audio_path)

        # Extract word-level timestamps
        logger.info(f"Extracting timestamps for scene: {scene.scene_id}")
        timestamps = await self.whisper.extract_timestamps(audio_path)

        # Create audio segment
        segment = AudioSegment(
            scene_id=scene.scene_id,
            file_path=audio_path,
            duration_seconds=duration,
            emotion=scene.emotion,
            voice_id=voice_id,
            timestamps=timestamps,
        )

        logger.info(f"Scene audio complete: {duration:.1f}s, {len(timestamps)} words")

        return segment

    async def _create_master_audio(
        self,
        segments: list[AudioSegment],
        script_id: str,
    ) -> Path:
        """Concatenate all scene audio into master file.

        Args:
            segments: List of audio segments
            script_id: Script identifier

        Returns:
            Path to master audio file
        """
        logger.info(f"Creating master audio from {len(segments)} segments")

        audio_paths = [seg.file_path for seg in segments]
        output_path = self.config.audio_dir / f"{script_id}_master.mp3"

        # Concatenate audio files
        master_path = await self.processor.concatenate_audio_files(
            audio_paths=audio_paths,
            output_path=output_path,
            crossfade_ms=100,  # Small crossfade for smooth transitions
        )

        # Apply speed factor if needed (Dynamic Pacing)
        if self.config.audio.speed_factor != 1.0:
            logger.info(f"Applying speed factor: {self.config.audio.speed_factor}x")
            master_path = await self.processor.change_speed(
                audio_path=master_path,
                speed_factor=self.config.audio.speed_factor,
            )

        # Normalize volume
        await self.processor.normalize_audio(
            audio_path=master_path,
            target_dbfs=-20.0,
        )

        logger.info(f"Master audio created: {master_path}")

        return master_path

    def _save_audio_project(self, audio_project: AudioProject) -> None:
        """Save audio project to disk.

        Args:
            audio_project: Audio project to save
        """
        output_path = self.config.audio_dir / f"{audio_project.script_id}_project.json"

        with open(output_path, "w") as f:
            json.dump(
                audio_project.model_dump(mode="json"),
                f,
                indent=2,
                default=str,
            )

        logger.info(f"Audio project saved to {output_path}")

    async def regenerate_scene_audio(
        self,
        audio_project: AudioProject,
        scene_id: str,
        new_narration: str,
        voice_id: Optional[str] = None,
    ) -> AudioProject:
        """Regenerate audio for a specific scene (useful for revisions).

        Args:
            audio_project: Existing audio project
            scene_id: Scene to regenerate
            new_narration: New narration text
            voice_id: Optional voice ID

        Returns:
            Updated audio project
        """
        if voice_id is None:
            voice_id = audio_project.voice_id

        logger.info(f"Regenerating audio for scene: {scene_id}")

        # Find and replace the segment
        for i, segment in enumerate(audio_project.segments):
            if segment.scene_id == scene_id:
                # Generate new audio
                output_path = self.config.audio_dir / f"{scene_id}_v2.mp3"

                audio_path = await self.tts_client.generate_speech(
                    text=new_narration,
                    voice_id=voice_id,
                    emotion=segment.emotion,
                    output_path=output_path,
                )

                # Extract timestamps
                timestamps = await self.whisper.extract_timestamps(audio_path)

                # Get duration
                duration = self.processor.get_audio_duration(audio_path)

                # Create new segment
                new_segment = AudioSegment(
                    scene_id=scene_id,
                    file_path=audio_path,
                    duration_seconds=duration,
                    emotion=segment.emotion,
                    voice_id=voice_id,
                    timestamps=timestamps,
                )

                # Replace old segment
                audio_project.segments[i] = new_segment

                # Recalculate total duration
                audio_project.total_duration = sum(
                    seg.duration_seconds for seg in audio_project.segments
                )

                # Recreate master audio
                audio_project.master_audio_path = await self._create_master_audio(
                    audio_project.segments,
                    audio_project.script_id,
                )

                # Save updated project
                self._save_audio_project(audio_project)

                logger.info(f"Scene {scene_id} regenerated successfully")
                return audio_project

        raise AudioGenerationError(f"Scene {scene_id} not found in audio project")
