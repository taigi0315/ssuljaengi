"""Pytest configuration and fixtures."""

from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from pydantic import HttpUrl

from gossiptoon.core.constants import ActType, EmotionTone, StoryCategory
from gossiptoon.models.audio import AudioProject, AudioSegment, WordTimestamp
from gossiptoon.models.script import Act, Scene, Script
from gossiptoon.models.story import RedditPostMetadata, Story
from gossiptoon.models.video import RenderConfig, TimelineSegment, VideoProject
from gossiptoon.models.visual import ImagePrompt, VisualAsset, VisualProject


@pytest.fixture
def sample_reddit_metadata() -> RedditPostMetadata:
    """Create sample Reddit post metadata."""
    return RedditPostMetadata(
        post_id="abc123",
        subreddit="AmItheAsshole",
        author="throwaway12345",
        upvotes=15420,
        num_comments=892,
        created_utc=datetime(2025, 1, 1, 12, 0, 0),
        url=HttpUrl("https://reddit.com/r/AmItheAsshole/comments/abc123"),
        flair="Not the A-hole",
    )


@pytest.fixture
def sample_story(sample_reddit_metadata: RedditPostMetadata) -> Story:
    """Create sample story."""
    return Story(
        id="story_20250101_abc123",
        title="AITA for refusing to attend my sister's wedding?",
        content="So this happened last week. My sister (28F) is getting married to her fiancé (30M). "
        "I (25F) have always been close with my sister, but recently things have been tense. "
        "She asked me to be her maid of honor, but then uninvited me after an argument. "
        "Now she wants me back as a regular guest. I told her I won't be attending at all. "
        "My family says I'm being petty and should just go. AITA?",
        category=StoryCategory.AITA,
        metadata=sample_reddit_metadata,
        viral_score=87.5,
        tags=["wedding", "family", "drama"],
    )


@pytest.fixture
def sample_scene() -> Scene:
    """Create sample scene."""
    return Scene(
        scene_id="scene_hook_01",
        act=ActType.HOOK,
        order=0,
        narration="You won't believe what happened at my sister's wedding last week.",
        emotion=EmotionTone.SHOCKED,
        visual_description="A shocked young woman in casual clothes, standing in a modern living room, "
        "hands on her face in disbelief",
        characters_present=["narrator"],
        estimated_duration_seconds=4.5,
    )


@pytest.fixture
def sample_act(sample_scene: Scene) -> Act:
    """Create sample act with scenes."""
    return Act(
        act_type=ActType.HOOK,
        scenes=[sample_scene],
        target_duration_seconds=5.0,
    )


@pytest.fixture
def sample_script(sample_act: Act) -> Script:
    """Create sample complete script with all five acts."""
    hook_scene = Scene(
        scene_id="scene_hook_01",
        act=ActType.HOOK,
        order=0,
        narration="You won't believe what happened at my sister's wedding.",
        emotion=EmotionTone.SHOCKED,
        visual_description="Shocked young woman in living room",
        characters_present=["Sarah"],
        estimated_duration_seconds=4.0,
    )

    build_scene = Scene(
        scene_id="scene_build_01",
        act=ActType.BUILD,
        order=0,
        narration="My sister and I were always close, until she met her fiancé.",
        emotion=EmotionTone.SAD,
        visual_description="Two sisters hugging, warm family photo",
        characters_present=["Sarah", "Sister"],
        estimated_duration_seconds=10.0,
    )

    crisis_scene = Scene(
        scene_id="scene_crisis_01",
        act=ActType.CRISIS,
        order=0,
        narration="She uninvited me as maid of honor after one stupid argument.",
        emotion=EmotionTone.ANGRY,
        visual_description="Woman arguing with sister, tense confrontation",
        characters_present=["Sarah", "Sister"],
        estimated_duration_seconds=15.0,
    )

    climax_scene = Scene(
        scene_id="scene_climax_01",
        act=ActType.CLIMAX,
        order=0,
        narration="When she asked me to come as a regular guest, I snapped.",
        emotion=EmotionTone.DRAMATIC,
        visual_description="Intense emotional confrontation",
        characters_present=["Sarah", "Sister"],
        estimated_duration_seconds=15.0,
    )

    resolution_scene = Scene(
        scene_id="scene_resolution_01",
        act=ActType.RESOLUTION,
        order=0,
        narration="I told her I wouldn't be attending at all. Best decision I ever made.",
        emotion=EmotionTone.NEUTRAL,
        visual_description="Woman looking relieved and confident",
        characters_present=["Sarah"],
        estimated_duration_seconds=11.0,
    )

    return Script(
        script_id="script_20250101_abc123",
        story_id="story_20250101_abc123",
        title="The Wedding Disaster",
        acts=[
            Act(act_type=ActType.HOOK, scenes=[hook_scene], target_duration_seconds=4.0),
            Act(act_type=ActType.BUILD, scenes=[build_scene], target_duration_seconds=10.0),
            Act(act_type=ActType.CRISIS, scenes=[crisis_scene], target_duration_seconds=15.0),
            Act(act_type=ActType.CLIMAX, scenes=[climax_scene], target_duration_seconds=15.0),
            Act(
                act_type=ActType.RESOLUTION,
                scenes=[resolution_scene],
                target_duration_seconds=11.0,
            ),
        ],
        total_estimated_duration=55.0,
        target_audience="18-35 years old",
    )


