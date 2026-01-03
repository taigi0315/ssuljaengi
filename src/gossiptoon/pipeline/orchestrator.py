"""Pipeline orchestrator for end-to-end video generation.

Coordinates: Story → Script → Audio → Visual → Video
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from gossiptoon.agents.engagement_writer import EngagementWriter
from gossiptoon.agents.scene_structurer import SceneStructurerAgent
from gossiptoon.agents.script_evaluator import ScriptEvaluator
from gossiptoon.agents.script_writer import ScriptWriterAgent
from gossiptoon.agents.story_finder import StoryFinderAgent
from gossiptoon.agents.visual_detailer import VisualDetailerAgent
from gossiptoon.audio.generator import AudioGenerator
from gossiptoon.core.config import ConfigManager
from gossiptoon.core.exceptions import GossipToonException
from gossiptoon.models.audio import AudioProject
from gossiptoon.models.script import Script
from gossiptoon.models.story import Story
from gossiptoon.models.video import VideoProject
from gossiptoon.models.visual import VisualProject
from gossiptoon.pipeline.checkpoint import CheckpointManager, PipelineStage
from gossiptoon.video.assembler import VideoAssembler
from gossiptoon.visual.director import VisualDirector

logger = logging.getLogger(__name__)


class PipelineResult:
    """Result from pipeline execution."""

    def __init__(
        self,
        project_id: str,
        success: bool,
        video_project: Optional[VideoProject] = None,
        error: Optional[str] = None,
        completed_stages: Optional[list[PipelineStage]] = None,
    ):
        """Initialize pipeline result.

        Args:
            project_id: Project identifier
            success: Whether pipeline succeeded
            video_project: Final video project (if successful)
            error: Error message (if failed)
            completed_stages: List of completed stages
        """
        self.project_id = project_id
        self.success = success
        self.video_project = video_project
        self.error = error
        self.completed_stages = completed_stages or []
        self.timestamp = datetime.now()

    def __repr__(self) -> str:
        """String representation."""
        status = "SUCCESS" if self.success else "FAILED"
        return f"PipelineResult({self.project_id}, {status})"


class PipelineOrchestrator:
    """Orchestrates complete video generation pipeline.

    Pipeline stages:
    1. Story Finding - Discover viral Reddit content
    2. Script Writing - Generate five-act narrative
    3. Audio Generation - TTS with emotion + timestamps
    4. Visual Generation - 9:16 images with character consistency
    5. Video Assembly - FFmpeg rendering with effects

    Features:
    - Checkpoint recovery (resume from any stage)
    - Progress tracking
    - Error handling with retry
    - Validation before execution
    """

    def __init__(self, config: ConfigManager) -> None:
        """Initialize pipeline orchestrator.

        Args:
            config: Configuration manager
        """
        self.config = config

        # Initialize components
        self.story_finder = StoryFinderAgent(config)

        # NEW 3-AGENT SCRIPT GENERATION WORKFLOW
        self.scene_structurer = SceneStructurerAgent(config)
        self.script_writer = ScriptWriterAgent(config)
        self.script_evaluator = ScriptEvaluator(config)
        self.visual_detailer = VisualDetailerAgent(config)

        self.engagement_writer = EngagementWriter(api_key=config.api.google_api_key)
        self.audio_generator = AudioGenerator(config)
        self.visual_director = VisualDirector(config)
        self.video_assembler = VideoAssembler(config)

        # Checkpoint manager
        self.checkpoint_manager = CheckpointManager(config.checkpoints_dir)

        # Use new 3-agent workflow by default
        self.use_new_workflow = True

        logger.info("Pipeline orchestrator initialized (3-AGENT WORKFLOW)")

    async def run(
        self,
        story_url: Optional[str] = None,
        project_id: Optional[str] = None,
        resume: bool = False,
    ) -> PipelineResult:
        """Run complete pipeline.

        Args:
            story_url: Reddit story URL (for new run)
            project_id: Project ID (for resume)
            resume: Whether to resume from checkpoint

        Returns:
            Pipeline result

        Raises:
            GossipToonException: If pipeline fails
        """
        # Determine project ID
        if resume:
            if not project_id:
                raise GossipToonException("project_id required for resume")
            
            # Set context before checking for checkpoint
            self.config.set_job_context(project_id)
            # Re-init checkpoint manager with new path
            # Re-init checkpoint manager with new path
            # Re-init checkpoint manager with new path
            self.checkpoint_manager = CheckpointManager(self.config.checkpoints_dir)
            print(f"DEBUG: Checking for checkpoint in: {self.config.checkpoints_dir}")
            
            if not self.checkpoint_manager.checkpoint_exists(project_id):
                path = self.checkpoint_manager._get_checkpoint_path(project_id)
                print(f"DEBUG: Checkpoint not found at: {path}")
                print(f"DEBUG: File exists? {path.exists()}")
                raise GossipToonException(f"No checkpoint found for project: {project_id} in {self.config.checkpoints_dir}")
        else:
            if not story_url:
                raise GossipToonException("story_url required for new run")
            project_id = self._generate_project_id()
            
            # Set context for new run
            self.config.set_job_context(project_id)
            # Re-init checkpoint manager with new path
            self.checkpoint_manager = CheckpointManager(self.config.checkpoints_dir)

        logger.info(f"Starting pipeline: {project_id} (resume={resume})")

        completed_stages = []
        video_project = None

        try:
            # Resume from checkpoint or start fresh
            if resume:
                checkpoint = self.checkpoint_manager.load_checkpoint(project_id)
                start_stage = checkpoint.current_stage
                logger.info(f"Resuming from stage: {start_stage.value}")


                # Load cached data from checkpoint
                story = self._load_story_from_checkpoint(checkpoint) if checkpoint.story_data else None
                script = self._load_script_from_checkpoint(checkpoint) if checkpoint.script_data else None
                audio_project = (
                    self._load_audio_from_checkpoint(checkpoint) if checkpoint.audio_data else None
                )
                visual_project = (
                    self._load_visual_from_checkpoint(checkpoint) if checkpoint.visual_data else None
                )
            else:
                start_stage = PipelineStage.INITIALIZED
                story = None
                script = None
                audio_project = None
                visual_project = None

            # Stage 1: Story Finding
            if self._should_run_stage(start_stage, PipelineStage.STORY_FOUND):
                logger.info("Stage 1: Finding story...")
                story = await self._run_story_finder(story_url)
                completed_stages.append(PipelineStage.STORY_FOUND)
                self.checkpoint_manager.save_checkpoint(
                    project_id,
                    PipelineStage.STORY_FOUND,
                    {"story": story.model_dump()},
                )

            # Stage 2: Script Writing
            if self._should_run_stage(start_stage, PipelineStage.SCRIPT_GENERATED):
                logger.info("Stage 2: Generating script...")
                if not story:
                    raise GossipToonException("Story not available for script generation")
                script = await self._run_script_writer(story)
                completed_stages.append(PipelineStage.SCRIPT_GENERATED)
                self.checkpoint_manager.save_checkpoint(
                    project_id,
                    PipelineStage.SCRIPT_GENERATED,
                    {"script": script.model_dump()},
                )

            # Stage 2.5: Engagement Hook Generation
            engagement_project = None
            if self._should_run_stage(start_stage, PipelineStage.ENGAGEMENT_GENERATED):
                logger.info("="*60)
                logger.info("Stage 2.5: Generating engagement hooks...")
                logger.info("="*60)
                if not script:
                    raise GossipToonException("Script not available for engagement generation")
                logger.info(f"Calling EngagementWriter with script: {script.get_scene_count()} scenes")
                engagement_project = await self._run_engagement_writer(script)
                logger.info(f"EngagementWriter completed successfully!")
                completed_stages.append(PipelineStage.ENGAGEMENT_GENERATED)
                self.checkpoint_manager.save_checkpoint(
                    project_id,
                    PipelineStage.ENGAGEMENT_GENERATED,
                    {"engagement_project": engagement_project.model_dump()},
                )
                logger.info(f"Engagement checkpoint saved")

            # Stage 3: Audio Generation
            if self._should_run_stage(start_stage, PipelineStage.AUDIO_GENERATED):
                logger.info("Stage 3: Generating audio...")
                if not script:
                    raise GossipToonException("Script not available for audio generation")
                audio_project = await self._run_audio_generator(script)
                completed_stages.append(PipelineStage.AUDIO_GENERATED)
                self.checkpoint_manager.save_checkpoint(
                    project_id,
                    PipelineStage.AUDIO_GENERATED,
                    {"audio_project": audio_project.model_dump()},
                )

            # Stage 4: Visual Generation
            if self._should_run_stage(start_stage, PipelineStage.VISUALS_GENERATED):
                logger.info("Stage 4: Generating visuals...")
                if not script:
                    raise GossipToonException("Script not available for visual generation")
                visual_project = await self._run_visual_director(script)
                completed_stages.append(PipelineStage.VISUALS_GENERATED)
                self.checkpoint_manager.save_checkpoint(
                    project_id,
                    PipelineStage.VISUALS_GENERATED,
                    {"visual_project": visual_project.model_dump()},
                )

            # Stage 5: Assembly (Video) & Metadata
            if self._should_run_stage(start_stage, PipelineStage.VIDEO_ASSEMBLED):
                logger.info("Stage 5: Assembling video & Generating metadata...")
                if not visual_project or not audio_project:
                    raise GossipToonException("Visual/Audio projects not available for video assembly")
                
                # Run parallel tasks: Video Assembly + Metadata Generation
                video_task = self._run_video_assembler(
                    visual_project, 
                    audio_project,
                    script,
                    engagement_project=engagement_project
                )
                
                metadata_task = self._run_metadata_generator(story, script)
                
                # Execute concurrently
                results = await asyncio.gather(video_task, metadata_task, return_exceptions=True)
                
                video_project = results[0]
                metadata = results[1]
                
                # Check for video failure
                if isinstance(video_project, Exception):
                    raise video_project

                # Log metadata status
                if isinstance(metadata, Exception):
                    logger.warning(f"Metadata generation failed: {metadata}")
                else:
                    logger.info("Metadata generation completed successfully")

                completed_stages.append(PipelineStage.VIDEO_ASSEMBLED)
                
                self.checkpoint_manager.save_checkpoint(
                    project_id,
                    PipelineStage.VIDEO_ASSEMBLED,
                    {"video_project": video_project.model_dump()},
                )

            # Mark as completed
            self.checkpoint_manager.save_checkpoint(
                project_id,
                PipelineStage.COMPLETED,
                {},
            )
            completed_stages.append(PipelineStage.COMPLETED)

            logger.info(f"Pipeline completed successfully: {project_id}")

            return PipelineResult(
                project_id=project_id,
                success=True,
                video_project=video_project,
                completed_stages=completed_stages,
            )

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            self.checkpoint_manager.add_error(project_id, str(e))

            return PipelineResult(
                project_id=project_id,
                success=False,
                error=str(e),
                completed_stages=completed_stages,
            )

    async def validate_setup(self) -> dict[str, bool]:
        """Validate pipeline setup and API keys.

        Returns:
            Dictionary of validation results
        """
        logger.info("Validating pipeline setup...")

        results = {}

        # Validate API keys
        results["openai_api_key"] = bool(self.config.api.openai_api_key)
        results["gemini_api_key"] = bool(self.config.api.google_api_key)
        results["elevenlabs_api_key"] = bool(self.config.api.elevenlabs_api_key)

        # Validate directories
        results["output_dirs"] = all(
            [
                self.config.app.output_dir.exists(),
                self.config.images_dir.exists(),
                self.config.audio_dir.exists(),
                self.config.videos_dir.exists(),
            ]
        )

        # Validate FFmpeg
        try:
            results["ffmpeg"] = self.video_assembler.validate_ffmpeg_installation()
        except Exception as e:
            logger.warning(f"FFmpeg validation failed: {e}")
            results["ffmpeg"] = False

        # Validate Whisper (optional)
        try:
            from gossiptoon.audio.whisper import WhisperExtractor

            whisper = WhisperExtractor(self.config)
            results["whisper"] = whisper.validate_installation()
        except Exception as e:
            logger.warning(f"Whisper validation failed: {e}")
            results["whisper"] = False

        # Overall status
        results["ready"] = all(
            [
                results["openai_api_key"],
                results["gemini_api_key"],
                results["elevenlabs_api_key"],
                results["output_dirs"],
                results["ffmpeg"],
            ]
        )

        logger.info(f"Validation complete: ready={results['ready']}")
        return results

    async def _run_story_finder(self, story_url: str) -> Story:
        """Run story finder stage.

        Args:
            story_url: Reddit story URL

        Returns:
            Story object
        """
        story = await self.story_finder.find_story(story_url=story_url)
        logger.info(f"Story found: {story.title[:50]}...")
        return story

    async def _run_script_writer(self, story: Story) -> Script:
        """Run script writer stage.

        Uses 3-agent workflow by default:
        1. SceneStructurer: Generates structure scaffold
        2. ScriptWriter: Fills scaffold with creative content
        3. ScriptEvaluator: QA validation and polish

        Args:
            story: Story object

        Returns:
            Script object
        """
        if self.use_new_workflow:
            # NEW 3-AGENT WORKFLOW with FEEDBACK LOOP (TICKET-041)
            logger.info("Using NEW 3-agent workflow (with coherence check)")
            
            # FEEDBACK LOOP: Retry script generation if coherence check fails
            max_attempts = 3
            final_validation_result = None
            
            for attempt in range(1, max_attempts + 1):
                logger.info(f"📝 Script generation attempt {attempt}/{max_attempts}")
                
                try:
                    # Step 1: Generate Structure
                    logger.info("Step 1: Generating script structure...")
                    scaffold = await self.scene_structurer.generate_scaffold(story)
                    if not scaffold:
                         raise GossipToonException("Failed to generate scaffold")
                    logger.info(f"Scaffold generated: {scaffold.get_scene_count()} scenes")

                    # Step 2: Fill Creative Content
                    logger.info("Step 2: Filling creative content...")
                    filled_script = await self.script_writer.fill_scaffold(story, scaffold)
                    
                    if filled_script is None:
                        raise GossipToonException("❌ CRITICAL: fill_scaffold returned None!")
                    
                    logger.info(f"Script filled: {filled_script.get_scene_count()} scenes")

                    # Step 3: Validate & Coherence/Fidelity Check
                    logger.info("Step 3: Validating script (QA + Coherence + Fidelity)...")
                    validation_result = await self.script_evaluator.validate_script(filled_script, story)
                    
                    if validation_result is None:
                        raise GossipToonException("❌ CRITICAL: validate_script returned None!")
                    
                    # Check validity
                    if validation_result.is_valid:
                        logger.info(f"✅ Script passed all checks (attempt {attempt})")
                        final_validation_result = validation_result
                        break  # Success!
                    else:
                        # Validation failed
                        logger.warning(f"❌ Script rejected (attempt {attempt}/{max_attempts}): {validation_result.error_message}")
                        
                        # Log specific issues
                        if validation_result.fidelity and validation_result.fidelity.verdict == "FAIL":
                             logger.error(f"Fidelity Issues: {validation_result.fidelity.missing_key_points}")

                        # Store result anyway in case we run out of retries
                        final_validation_result = validation_result

                        if attempt < max_attempts:
                            logger.info("🔄 Regenerating script...")
                            import asyncio
                            await asyncio.sleep(2)
                            
                except Exception as e:
                    logger.error(f"Script generation attempt {attempt} failed: {e}")
                    if attempt >= max_attempts:
                        raise
                    logger.info("Retrying...")
                    import asyncio
                    await asyncio.sleep(2)
            
            if final_validation_result is None:
                raise GossipToonException("Failed to generate script after all attempts")
            
            final_script = final_validation_result.script
            logger.info(f"Script validated: {final_script.get_scene_count()} scenes")

            # Step 4: Visual Enrichment (TICKET-038)
            logger.info("Step 4: Enriching visual descriptions...")
            final_script = await self.visual_detailer.enrich_script_visuals(final_script, story)

            # Post-validation (metadata, etc.)
            final_script = self.script_writer._validate_and_enhance_script(final_script, story)

            # Save script
            self.script_writer._save_script(final_script)

            logger.info(
                f"3-AGENT WORKFLOW COMPLETE: {len(final_script.acts)} acts, "
                f"{final_script.get_scene_count()} scenes"
            )
            return final_script

        else:
            # LEGACY 2-agent workflow
            logger.info("Using LEGACY 2-agent workflow")
            script = await self.script_writer.write_script(story)
            logger.info(f"Script generated: {len(script.acts)} acts, {script.get_scene_count()} scenes")
            return script

    async def _run_engagement_writer(self, script: Script):
        """Run engagement writer stage.

        Args:
            script: Script object

        Returns:
            EngagementProject object
        """
        from gossiptoon.models.engagement import EngagementProject

        engagement_project = await self.engagement_writer.generate_engagement_hooks(script)
        logger.info(
            f"Engagement hooks generated: {len(engagement_project.hooks)} hooks - "
            f"{[h.hook_id for h in engagement_project.hooks]}"
        )
        return engagement_project

    async def _run_audio_generator(self, script: Script) -> AudioProject:
        """Run audio generator stage.

        Args:
            script: Script object

        Returns:
            AudioProject object
        """
        audio_project = await self.audio_generator.generate_audio_project(script)
        logger.info(f"Audio generated: {audio_project.total_duration:.1f}s")
        
        # Overlay SFX if scenes have visual_sfx
        audio_project = await self._overlay_audio_sfx(script, audio_project)
        
        return audio_project
    
    async def _overlay_audio_sfx(self, script: Script, audio_project: AudioProject) -> AudioProject:
        """Overlay audio SFX on master audio based on scene visual_sfx.

        Args:
            script: Script with scene SFX information
            audio_project: Audio project with master audio

        Returns:
            AudioProject with SFX-mixed master audio
        """
        from gossiptoon.audio.sfx_mapper import SFXMapper
        from gossiptoon.audio.sfx_mixer import AudioSFXMixer

        # Group segments by scene_id first
        from collections import defaultdict
        segments_by_scene = defaultdict(list)
        
        for segment in audio_project.segments:
            segments_by_scene[segment.scene_id].append(segment)
        
        # Collect SFX to overlay
        sfx_list = []
        current_offset = 0.0

        for scene in script.get_all_scenes():
            # Get ALL segments for this scene
            scene_segments = segments_by_scene.get(scene.scene_id, [])
            scene_duration = sum(s.duration_seconds for s in scene_segments)
            
            # Check if scene has visual SFX
            if hasattr(scene, 'visual_sfx') and scene.visual_sfx:
                # Map SFX keyword to audio file
                mapper = SFXMapper()
                sfx_key = scene.visual_sfx.upper().strip()
                
                # Check if it's a known Audio SFX keyword
                # This decouples "Visual Text" (e.g. "AITA?") from "Audio Cues" (e.g. "BAM!")
                if sfx_key in mapper.list_available_sfx():
                    logger.info(f"Scene {scene.scene_id} has Audio SFX: {scene.visual_sfx}")
                    sfx_path = mapper.get_sfx_path(scene.visual_sfx)
                    
                    if sfx_path and sfx_path.exists():
                        sfx_list.append((sfx_path, current_offset))
                        logger.info(f"  → Mapped to: {sfx_path.name} at {current_offset:.2f}s")
                    else:
                        logger.warning(f"  → Audio SFX file missing for '{scene.visual_sfx}'")
                else:
                    # It's purely visual text (comic style)
                    logger.debug(f"Scene {scene.scene_id} has Visual-only SFX: {scene.visual_sfx} (No audio mapped)")
            
            # Accumulate TOTAL scene duration (all chunks)
            current_offset += scene_duration
        
        # Apply SFX overlays if any found
        if sfx_list:
            logger.info(f"Applying {len(sfx_list)} SFX overlays to master audio...")
            
            mixer = AudioSFXMixer(sfx_volume=0.8)  # 80% volume - increased for better audibility
            master_audio_path = audio_project.master_audio_path
            
            # Create mixed audio with all SFX
            mixed_audio_path = mixer.overlay_multiple_sfx(
                master_audio_path,
                sfx_list,
                output_path=master_audio_path.with_name(master_audio_path.stem + "_with_sfx.mp3")
            )
            
            # Update audio project to use mixed audio
            audio_project.master_audio_path = mixed_audio_path
            logger.info(f"SFX mixing complete: {mixed_audio_path}")
        else:
            logger.info("No SFX to overlay")
        
        return audio_project

    async def _run_visual_director(self, script: Script) -> VisualProject:
        """Run visual director stage.

        Args:
            script: Script object

        Returns:
            VisualProject object
        """
        visual_project = await self.visual_director.create_visual_project(script)
        logger.info(f"Visuals generated: {len(visual_project.assets)} images")
        return visual_project

    async def _run_video_assembler(
        self,
        visual_project: VisualProject,
        audio_project: AudioProject,
        script: Script,
        engagement_project=None,  # Optional EngagementProject
    ) -> VideoProject:
        """Run video assembler stage.

        Args:
            visual_project: Visual project
            audio_project: Audio project
            script: Script object
            engagement_project: Optional engagement hooks

        Returns:
            VideoProject object
        """
        video_project = await self.video_assembler.assemble_video(
            visual_project, 
            audio_project,
            script,
            engagement_project=engagement_project
        )
        logger.info(f"Video assembled: {video_project.output_path}")
        return video_project

    def _should_run_stage(
        self,
        current_stage: PipelineStage,
        target_stage: PipelineStage,
    ) -> bool:
        """Check if stage should be executed.

        Args:
            current_stage: Current checkpoint stage
            target_stage: Stage to check

        Returns:
            True if stage should run
        """
        stage_order = [
            PipelineStage.INITIALIZED,
            PipelineStage.STORY_FOUND,
            PipelineStage.SCRIPT_GENERATED,
            PipelineStage.ENGAGEMENT_GENERATED,
            PipelineStage.AUDIO_GENERATED,
            PipelineStage.VISUALS_GENERATED,
            PipelineStage.VIDEO_ASSEMBLED,
            PipelineStage.COMPLETED,
        ]

        current_idx = stage_order.index(current_stage)
        target_idx = stage_order.index(target_stage)

        return target_idx > current_idx

    def _generate_project_id(self) -> str:
        """Generate unique project ID.

        Returns:
            Project ID string
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"project_{timestamp}"

    def _load_story_from_checkpoint(self, checkpoint) -> Optional[Story]:
        """Load story from checkpoint data.

        Args:
            checkpoint: Checkpoint data

        Returns:
            Story object or None
        """
        if checkpoint.story_data and "story" in checkpoint.story_data:
            return Story.model_validate(checkpoint.story_data["story"])
        return None

    def _load_script_from_checkpoint(self, checkpoint) -> Optional[Script]:
        """Load script from checkpoint data.

        Args:
            checkpoint: Checkpoint data

        Returns:
            Script object or None
        """
        if checkpoint.script_data and "script" in checkpoint.script_data:
            return Script.model_validate(checkpoint.script_data["script"])
        return None

    def _load_audio_from_checkpoint(self, checkpoint) -> Optional[AudioProject]:
        """Load audio project from checkpoint data.

        Args:
            checkpoint: Checkpoint data

        Returns:
            AudioProject object or None
        """
        if checkpoint.audio_data and "audio_project" in checkpoint.audio_data:
            return AudioProject.model_validate(checkpoint.audio_data["audio_project"])
        return None

    def _load_visual_from_checkpoint(self, checkpoint) -> Optional[VisualProject]:
        """Load visual project from checkpoint data.

        Args:
            checkpoint: Checkpoint data

        Returns:
            VisualProject object or None
        """
        if checkpoint.visual_data and "visual_project" in checkpoint.visual_data:
            return VisualProject.model_validate(checkpoint.visual_data["visual_project"])
        return None

    async def _run_metadata_generator(self, story: Story, script: Script):
        """Run metadata generator stage.
        
        Args:
            story: Story object
            script: Script object
            
        Returns:
            YouTubeMetadata object
        """
        try:
            from gossiptoon.agents.metadata_generator import MetadataGeneratorAgent
            
            generator = MetadataGeneratorAgent(self.config)
            metadata = await generator.generate_metadata(story, script)
            
            # Save to disk
            output_dir = self.config.outputs_dir / self.config.job_id / "youtube"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save formats
            with open(output_dir / "metadata.json", "w") as f:
                f.write(metadata.model_dump_json(indent=2))
                
            with open(output_dir / "metadata.md", "w") as f:
                f.write(metadata.to_markdown())
                
            with open(output_dir / "metadata.txt", "w") as f:
                f.write(metadata.to_upload_text())
                
            logger.info(f"YouTube metadata saved to: {output_dir}")
            return metadata
            
        except Exception as e:
            logger.error(f"Metadata generation error: {e}")
            raise
