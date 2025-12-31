"""Unit tests for video assembly components.

Tests:
- Ken Burns effect
- Caption effect
- FFmpeg command builder
- Video assembler
- Effect composition
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from gossiptoon.core.config import ConfigManager
from gossiptoon.core.exceptions import VideoAssemblyError
from gossiptoon.models.audio import AudioProject, AudioSegment, WordTimestamp
from gossiptoon.models.visual import ImagePrompt, VisualAsset, VisualProject
from gossiptoon.video.assembler import VideoAssembler
from gossiptoon.video.effects.base import CompositeEffect, Effect, EffectConfig
from gossiptoon.video.effects.captions import CaptionConfig, CaptionEffect
from gossiptoon.video.effects.ken_burns import KenBurnsConfig, KenBurnsEffect
from gossiptoon.video.ffmpeg_builder import FFmpegBuilder, FFmpegCommand, VideoSegment


@pytest.fixture
def temp_dirs(tmp_path):
    """Create temporary directories for testing."""
    dirs = {
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
    config.images_dir = temp_dirs["images"]
    config.audio_dir = temp_dirs["audio"]
    config.videos_dir = temp_dirs["videos"]

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
def sample_word_timestamps():
    """Create sample word timestamps."""
    return [
        WordTimestamp(word="Hello", start=0.0, end=0.5, confidence=0.95),
        WordTimestamp(word="world", start=0.6, end=1.0, confidence=0.93),
        WordTimestamp(word="this", start=1.1, end=1.4, confidence=0.92),
        WordTimestamp(word="is", start=1.5, end=1.7, confidence=0.94),
        WordTimestamp(word="a", start=1.8, end=1.9, confidence=0.91),
        WordTimestamp(word="test", start=2.0, end=2.5, confidence=0.96),
    ]


@pytest.fixture
def sample_audio_project(temp_dirs, sample_word_timestamps):
    """Create sample audio project."""
    from gossiptoon.core.constants import EmotionTone

    audio_path = temp_dirs["audio"] / "master.mp3"
    audio_path.write_bytes(b"fake_audio")

    scene1_audio = temp_dirs["audio"] / "scene_1.mp3"
    scene1_audio.write_bytes(b"fake_audio_1")

    scene2_audio = temp_dirs["audio"] / "scene_2.mp3"
    scene2_audio.write_bytes(b"fake_audio_2")

    return AudioProject(
        script_id="test_script",
        segments=[
            AudioSegment(
                scene_id="scene_1",
                file_path=scene1_audio,
                duration_seconds=3.0,
                emotion=EmotionTone.DRAMATIC,
                voice_id="test_voice",
                timestamps=sample_word_timestamps[:3],
            ),
            AudioSegment(
                scene_id="scene_2",
                file_path=scene2_audio,
                duration_seconds=2.5,
                emotion=EmotionTone.NEUTRAL,
                voice_id="test_voice",
                timestamps=sample_word_timestamps[3:],
            ),
        ],
        master_audio_path=audio_path,
        total_duration=5.5,
        voice_id="test_voice",
    )


@pytest.fixture
def sample_visual_project(temp_dirs):
    """Create sample visual project."""
    image_paths = []
    for i in range(2):
        img_path = temp_dirs["images"] / f"scene_{i+1}.png"
        img_path.write_bytes(b"fake_image")
        image_paths.append(img_path)

    return VisualProject(
        script_id="test_script",
        assets=[
            VisualAsset(
                scene_id="scene_1",
                image_path=image_paths[0],
                prompt_used=ImagePrompt(
                    scene_id="scene_1",
                    base_prompt="A mysterious scene with dramatic lighting and composition",
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
                image_path=image_paths[1],
                prompt_used=ImagePrompt(
                    scene_id="scene_2",
                    base_prompt="An exciting conclusion with vibrant colors and energy",
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
        generation_config={"model": "test-model"},
    )


# ============================================================================
# Ken Burns Effect Tests
# ============================================================================


def test_ken_burns_config():
    """Test Ken Burns configuration."""
    config = KenBurnsConfig(
        enabled=True,
        zoom_start=1.0,
        zoom_end=1.3,
        pan_direction="up",
        pan_intensity=0.2,
        ease_function="ease-in-out",
    )

    assert config.enabled is True
    assert config.zoom_start == 1.0
    assert config.zoom_end == 1.3
    assert config.pan_direction == "up"
    assert config.pan_intensity == 0.2


def test_ken_burns_effect_initialization():
    """Test Ken Burns effect initialization."""
    config = KenBurnsConfig()
    effect = KenBurnsEffect(config)

    assert effect.is_enabled() is True
    assert effect.get_effect_name().startswith("KenBurns")


def test_ken_burns_filter_string():
    """Test Ken Burns filter string generation."""
    config = KenBurnsConfig(
        zoom_start=1.0,
        zoom_end=1.2,
        pan_direction="none",
        output_width=1080,
        output_height=1920,
    )
    effect = KenBurnsEffect(config)

    filter_str = effect.get_filter_string(
        "[0:v]",
        "[v0]",
        duration=5.0,
        fps=30,
    )

    assert "zoompan" in filter_str
    assert "[0:v]" in filter_str
    assert "[v0]" in filter_str
    assert "1080x1920" in filter_str


def test_ken_burns_tunable_params():
    """Test getting tunable parameters."""
    config = KenBurnsConfig(zoom_start=1.0, zoom_end=1.5)
    effect = KenBurnsEffect(config)

    params = effect.get_tunable_params()

    assert "zoom_start" in params
    assert "zoom_end" in params
    assert "pan_direction" in params
    assert params["zoom_start"] == 1.0
    assert params["zoom_end"] == 1.5


# ============================================================================
# Caption Effect Tests
# ============================================================================


def test_caption_config():
    """Test caption configuration."""
    config = CaptionConfig(
        enabled=True,
        font_family="Arial",
        font_size=48,
        font_color="white",
        box_enabled=True,
        position_y="bottom",
        highlight_enabled=True,
    )

    assert config.enabled is True
    assert config.font_family == "Arial"
    assert config.font_size == 48
    assert config.highlight_enabled is True


def test_caption_effect_initialization():
    """Test caption effect initialization."""
    config = CaptionConfig()
    effect = CaptionEffect(config)

    assert effect.is_enabled() is True
    assert "Captions" in effect.get_effect_name()


def test_caption_filter_string(tmp_path):
    """Test caption filter string generation."""
    config = CaptionConfig()
    effect = CaptionEffect(config)

    subtitle_file = tmp_path / "captions.ass"
    subtitle_file.write_text("fake subtitles")

    filter_str = effect.get_filter_string(
        "[v0]",
        "[v1]",
        subtitle_file=subtitle_file,
    )

    assert "subtitles" in filter_str
    assert "[v0]" in filter_str
    assert "[v1]" in filter_str


def test_caption_generate_subtitle_file(tmp_path, sample_word_timestamps):
    """Test subtitle file generation."""
    config = CaptionConfig()
    effect = CaptionEffect(config)

    output_file = tmp_path / "test_captions.ass"

    result = effect.generate_subtitle_file(
        word_timestamps=sample_word_timestamps,
        output_path=output_file,
        video_width=1080,
        video_height=1920,
    )

    assert result.exists()
    content = result.read_text()

    # Check ASS file structure
    assert "[Script Info]" in content
    assert "[V4+ Styles]" in content
    assert "[Events]" in content

    # Check some words are present
    assert "Hello" in content or "world" in content


def test_caption_tunable_params():
    """Test getting tunable parameters."""
    config = CaptionConfig(font_size=60)
    effect = CaptionEffect(config)

    params = effect.get_tunable_params()

    assert "font_size" in params
    assert params["font_size"] == 60


# ============================================================================
# Effect Base and Composition Tests
# ============================================================================


def test_effect_config():
    """Test base effect configuration."""
    config = EffectConfig(enabled=True)
    assert config.enabled is True


class MockEffect(Effect):
    """Mock effect for testing."""

    def get_filter_string(self, input_label, output_label, **context):
        return f"{input_label}mock{output_label}"

    def get_effect_name(self):
        return "MockEffect"


def test_mock_effect():
    """Test mock effect."""
    config = EffectConfig(enabled=True)
    effect = MockEffect(config)

    filter_str = effect.get_filter_string("[0:v]", "[v0]")
    assert filter_str == "[0:v]mock[v0]"
    assert effect.get_effect_name() == "MockEffect"
    assert effect.is_enabled() is True


def test_composite_effect():
    """Test composite effect chaining."""
    effect1 = MockEffect(EffectConfig(enabled=True))
    effect2 = MockEffect(EffectConfig(enabled=True))

    composite = CompositeEffect([effect1, effect2])

    filter_str = composite.get_filter_string("[0:v]", "[v2]")

    # Should chain effects
    assert "[0:v]mock" in filter_str
    assert "[v2]" in filter_str


# ============================================================================
# FFmpeg Builder Tests
# ============================================================================


def test_ffmpeg_builder_initialization():
    """Test FFmpeg builder initialization."""
    builder = FFmpegBuilder(
        fps=30,
        output_width=1080,
        output_height=1920,
    )

    assert builder.fps == 30
    assert builder.output_width == 1080
    assert builder.output_height == 1920


def test_video_segment_creation(temp_dirs):
    """Test video segment creation."""
    img_path = temp_dirs["images"] / "test.png"
    img_path.write_bytes(b"fake_image")

    segment = VideoSegment(
        image_path=img_path,
        duration=5.0,
        effects=[],
    )

    assert segment.image_path == img_path
    assert segment.duration == 5.0


def test_ffmpeg_command_to_list(tmp_path):
    """Test FFmpeg command conversion to list."""
    command = FFmpegCommand(
        inputs=["-i", "input.mp4"],
        filter_complex="scale=1920:1080",
        maps=["[v]"],
        output_options=["-c:v", "libx264"],
        output_file=tmp_path / "output.mp4",
    )

    cmd_list = command.to_list()

    assert "ffmpeg" in cmd_list
    assert "-filter_complex" in cmd_list
    assert "scale=1920:1080" in cmd_list


def test_ffmpeg_command_to_string(tmp_path):
    """Test FFmpeg command conversion to string."""
    command = FFmpegCommand(
        inputs=["-i", "input.mp4"],
        output_file=tmp_path / "output.mp4",
    )

    cmd_str = command.to_string()

    assert "ffmpeg" in cmd_str
    assert "input.mp4" in cmd_str


def test_build_video_command(temp_dirs):
    """Test building complete video command."""
    builder = FFmpegBuilder()

    img_path = temp_dirs["images"] / "test.png"
    img_path.write_bytes(b"fake_image")

    audio_path = temp_dirs["audio"] / "audio.mp3"
    audio_path.write_bytes(b"fake_audio")

    segments = [
        VideoSegment(image_path=img_path, duration=5.0, effects=[]),
    ]

    output_file = temp_dirs["videos"] / "output.mp4"

    command = builder.build_video_command(
        segments=segments,
        master_audio=audio_path,
        output_file=output_file,
    )

    assert isinstance(command, FFmpegCommand)
    assert command.output_file == output_file
    assert len(command.inputs) > 0


def test_estimate_render_time(temp_dirs):
    """Test render time estimation."""
    builder = FFmpegBuilder()

    img_path = temp_dirs["images"] / "test.png"
    img_path.write_bytes(b"fake_image")

    segments = [
        VideoSegment(image_path=img_path, duration=5.0, effects=[]),
        VideoSegment(image_path=img_path, duration=3.0, effects=[]),
    ]

    estimated = builder.estimate_render_time(segments)

    assert estimated > 0
    assert isinstance(estimated, float)


# ============================================================================
# Video Assembler Tests (Mocked)
# ============================================================================


@pytest.mark.asyncio
async def test_video_assembler_initialization(mock_config):
    """Test video assembler initialization."""
    assembler = VideoAssembler(mock_config)

    assert assembler.config == mock_config
    assert isinstance(assembler.ffmpeg_builder, FFmpegBuilder)


@pytest.mark.asyncio
async def test_assemble_video_mocked(mock_config, sample_visual_project, sample_audio_project):
    """Test video assembly with mocked FFmpeg."""
    assembler = VideoAssembler(mock_config)

    # Mock FFmpeg execution
    async def mock_execute(command):
        # Just pretend FFmpeg succeeded
        output_file = command[-1]
        Path(output_file).write_bytes(b"fake_video")

    assembler._execute_ffmpeg = AsyncMock(side_effect=mock_execute)

    video_project = await assembler.assemble_video(
        sample_visual_project,
        sample_audio_project,
    )

    assert video_project.script_id == "test_script"
    assert video_project.project_id == "test_script"
    assert video_project.output_path.exists()
    assert len(video_project.timeline) == 2
    assert video_project.total_duration == 5.5
    assert video_project.render_config.fps == 30
    assert assembler._execute_ffmpeg.called


@pytest.mark.asyncio
async def test_create_preview(mock_config, sample_visual_project, sample_audio_project):
    """Test preview creation."""
    assembler = VideoAssembler(mock_config)

    # Mock FFmpeg execution
    async def mock_execute(command):
        output_file = command[-1]
        Path(output_file).write_bytes(b"fake_preview")

    assembler._execute_ffmpeg = AsyncMock(side_effect=mock_execute)

    preview_path = await assembler.create_preview(
        sample_visual_project,
        sample_audio_project,
        duration_limit=3.0,
    )

    assert preview_path.exists()
    assert "_preview" in str(preview_path)


def test_validate_ffmpeg_not_found(mock_config):
    """Test FFmpeg validation when not installed."""
    assembler = VideoAssembler(mock_config)

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError()

        with pytest.raises(VideoAssemblyError, match="FFmpeg not found"):
            assembler.validate_ffmpeg_installation()


def test_validate_ffmpeg_success(mock_config):
    """Test FFmpeg validation when installed."""
    assembler = VideoAssembler(mock_config)

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="ffmpeg version 6.0")

        result = assembler.validate_ffmpeg_installation()
        assert result is True


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_full_video_pipeline_mocked(mock_config, sample_visual_project, sample_audio_project, temp_dirs):
    """Test complete video pipeline with mocked FFmpeg."""
    assembler = VideoAssembler(mock_config)

    # Mock FFmpeg execution
    async def mock_execute(command):
        output_file = command[-1]
        Path(output_file).write_bytes(b"fake_rendered_video")

    assembler._execute_ffmpeg = AsyncMock(side_effect=mock_execute)

    # Run full assembly
    video_project = await assembler.assemble_video(
        sample_visual_project,
        sample_audio_project,
    )

    # Verify video project
    assert video_project.script_id == "test_script"
    assert video_project.project_id == "test_script"
    assert video_project.output_path.exists()
    assert len(video_project.timeline) == 2
    assert video_project.total_duration == 5.5

    # Verify render config
    width, height = video_project.render_config.get_width_height()
    assert width == 1080
    assert height == 1920
    assert video_project.render_config.fps == 30

    # Verify FFmpeg was called
    assert assembler._execute_ffmpeg.called