@pytest.fixture
def sample_word_timestamps() -> list[WordTimestamp]:
    """Create sample word timestamps."""
    return [
        WordTimestamp(word="You", start=0.0, end=0.2, confidence=0.95),
        WordTimestamp(word="won't", start=0.2, end=0.5, confidence=0.92),
        WordTimestamp(word="believe", start=0.5, end=0.9, confidence=0.98),
        WordTimestamp(word="this", start=0.9, end=1.1, confidence=0.96),
    ]


@pytest.fixture
def sample_audio_segment(tmp_path: Path, sample_word_timestamps: list[WordTimestamp]) -> AudioSegment:
    """Create sample audio segment."""
    audio_path = tmp_path / "scene_hook_01.mp3"
    audio_path.touch()

    return AudioSegment(
        scene_id="scene_hook_01",
        file_path=audio_path,
        duration_seconds=4.5,
        emotion=EmotionTone.SHOCKED,
        voice_id="21m00Tcm4TlvDq8ikWAM",
        timestamps=sample_word_timestamps,
    )


@pytest.fixture
def sample_audio_project(tmp_path: Path, sample_audio_segment: AudioSegment) -> AudioProject:
    """Create sample audio project."""
    master_path = tmp_path / "master.mp3"
    master_path.touch()

    return AudioProject(
        script_id="script_20250101_abc123",
        segments=[sample_audio_segment],
        total_duration=4.5,
        master_audio_path=master_path,
        voice_id="21m00Tcm4TlvDq8ikWAM",
    )


@pytest.fixture
def sample_image_prompt() -> ImagePrompt:
    """Create sample image prompt."""
    return ImagePrompt(
        scene_id="scene_hook_01",
        base_prompt="A shocked young woman standing in a modern living room",
        characters=["Sarah"],
        style="cinematic digital art, dramatic lighting",
        aspect_ratio="9:16",
    )


@pytest.fixture
def sample_visual_asset(tmp_path: Path, sample_image_prompt: ImagePrompt) -> VisualAsset:
    """Create sample visual asset."""
    image_path = tmp_path / "scene_hook_01.png"
    image_path.touch()

    return VisualAsset(
        scene_id="scene_hook_01",
        image_path=image_path,
        prompt_used=sample_image_prompt,
        characters_rendered=["Sarah"],
        width=1080,
        height=1920,
    )


@pytest.fixture
def sample_visual_project(sample_visual_asset: VisualAsset) -> VisualProject:
    """Create sample visual project."""
    return VisualProject(
        script_id="script_20250101_abc123",
        assets=[sample_visual_asset],
        character_bank=[],
    )


@pytest.fixture
def sample_timeline_segment(
    tmp_path: Path, sample_visual_asset: VisualAsset, sample_audio_segment: AudioSegment
) -> TimelineSegment:
    """Create sample timeline segment."""
    return TimelineSegment(
        scene_id="scene_hook_01",
        start_time=0.0,
        end_time=4.5,
        visual_asset_path=sample_visual_asset.image_path,
        audio_segment_path=sample_audio_segment.file_path,
        effects=[],
    )


@pytest.fixture
def sample_render_config() -> RenderConfig:
    """Create sample render configuration."""
    return RenderConfig(
        resolution="1080x1920",
        fps=30,
        video_codec="libx264",
        audio_codec="aac",
        preset="medium",
    )


@pytest.fixture
def sample_video_project(
    sample_timeline_segment: TimelineSegment, sample_render_config: RenderConfig
) -> VideoProject:
    """Create sample video project."""
    return VideoProject(
        project_id="project_20250101_abc123",
        script_id="script_20250101_abc123",
        timeline=[sample_timeline_segment],
        captions=[],
        render_config=sample_render_config,
    )
