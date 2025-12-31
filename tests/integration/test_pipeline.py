"""Integration tests for pipeline orchestration.

Tests:
- Checkpoint save/load
- Pipeline execution with mocks
- Resume from checkpoint
- Error handling and recovery
- Validation
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gossiptoon.core.config import ConfigManager
from gossiptoon.core.exceptions import CheckpointError, GossipToonException
from gossiptoon.models.audio import AudioProject, AudioSegment, WordTimestamp
from gossiptoon.models.script import Act, Scene, Script
from gossiptoon.models.story import Story
from gossiptoon.models.video import RenderConfig, TimelineSegment, VideoProject
from gossiptoon.models.visual import ImagePrompt, VisualAsset, VisualProject
from gossiptoon.pipeline.checkpoint import CheckpointData, CheckpointManager, PipelineStage
from gossiptoon.pipeline.orchestrator import PipelineOrchestrator, PipelineResult


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_dirs(tmp_path):
    """Create temporary directories."""
    dirs = {
        "checkpoints": tmp_path / "checkpoints",
        "images": tmp_path / "images",
        "audio": tmp_path / "audio",
        "videos": tmp_path / "videos",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


@pytest.fixture
def mock_config(temp_dirs):
    """Create mock configuration."""
    config = MagicMock(spec=ConfigManager)
    config.checkpoints_dir = temp_dirs["checkpoints"]
    config.images_dir = temp_dirs["images"]
    config.audio_dir = temp_dirs["audio"]
    config.videos_dir = temp_dirs["videos"]
    config.outputs_dir = temp_dirs["checkpoints"].parent

    # API keys
    config.openai_api_key = "test_openai_key"
    config.gemini_api_key = "test_gemini_key"
    config.elevenlabs_api_key = "test_elevenlabs_key"

    # API config for agents
    api_config = MagicMock()
    api_config.reddit_client_id = "test_reddit_client_id"
    api_config.reddit_client_secret = "test_reddit_client_secret"
    api_config.reddit_user_agent = "test_user_agent"
    config.api = api_config

    # Video config
    video_config = MagicMock()
    video_config.width = 1080
    video_config.height = 1920
    video_config.fps = 30
    video_config.resolution = "1080x1920"
    video_config.video_codec = "libx264"
    video_config.audio_codec = "aac"
    video_config.preset = "medium"
    video_config.bitrate = "5M"
    video_config.ken_burns_enabled = True
    video_config.captions_enabled = True
    config.video = video_config

    return config


@pytest.fixture
def sample_story():
    """Create sample story."""
    from datetime import datetime

    from gossiptoon.core.constants import StoryCategory
    from gossiptoon.models.story import RedditPostMetadata

    return Story(
        id="test_story_001",
        title="AITA for telling my sister the truth?",
        content="My sister asked me if her new haircut looked good and I told her honestly that it wasn't the most flattering style for her face shape. Now she won't talk to me and my family is saying I was cruel.",
        category=StoryCategory.RELATIONSHIP,
        metadata=RedditPostMetadata(
            post_id="abc123",
            subreddit="AmItheAsshole",
            author="test_user",
            upvotes=1500,
            num_comments=234,
            created_utc=datetime.utcfromtimestamp(1234567890),
            url="https://reddit.com/r/test/comments/123",
        ),
        viral_score=85.0,
    )


@pytest.fixture
def sample_script():
    """Create sample script."""
    from gossiptoon.core.constants import EmotionTone

    scenes = [
        Scene(
            scene_id="scene_1",
            act_id="hook",
            narration="This is the hook",
            visual_description="Dramatic scene",
            duration_estimate=3.0,
            emotion=EmotionTone.DRAMATIC,
        ),
        Scene(
            scene_id="scene_2",
            act_id="build",
            narration="This is the build",
            visual_description="Exciting scene",
            duration_estimate=4.0,
            emotion=EmotionTone.EXCITED,
        ),
    ]

    return Script(
        script_id="test_script_001",
        story_id="test_story_001",
        acts=[
            Act(act_id="hook", name="Hook", scenes=[scenes[0]]),
            Act(act_id="build", name="Build", scenes=[scenes[1]]),
        ],
        total_estimated_duration=7.0,
        target_duration=60.0,
        metadata={},
    )


# ============================================================================
# Checkpoint Manager Tests
# ============================================================================


def test_checkpoint_manager_initialization(temp_dirs):
    """Test checkpoint manager initialization."""
    manager = CheckpointManager(temp_dirs["checkpoints"])
    assert manager.checkpoint_dir.exists()


def test_save_and_load_checkpoint(temp_dirs):
    """Test checkpoint save and load."""
    manager = CheckpointManager(temp_dirs["checkpoints"])

    # Save checkpoint
    project_id = "test_project_001"
    stage = PipelineStage.SCRIPT_GENERATED
    data = {"script": {"script_id": "test_script"}}

    checkpoint_path = manager.save_checkpoint(project_id, stage, data)
    assert checkpoint_path.exists()

    # Load checkpoint
    checkpoint = manager.load_checkpoint(project_id)
    assert checkpoint.project_id == project_id
    assert checkpoint.current_stage == stage
    assert checkpoint.script_data == data


def test_checkpoint_exists(temp_dirs):
    """Test checkpoint existence check."""
    manager = CheckpointManager(temp_dirs["checkpoints"])

    project_id = "test_project_002"
    assert not manager.checkpoint_exists(project_id)

    manager.save_checkpoint(project_id, PipelineStage.INITIALIZED, {})
    assert manager.checkpoint_exists(project_id)


def test_delete_checkpoint(temp_dirs):
    """Test checkpoint deletion."""
    manager = CheckpointManager(temp_dirs["checkpoints"])

    project_id = "test_project_003"
    manager.save_checkpoint(project_id, PipelineStage.INITIALIZED, {})
    assert manager.checkpoint_exists(project_id)

    manager.delete_checkpoint(project_id)
    assert not manager.checkpoint_exists(project_id)


def test_add_error_to_checkpoint(temp_dirs):
    """Test adding error to checkpoint."""
    manager = CheckpointManager(temp_dirs["checkpoints"])

    project_id = "test_project_004"
    manager.save_checkpoint(project_id, PipelineStage.INITIALIZED, {})

    error_msg = "Test error message"
    manager.add_error(project_id, error_msg)

    checkpoint = manager.load_checkpoint(project_id)
    assert len(checkpoint.error_history) == 1
    assert error_msg in checkpoint.error_history[0]


def test_list_checkpoints(temp_dirs):
    """Test listing checkpoints."""
    manager = CheckpointManager(temp_dirs["checkpoints"])

    # Create multiple checkpoints
    manager.save_checkpoint("project_001", PipelineStage.INITIALIZED, {})
    manager.save_checkpoint("project_002", PipelineStage.SCRIPT_GENERATED, {})
    manager.save_checkpoint("project_003", PipelineStage.AUDIO_GENERATED, {})

    checkpoints = manager.list_checkpoints()
    assert len(checkpoints) == 3
    assert "project_001" in checkpoints
    assert "project_002" in checkpoints
    assert "project_003" in checkpoints


def test_checkpoint_not_found(temp_dirs):
    """Test loading non-existent checkpoint."""
    manager = CheckpointManager(temp_dirs["checkpoints"])

    with pytest.raises(CheckpointError, match="No checkpoint found"):
        manager.load_checkpoint("nonexistent_project")


def test_get_next_stage():
    """Test getting next pipeline stage."""
    manager = CheckpointManager(Path("/tmp/test"))

    next_stage = manager.get_next_stage(PipelineStage.INITIALIZED)
    assert next_stage == PipelineStage.STORY_FOUND

    next_stage = manager.get_next_stage(PipelineStage.VIDEO_ASSEMBLED)
    assert next_stage == PipelineStage.COMPLETED

    next_stage = manager.get_next_stage(PipelineStage.COMPLETED)
    assert next_stage is None


# ============================================================================
# Pipeline Orchestrator Tests
# ============================================================================


@pytest.mark.asyncio
async def test_orchestrator_initialization(mock_config):
    """Test orchestrator initialization."""
    # Mock the agent initializations to avoid needing real API keys
    with patch("gossiptoon.pipeline.orchestrator.StoryFinderAgent"), \
         patch("gossiptoon.pipeline.orchestrator.ScriptWriterAgent"), \
         patch("gossiptoon.pipeline.orchestrator.AudioGenerator"), \
         patch("gossiptoon.pipeline.orchestrator.VisualDirector"), \
         patch("gossiptoon.pipeline.orchestrator.VideoAssembler"):
        orchestrator = PipelineOrchestrator(mock_config)

        assert orchestrator.config == mock_config
        assert orchestrator.story_finder is not None
        assert orchestrator.script_writer is not None
        assert orchestrator.audio_generator is not None
        assert orchestrator.visual_director is not None
        assert orchestrator.video_assembler is not None
        assert orchestrator.checkpoint_manager is not None


@pytest.mark.asyncio
async def test_validate_setup(mock_config):
    """Test setup validation."""
    with patch("gossiptoon.pipeline.orchestrator.StoryFinderAgent"), \
         patch("gossiptoon.pipeline.orchestrator.ScriptWriterAgent"), \
         patch("gossiptoon.pipeline.orchestrator.AudioGenerator"), \
         patch("gossiptoon.pipeline.orchestrator.VisualDirector"), \
         patch("gossiptoon.pipeline.orchestrator.VideoAssembler"):
        orchestrator = PipelineOrchestrator(mock_config)

        # Mock FFmpeg validation
        orchestrator.video_assembler.validate_ffmpeg_installation = MagicMock(return_value=True)

        results = await orchestrator.validate_setup()

        assert results["openai_api_key"] is True
        assert results["gemini_api_key"] is True
        assert results["elevenlabs_api_key"] is True
        assert results["output_dirs"] is True
        assert results["ffmpeg"] is True


@pytest.mark.skip(reason="Complex test - needs refactoring for proper mocking")
@pytest.mark.asyncio
async def test_pipeline_run_success(mock_config, sample_story, sample_script, temp_dirs):
    """Test successful pipeline execution."""
    with patch("gossiptoon.pipeline.orchestrator.StoryFinderAgent"), \
         patch("gossiptoon.pipeline.orchestrator.ScriptWriterAgent"), \
         patch("gossiptoon.pipeline.orchestrator.AudioGenerator"), \
         patch("gossiptoon.pipeline.orchestrator.VisualDirector"), \
         patch("gossiptoon.pipeline.orchestrator.VideoAssembler"):
        orchestrator = PipelineOrchestrator(mock_config)

    # Create mock audio and visual data
    audio_path = temp_dirs["audio"] / "master.mp3"
    audio_path.write_bytes(b"fake_audio")

    scene1_audio = temp_dirs["audio"] / "scene_1.mp3"
    scene1_audio.write_bytes(b"fake_audio_1")

    scene2_audio = temp_dirs["audio"] / "scene_2.mp3"
    scene2_audio.write_bytes(b"fake_audio_2")

    from gossiptoon.core.constants import EmotionTone

    mock_audio_project = AudioProject(
        script_id="test_script_001",
        segments=[
            AudioSegment(
                scene_id="scene_1",
                file_path=scene1_audio,
                duration_seconds=3.0,
                emotion=EmotionTone.DRAMATIC,
                voice_id="test_voice",
                timestamps=[],
            ),
            AudioSegment(
                scene_id="scene_2",
                file_path=scene2_audio,
                duration_seconds=4.0,
                emotion=EmotionTone.EXCITED,
                voice_id="test_voice",
                timestamps=[],
            ),
        ],
        master_audio_path=audio_path,
        total_duration=7.0,
        voice_id="test_voice",
    )

    image1 = temp_dirs["images"] / "scene_1.png"
    image1.write_bytes(b"fake_image_1")
    image2 = temp_dirs["images"] / "scene_2.png"
    image2.write_bytes(b"fake_image_2")

    mock_visual_project = VisualProject(
        script_id="test_script_001",
        assets=[
            VisualAsset(
                scene_id="scene_1",
                image_path=image1,
                prompt_used=ImagePrompt(
                    scene_id="scene_1",
                    base_prompt="Test prompt",
                    characters=[],
                    style="cinematic",
                    aspect_ratio="9:16",
                ),
                characters_rendered=[],
                width=1080,
                height=1920,
            ),
            VisualAsset(
                scene_id="scene_2",
                image_path=image2,
                prompt_used=ImagePrompt(
                    scene_id="scene_2",
                    base_prompt="Test prompt 2",
                    characters=[],
                    style="cinematic",
                    aspect_ratio="9:16",
                ),
                characters_rendered=[],
                width=1080,
                height=1920,
            ),
        ],
        character_bank=[],
        generation_config={},
    )

    video_path = temp_dirs["videos"] / "test_script_001.mp4"
    video_path.write_bytes(b"fake_video")

    mock_video_project = VideoProject(
        project_id="test_script_001",
        script_id="test_script_001",
        timeline=[
            TimelineSegment(
                scene_id="scene_1",
                start_time=0.0,
                end_time=3.0,
                visual_asset_path=image1,
                audio_segment_path=scene1_audio,
                effects=[],
            ),
            TimelineSegment(
                scene_id="scene_2",
                start_time=3.0,
                end_time=7.0,
                visual_asset_path=image2,
                audio_segment_path=scene2_audio,
                effects=[],
            ),
        ],
        render_config=RenderConfig(resolution="1080x1920", fps=30),
        output_path=video_path,
    )

    # Mock all pipeline stages
    orchestrator.story_finder.find_story = AsyncMock(return_value=sample_story)
    orchestrator.script_writer.write_script = AsyncMock(return_value=sample_script)
    orchestrator.audio_generator.generate_audio = AsyncMock(return_value=mock_audio_project)
    orchestrator.visual_director.generate_visuals = AsyncMock(return_value=mock_visual_project)
    orchestrator.video_assembler.assemble_video = AsyncMock(return_value=mock_video_project)

    # Run pipeline
    result = await orchestrator.run(story_url="https://reddit.com/test")

    # Verify result
    assert result.success is True
    assert result.video_project is not None
    assert len(result.completed_stages) == 6  # All stages + COMPLETED

    # Verify checkpoint was saved
    assert orchestrator.checkpoint_manager.checkpoint_exists(result.project_id)


@pytest.mark.skip(reason="Complex test - needs refactoring for proper mocking")
@pytest.mark.asyncio
async def test_pipeline_resume(mock_config, sample_story, sample_script, temp_dirs):
    """Test pipeline resume from checkpoint."""
    orchestrator = PipelineOrchestrator(mock_config)

    # Create a checkpoint at SCRIPT_GENERATED stage
    project_id = "test_project_resume"
    orchestrator.checkpoint_manager.save_checkpoint(
        project_id,
        PipelineStage.SCRIPT_GENERATED,
        {
            "story": sample_story.model_dump(),
            "script": sample_script.model_dump(),
        },
    )

    # Update checkpoint with both story and script data
    checkpoint = orchestrator.checkpoint_manager.load_checkpoint(project_id)
    checkpoint.story_data = {"story": sample_story.model_dump()}
    checkpoint.script_data = {"script": sample_script.model_dump()}

    checkpoint_path = orchestrator.checkpoint_manager._get_checkpoint_path(project_id)
    checkpoint_json = checkpoint.model_dump_json(indent=2)
    checkpoint_path.write_text(checkpoint_json)

    # Create mock data for remaining stages
    audio_path = temp_dirs["audio"] / "master.mp3"
    audio_path.write_bytes(b"fake_audio")

    from gossiptoon.core.constants import EmotionTone

    mock_audio_project = AudioProject(
        script_id=sample_script.script_id,
        segments=[
            AudioSegment(
                scene_id="scene_1",
                file_path=temp_dirs["audio"] / "scene_1.mp3",
                duration_seconds=3.0,
                emotion=EmotionTone.DRAMATIC,
                voice_id="test_voice",
                timestamps=[],
            ),
        ],
        master_audio_path=audio_path,
        total_duration=3.0,
        voice_id="test_voice",
    )

    image1 = temp_dirs["images"] / "scene_1.png"
    image1.write_bytes(b"fake_image")

    mock_visual_project = VisualProject(
        script_id=sample_script.script_id,
        assets=[
            VisualAsset(
                scene_id="scene_1",
                image_path=image1,
                prompt_used=ImagePrompt(
                    scene_id="scene_1",
                    base_prompt="Test",
                    characters=[],
                    style="cinematic",
                    aspect_ratio="9:16",
                ),
                characters_rendered=[],
                width=1080,
                height=1920,
            ),
        ],
        character_bank=[],
        generation_config={},
    )

    video_path = temp_dirs["videos"] / f"{sample_script.script_id}.mp4"
    video_path.write_bytes(b"fake_video")

    mock_video_project = VideoProject(
        project_id=sample_script.script_id,
        script_id=sample_script.script_id,
        timeline=[],
        render_config=RenderConfig(),
        output_path=video_path,
    )

    # Mock remaining stages (audio, visual, video)
    orchestrator.audio_generator.generate_audio = AsyncMock(return_value=mock_audio_project)
    orchestrator.visual_director.generate_visuals = AsyncMock(return_value=mock_visual_project)
    orchestrator.video_assembler.assemble_video = AsyncMock(return_value=mock_video_project)

    # Resume pipeline
    result = await orchestrator.run(project_id=project_id, resume=True)

    # Verify result
    assert result.success is True

    # Story and script stages should be skipped
    orchestrator.story_finder.find_story.assert_not_called()
    orchestrator.script_writer.write_script.assert_not_called()

    # Remaining stages should be executed
    orchestrator.audio_generator.generate_audio.assert_called_once()
    orchestrator.visual_director.generate_visuals.assert_called_once()
    orchestrator.video_assembler.assemble_video.assert_called_once()


@pytest.mark.asyncio
async def test_pipeline_error_handling(mock_config):
    """Test pipeline error handling."""
    with patch("gossiptoon.pipeline.orchestrator.StoryFinderAgent"), \
         patch("gossiptoon.pipeline.orchestrator.ScriptWriterAgent"), \
         patch("gossiptoon.pipeline.orchestrator.AudioGenerator"), \
         patch("gossiptoon.pipeline.orchestrator.VisualDirector"), \
         patch("gossiptoon.pipeline.orchestrator.VideoAssembler"):
        orchestrator = PipelineOrchestrator(mock_config)

        # Mock story finder to fail
        orchestrator.story_finder.find_story = AsyncMock(
            side_effect=GossipToonException("Story not found")
        )

        # Run pipeline
        result = await orchestrator.run(story_url="https://reddit.com/test")

        # Verify result
        assert result.success is False
        assert result.error is not None
        assert "Story not found" in result.error
        assert result.project_id is not None


def test_should_run_stage(mock_config):
    """Test stage execution logic."""
    with patch("gossiptoon.pipeline.orchestrator.StoryFinderAgent"), \
         patch("gossiptoon.pipeline.orchestrator.ScriptWriterAgent"), \
         patch("gossiptoon.pipeline.orchestrator.AudioGenerator"), \
         patch("gossiptoon.pipeline.orchestrator.VisualDirector"), \
         patch("gossiptoon.pipeline.orchestrator.VideoAssembler"):
        orchestrator = PipelineOrchestrator(mock_config)

        # From INITIALIZED, should run all stages
        assert orchestrator._should_run_stage(PipelineStage.INITIALIZED, PipelineStage.STORY_FOUND)
        assert orchestrator._should_run_stage(
            PipelineStage.INITIALIZED, PipelineStage.SCRIPT_GENERATED
        )

        # From SCRIPT_GENERATED, should skip earlier stages
        assert not orchestrator._should_run_stage(
            PipelineStage.SCRIPT_GENERATED, PipelineStage.STORY_FOUND
        )
        assert not orchestrator._should_run_stage(
            PipelineStage.SCRIPT_GENERATED, PipelineStage.SCRIPT_GENERATED
        )
        assert orchestrator._should_run_stage(
            PipelineStage.SCRIPT_GENERATED, PipelineStage.AUDIO_GENERATED
        )


def test_generate_project_id(mock_config):
    """Test project ID generation."""
    with patch("gossiptoon.pipeline.orchestrator.StoryFinderAgent"), \
         patch("gossiptoon.pipeline.orchestrator.ScriptWriterAgent"), \
         patch("gossiptoon.pipeline.orchestrator.AudioGenerator"), \
         patch("gossiptoon.pipeline.orchestrator.VisualDirector"), \
         patch("gossiptoon.pipeline.orchestrator.VideoAssembler"):
        orchestrator = PipelineOrchestrator(mock_config)

        project_id = orchestrator._generate_project_id()
        assert project_id.startswith("project_")
        assert len(project_id) > 10
