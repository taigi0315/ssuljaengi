"""Video assembler orchestrates FFmpeg rendering.

Coordinates effects, audio sync, and final video assembly.
"""

import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Any, Optional

from gossiptoon.core.config import ConfigManager
from gossiptoon.core.exceptions import VideoAssemblyError
from gossiptoon.models.audio import AudioProject
from gossiptoon.models.video import VideoProject
from gossiptoon.models.visual import VisualProject
from gossiptoon.utils.retry import retry_with_backoff
from gossiptoon.video.effects.captions import CaptionConfig, CaptionEffect
from gossiptoon.video.effects.ken_burns import KenBurnsConfig, KenBurnsEffect
from gossiptoon.video.effects.camera import CameraEffect, CameraEffectConfig
from gossiptoon.video.ffmpeg_builder import FFmpegBuilder, VideoSegment

logger = logging.getLogger(__name__)


class VideoAssembler:
    """Assembles final video from visual and audio assets.

    Coordinates:
    - FFmpeg command building
    - Effect application
    - Audio synchronization
    - Video rendering
    """

    def __init__(self, config: ConfigManager) -> None:
        """Initialize video assembler.

        Args:
            config: Configuration manager
        """
        self.config = config

        self.ffmpeg_builder = FFmpegBuilder(
            fps=config.video.fps,
            output_width=config.video.width,
            output_height=config.video.height,
        )

        logger.info("Video assembler initialized")

    async def assemble_video(
        self,
        visual_project: VisualProject,
        audio_project: AudioProject,
        script: Any,  # Avoid circular import, typed as Any or check if Script is imported
        engagement_project=None,  # Optional EngagementProject
    ) -> VideoProject:
        """Assemble complete video from visual and audio assets.

        Args:
            visual_project: Visual project with images
            audio_project: Audio project with master audio and timestamps
            script: Script object
            engagement_project: Optional engagement hooks to render

        Returns:
            VideoProject with rendered video

        Raises:
            VideoAssemblyError: If assembly fails
        """
        logger.info(f"Assembling video for project: {visual_project.script_id}")

        # Create video segments with effects
        segments = self._create_segments_with_effects(
            visual_project,
            audio_project,
        )

        # Generate caption file if enabled
        subtitle_file = None
        if self.config.video.captions_enabled:
            subtitle_file = await self._generate_captions(
                audio_project,
                visual_project.script_id,
            )

        # Generate engagement overlay if provided
        engagement_overlay_file = None
        if engagement_project:
            from gossiptoon.video.engagement_overlay import EngagementOverlayGenerator
            
            generator = EngagementOverlayGenerator()
            overlay_path = self.config.videos_dir / f"{visual_project.script_id}_engagement.ass"
            
            engagement_overlay_file = generator.generate_ass_file(
                engagement_project=engagement_project,
                script=script,  # Use passed script object
                audio_project=audio_project,
                output_path=overlay_path,
                video_width=self.config.video.width,
                video_height=self.config.video.height,
            )
            logger.info(f"Generated engagement overlay: {engagement_overlay_file}")

        # Build FFmpeg command
        output_file = self.config.videos_dir / f"{visual_project.script_id}.mp4"

        command = self.ffmpeg_builder.build_video_command(
            segments=segments,
            master_audio=audio_project.master_audio_path,
            output_file=output_file,
            subtitles_path=subtitle_file,
            engagement_overlay=engagement_overlay_file,  # NEW
        )

        # Execute FFmpeg
        logger.info("Starting video render...")
        estimated_time = self.ffmpeg_builder.estimate_render_time(segments)
        logger.info(f"Estimated render time: {estimated_time:.1f}s")

        await self._execute_ffmpeg(command.to_list())

        # Build timeline segments
        timeline = self._build_timeline(visual_project, audio_project)

        # Build render config
        from gossiptoon.models.video import RenderConfig

        render_config = RenderConfig(
            resolution=self.config.video.resolution,
            fps=self.config.video.fps,
            video_codec=self.config.video.video_codec,
            audio_codec=self.config.video.audio_codec,
            bitrate=self.config.video.bitrate,
            preset=self.config.video.preset,
        )

        # Create video project
        video_project = VideoProject(
            project_id=visual_project.script_id,
            script_id=visual_project.script_id,
            timeline=timeline,
            render_config=render_config,
            output_path=output_file,
            metadata={
                "effects_applied": [
                    "ken_burns" if self.config.video.ken_burns_enabled else None,
                    "captions" if self.config.video.captions_enabled else None,
                ],
                "ffmpeg_command": command.to_string(),
                "audio_path": str(audio_project.master_audio_path),
                "total_duration": audio_project.total_duration,
            },
        )

        logger.info(f"Video assembly complete: {output_file}")

        return video_project

    def _create_segments_with_effects(
        self,
        visual_project: VisualProject,
        audio_project: AudioProject,
    ) -> list[VideoSegment]:
        """Create video segments with effects applied.

        Args:
            visual_project: Visual project
            audio_project: Audio project

        Returns:
            List of video segments
        """
        segments = []

        total_audio_time = 0.0
        total_frames = 0
        fps = self.config.video.fps
        
        for i, asset in enumerate(visual_project.assets):
            # Get raw audio duration
            audio_duration = self._get_scene_duration(
                asset.scene_id,
                audio_project,
            )
            
            # Frame-Accurate Duration Calculation (DDA)
            # 1. Update ideal audio timeline
            total_audio_time += audio_duration
            
            try:
                # 2. Calculate target frame count for this timestamp
                target_total_frames = round(total_audio_time * fps)
                
                # 3. Determine frames for THIS segment
                segment_frames = target_total_frames - total_frames
                
                # 4. Calculate precise duration for FFmpeg
                # This ensures video duration exactly matches the frame count FFmpeg will generate
                duration = segment_frames / fps
            except TypeError as e:
                logger.error(f"TypeError during duration calc in segment {i}: {e}")
                logger.error(f"total_audio_time: {type(total_audio_time)} = {total_audio_time}")
                logger.error(f"fps: {type(fps)} = {fps}")
                logger.error(f"audio_duration: {type(audio_duration)} = {audio_duration}")
                raise
            
            # Update state
            total_frames = target_total_frames
            
            logger.info(
                f"Segment {i}: Audio={audio_duration:.4f}s, "
                f"Video={duration:.4f}s ({segment_frames} frames), "
                f"Drift={total_frames/fps - total_audio_time:.4f}s"
            )

            # Create effects for this segment
            effects = []

            # 1. AI Camera Effects (Priority)
            if self.config.video.use_ai_camera_effects and asset.camera_effect:
                camera_effect = CameraEffect(CameraEffectConfig(
                    enabled=True,
                    effect_type=asset.camera_effect,
                    intensity=0.3
                ))
                effects.append(camera_effect)
            
            # 2. Generic Ken Burns (Fallback)
            elif self.config.video.ken_burns_enabled:
                ken_burns_effect = self._create_ken_burns_effect(asset.scene_id)
                effects.append(ken_burns_effect)

            # Note: Captions are applied globally via subtitle file, not per-segment

            segment = VideoSegment(
                image_path=asset.image_path,
                duration=duration,
                effects=effects,
            )

            segments.append(segment)
            
        final_video_duration = total_frames / fps
        logger.info(f"Total Video Duration: {final_video_duration:.4f}s ({total_frames} frames)")
        logger.info(f"Total Audio Duration: {total_audio_time:.4f}s")
        diff = final_video_duration - total_audio_time
        if abs(diff) > (1.0 / fps):
             logger.warning(f"Final AV Sync Diff: {diff:.4f}s (Should be < 1 frame)")

        return segments

    def _create_ken_burns_effect(self, scene_id: str) -> KenBurnsEffect:
        """Create Ken Burns effect for a scene.

        Args:
            scene_id: Scene identifier

        Returns:
            Configured Ken Burns effect
        """
        # Load config or use defaults
        config = KenBurnsConfig(
            enabled=True,
            zoom_start=1.0,
            zoom_end=1.2,
            pan_direction="up",
            pan_intensity=0.15,
            ease_function="ease-in-out",
            output_width=self.config.video.width,
            output_height=self.config.video.height,
        )

        return KenBurnsEffect(config)

    async def _generate_captions(
        self,
        audio_project: AudioProject,
        script_id: str,
    ) -> Optional[Path]:
        """Generate caption file from audio timestamps.

        Args:
            audio_project: Audio project with word timestamps
            script_id: Script identifier

        Returns:
            Path to subtitle file
        """
        logger.info("Generating captions...")

        # Import locally to avoid circular dependencies
        from gossiptoon.video.subtitles import SubtitleGenerator

        # Create generator
        generator = SubtitleGenerator(
            font_name="Arial",
            rapid_font_size=80,
            sentence_font_size=64,
        )

        # Generate subtitle file
        subtitle_file = self.config.videos_dir / f"{script_id}_captions.ass"

        generator.generate_ass_file(
            audio_project=audio_project,
            output_path=subtitle_file,
            video_width=self.config.video.width,
            video_height=self.config.video.height,
        )

        logger.info(f"Captions generated: {subtitle_file}")

        return subtitle_file

    def _build_timeline(
        self,
        visual_project: VisualProject,
        audio_project: AudioProject,
    ) -> list:
        """Build timeline segments from visual and audio projects.

        Args:
            visual_project: Visual project
            audio_project: Audio project

        Returns:
            List of TimelineSegment objects
        """
        from gossiptoon.models.video import TimelineSegment

        timeline = []
        current_time = 0.0

        for asset in visual_project.assets:
            # Get matching audio segment
            audio_segment = None
            for seg in audio_project.segments:
                if seg.scene_id == asset.scene_id:
                    audio_segment = seg
                    break

            if audio_segment is None:
                logger.warning(f"No audio segment found for scene {asset.scene_id}, skipping")
                continue

            duration = audio_segment.duration_seconds

            # Create timeline segment
            segment = TimelineSegment(
                scene_id=asset.scene_id,
                start_time=current_time,
                end_time=current_time + duration,
                visual_asset_path=asset.image_path,
                audio_segment_path=audio_segment.file_path,
                effects=[],  # Effects are applied globally via FFmpeg, not per-segment in this model
            )

            timeline.append(segment)
            current_time += duration

        return timeline

    def _get_scene_duration(
        self,
        scene_id: str,
        audio_project: AudioProject,
    ) -> float:
        """Get scene duration from audio project.

        Args:
            scene_id: Scene identifier
            audio_project: Audio project

        Returns:
            Duration in seconds
        """
        # Find matching audio segment
        for segment in audio_project.segments:
            if segment.scene_id == scene_id:
                return segment.duration_seconds

        # Fallback to default
        logger.warning(f"No audio segment found for scene {scene_id}, using default duration")
        return 5.0

    @retry_with_backoff(max_retries=2, exceptions=(VideoAssemblyError,))
    async def _execute_ffmpeg(self, command: list[str]) -> None:
        """Execute FFmpeg command.

        Args:
            command: FFmpeg command as list

        Raises:
            VideoAssemblyError: If FFmpeg fails
        """
        try:
            logger.debug(f"Executing: {' '.join(command)}")

            # Run FFmpeg
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"FFmpeg failed: {error_msg}")
                raise VideoAssemblyError(f"FFmpeg failed: {error_msg}")

            logger.info("FFmpeg completed successfully")

        except Exception as e:
            logger.error(f"FFmpeg execution failed: {e}")
            raise VideoAssemblyError(f"FFmpeg execution failed: {e}") from e

    def validate_ffmpeg_installation(self) -> bool:
        """Validate FFmpeg is installed and accessible.

        Returns:
            True if FFmpeg is available

        Raises:
            VideoAssemblyError: If FFmpeg is not found
        """
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                version_line = result.stdout.split("\n")[0]
                logger.info(f"FFmpeg found: {version_line}")
                return True
            else:
                raise VideoAssemblyError("FFmpeg command failed")

        except FileNotFoundError:
            raise VideoAssemblyError(
                "FFmpeg not found. Please install FFmpeg: https://ffmpeg.org/download.html"
            )
        except Exception as e:
            raise VideoAssemblyError(f"Failed to validate FFmpeg: {e}") from e

    async def create_preview(
        self,
        visual_project: VisualProject,
        audio_project: AudioProject,
        duration_limit: float = 10.0,
    ) -> Path:
        """Create quick preview video (first N seconds).

        Args:
            visual_project: Visual project
            audio_project: Audio project
            duration_limit: Maximum duration for preview

        Returns:
            Path to preview video
        """
        logger.info(f"Creating {duration_limit}s preview...")

        # Take first few segments up to duration limit
        preview_segments = []
        total_duration = 0.0

        for asset in visual_project.assets:
            if total_duration >= duration_limit:
                break

            duration = min(
                self._get_scene_duration(asset.scene_id, audio_project),
                duration_limit - total_duration,
            )

            segment = VideoSegment(
                image_path=asset.image_path,
                duration=duration,
                effects=[],  # No effects for quick preview
            )

            preview_segments.append(segment)
            total_duration += duration

        # Build and execute
        output_file = self.config.videos_dir / f"{visual_project.script_id}_preview.mp4"

        command = self.ffmpeg_builder.build_video_command(
            segments=preview_segments,
            master_audio=audio_project.master_audio_path,
            output_file=output_file,
            preset="ultrafast",  # Fast encoding
            crf=28,  # Lower quality
        )

        await self._execute_ffmpeg(command.to_list())

        logger.info(f"Preview created: {output_file}")

        return output_file
