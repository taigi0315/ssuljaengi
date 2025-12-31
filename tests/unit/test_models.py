"""Unit tests for Pydantic models."""

from datetime import datetime
from pathlib import Path

import pytest
from pydantic import HttpUrl, ValidationError

from gossiptoon.core.constants import ActType, EmotionTone, EffectType, StoryCategory
from gossiptoon.models.audio import AudioProject, AudioSegment, WordTimestamp
from gossiptoon.models.script import Act, Scene, Script
from gossiptoon.models.story import RedditPostMetadata, Story
from gossiptoon.models.video import (
    CaptionSegment,
    EffectConfig,
    RenderConfig,
    TimelineSegment,
    VideoProject,
)
from gossiptoon.models.visual import (
    CharacterConsistency,
    ImagePrompt,
    VisualAsset,
    VisualProject,
)


class TestStoryModels:
    """Tests for story data models."""

    def test_reddit_metadata_valid(self, sample_reddit_metadata: RedditPostMetadata) -> None:
        """Test valid Reddit metadata creation."""
        assert sample_reddit_metadata.post_id == "abc123"
        assert sample_reddit_metadata.upvotes == 15420
        assert isinstance(sample_reddit_metadata.url, HttpUrl)

    def test_reddit_metadata_negative_upvotes_fails(self) -> None:
        """Test that negative upvotes are rejected."""
        with pytest.raises(ValidationError):
            RedditPostMetadata(
                post_id="abc",
                subreddit="test",
                author="test",
                upvotes=-5,  # Invalid
                num_comments=0,
                created_utc=datetime.utcnow(),
                url="https://reddit.com/test",
            )

    def test_story_valid(self, sample_story: Story) -> None:
        """Test valid story creation."""
        assert sample_story.id == "story_20250101_abc123"
        assert sample_story.category == StoryCategory.AITA
        assert 0 <= sample_story.viral_score <= 100

    def test_story_word_count(self, sample_story: Story) -> None:
        """Test story word count calculation."""
        word_count = sample_story.get_word_count()
        assert word_count > 0
        assert isinstance(word_count, int)

    def test_story_reading_time(self, sample_story: Story) -> None:
        """Test reading time estimation."""
        reading_time = sample_story.get_reading_time_seconds()
        assert reading_time > 0

    def test_story_suitable_for_shorts(self, sample_story: Story) -> None:
        """Test shorts suitability check."""
        assert sample_story.is_suitable_for_shorts(max_words=500)

    def test_story_too_short_fails(self) -> None:
        """Test that too-short content is rejected."""
        with pytest.raises(ValidationError):
            Story(
                id="test",
                title="Valid Title Here",
                content="Too short",  # Less than 100 chars
                category=StoryCategory.OTHER,
                metadata=RedditPostMetadata(
                    post_id="test",
                    subreddit="test",
                    author="test",
                    upvotes=0,
                    num_comments=0,
                    created_utc=datetime.utcnow(),
                    url="https://reddit.com/test",
                ),
                viral_score=50.0,
            )


class TestScriptModels:
    """Tests for script data models."""

    def test_scene_valid(self, sample_scene: Scene) -> None:
        """Test valid scene creation."""
        assert sample_scene.scene_id == "scene_hook_01"
        assert sample_scene.act == ActType.HOOK
        assert sample_scene.emotion == EmotionTone.SHOCKED

    def test_scene_narration_too_long_fails(self) -> None:
        """Test that too-long narration is rejected."""
        long_narration = " ".join(["word"] * 60)  # 60 words, exceeds max
        with pytest.raises(ValidationError, match="Narration too long"):
            Scene(
                scene_id="test",
                act=ActType.HOOK,
                order=0,
                narration=long_narration,
                emotion=EmotionTone.NEUTRAL,
                visual_description="A scene with a long narration",
                estimated_duration_seconds=5.0,
            )

    def test_scene_visual_description_too_short_fails(self) -> None:
        """Test that too-short visual description is rejected."""
        with pytest.raises(ValidationError, match="too short"):
            Scene(
                scene_id="test",
                act=ActType.HOOK,
                order=0,
                narration="Valid narration here",
                emotion=EmotionTone.NEUTRAL,
                visual_description="Bad",  # Too short
                estimated_duration_seconds=5.0,
            )

    def test_act_scene_order_validation(self) -> None:
        """Test that scene order is validated."""
        scene1 = Scene(
            scene_id="s1",
            act=ActType.HOOK,
            order=0,
            narration="First scene",
            emotion=EmotionTone.NEUTRAL,
            visual_description="A valid description here",
            estimated_duration_seconds=3.0,
        )
        scene2 = Scene(
            scene_id="s2",
            act=ActType.HOOK,
            order=5,  # Wrong order - should be 1
            narration="Second scene",
            emotion=EmotionTone.NEUTRAL,
            visual_description="Another valid description",
            estimated_duration_seconds=3.0,
        )

        with pytest.raises(ValidationError, match="Scene order mismatch"):
            Act(
                act_type=ActType.HOOK,
                scenes=[scene1, scene2],
                target_duration_seconds=6.0,
            )

    def test_act_get_total_duration(self, sample_act: Act) -> None:
        """Test act duration calculation."""
        total = sample_act.get_total_estimated_duration()
        assert total == sum(s.estimated_duration_seconds for s in sample_act.scenes)

    def test_script_requires_five_acts(self) -> None:
        """Test that script requires exactly 5 acts."""
        scene = Scene(
            scene_id="s1",
            act=ActType.HOOK,
            order=0,
            narration="Test scene",
            emotion=EmotionTone.NEUTRAL,
            visual_description="A test scene description",
            estimated_duration_seconds=5.0,
        )

        with pytest.raises(ValidationError, match="5"):
            Script(
                script_id="test",
                story_id="test",
                title="Test Script",
                acts=[Act(act_type=ActType.HOOK, scenes=[scene], target_duration_seconds=5.0)],
                total_estimated_duration=5.0,
            )

    def test_script_acts_must_be_in_order(self, sample_script: Script) -> None:
        """Test that script validates act order."""
        # Swap two acts to break order
        acts = sample_script.acts.copy()
        acts[0], acts[1] = acts[1], acts[0]

        with pytest.raises(ValidationError, match="order"):
            Script(
                script_id="test",
                story_id="test",
                title="Test",
                acts=acts,
                total_estimated_duration=55.0,
            )

    def test_script_get_all_scenes(self, sample_script: Script) -> None:
        """Test getting all scenes from script."""
        scenes = sample_script.get_all_scenes()
        assert len(scenes) == 5  # One scene per act
        assert all(isinstance(s, Scene) for s in scenes)

    def test_script_get_characters(self, sample_script: Script) -> None:
        """Test extracting characters from script."""
        characters = sample_script.get_characters()
        assert "Sarah" in characters
        assert "Sister" in characters


class TestAudioModels:
    """Tests for audio data models."""

    def test_word_timestamp_valid(self, sample_word_timestamps: list[WordTimestamp]) -> None:
        """Test valid word timestamp creation."""
        ts = sample_word_timestamps[0]
        assert ts.word == "You"
        assert ts.start < ts.end
        assert 0 <= ts.confidence <= 1

    def test_word_timestamp_duration(self, sample_word_timestamps: list[WordTimestamp]) -> None:
        """Test duration calculation."""
        ts = sample_word_timestamps[0]
        assert ts.duration == ts.end - ts.start

    def test_word_timestamp_overlaps(self) -> None:
        """Test overlap detection."""
        ts = WordTimestamp(word="test", start=1.0, end=2.0, confidence=0.9)
        assert ts.overlaps_with(1.5, 2.5)
        assert ts.overlaps_with(0.5, 1.5)
        assert not ts.overlaps_with(2.5, 3.0)
        assert not ts.overlaps_with(0.0, 0.5)

    def test_audio_segment_valid(self, sample_audio_segment: AudioSegment) -> None:
        """Test valid audio segment creation."""
        assert sample_audio_segment.scene_id == "scene_hook_01"
        assert sample_audio_segment.duration_seconds > 0
        assert sample_audio_segment.file_path.exists()

    def test_audio_segment_get_timestamps_in_range(
        self, sample_audio_segment: AudioSegment
    ) -> None:
        """Test getting timestamps in time range."""
        timestamps = sample_audio_segment.get_timestamps_in_range(0.0, 0.6)
        assert len(timestamps) == 3  # "You", "won't", "believe"

    def test_audio_segment_get_word_at_time(self, sample_audio_segment: AudioSegment) -> None:
        """Test getting word at specific time."""
        word = sample_audio_segment.get_word_at_time(0.7)
        assert word is not None
        assert word.word == "believe"

    def test_audio_project_get_all_timestamps(self, sample_audio_project: AudioProject) -> None:
        """Test getting all timestamps with adjusted times."""
        all_ts = sample_audio_project.get_all_timestamps()
        assert len(all_ts) == 4
        assert all(isinstance(ts, WordTimestamp) for ts in all_ts)


class TestVisualModels:
    """Tests for visual data models."""

    def test_character_consistency_valid(self, tmp_path: Path) -> None:
        """Test valid character consistency creation."""
        ref_path = tmp_path / "sarah.png"
        ref_path.touch()

        char = CharacterConsistency(
            character_name="Sarah",
            reference_image_path=ref_path,
            description="Blonde woman, 25 years old",
            first_appearance_scene_id="scene_hook_01",
        )
        assert char.character_name == "Sarah"
        assert char.reference_image_path.exists()

    def test_image_prompt_build_full_prompt(self, sample_image_prompt: ImagePrompt) -> None:
        """Test building full prompt with character details."""
        char_descriptions = {"Sarah": "Blonde woman, green eyes"}
        full_prompt = sample_image_prompt.build_full_prompt(char_descriptions)

        assert "shocked young woman" in full_prompt.lower()
        assert "Sarah" in full_prompt
        assert sample_image_prompt.style in full_prompt

    def test_visual_asset_aspect_ratio(self, sample_visual_asset: VisualAsset) -> None:
        """Test aspect ratio calculation."""
        ratio = sample_visual_asset.get_aspect_ratio()
        assert ratio == 1080 / 1920
        assert sample_visual_asset.is_vertical()

    def test_visual_project_get_asset_by_scene(
        self, sample_visual_project: VisualProject
    ) -> None:
        """Test retrieving asset by scene ID."""
        asset = sample_visual_project.get_asset_by_scene("scene_hook_01")
        assert asset is not None
        assert asset.scene_id == "scene_hook_01"

        missing = sample_visual_project.get_asset_by_scene("nonexistent")
        assert missing is None


class TestVideoModels:
    """Tests for video data models."""

    def test_effect_config_valid(self) -> None:
        """Test valid effect configuration."""
        effect = EffectConfig(
            effect_type=EffectType.KEN_BURNS,
            params={"zoom_start": 1.0, "zoom_end": 1.2},
        )
        assert effect.effect_type == EffectType.KEN_BURNS
        assert effect.params["zoom_start"] == 1.0

    def test_timeline_segment_duration(self, sample_timeline_segment: TimelineSegment) -> None:
        """Test timeline segment duration calculation."""
        assert sample_timeline_segment.duration == 4.5
        assert sample_timeline_segment.start_time == 0.0
        assert sample_timeline_segment.end_time == 4.5

    def test_timeline_segment_end_before_start_fails(self, tmp_path: Path) -> None:
        """Test that end time must be after start time."""
        img_path = tmp_path / "img.png"
        aud_path = tmp_path / "aud.mp3"
        img_path.touch()
        aud_path.touch()

        with pytest.raises(ValidationError, match="End time"):
            TimelineSegment(
                scene_id="test",
                start_time=10.0,
                end_time=5.0,  # Before start
                visual_asset_path=img_path,
                audio_segment_path=aud_path,
            )

    def test_caption_segment_duration(self) -> None:
        """Test caption duration calculation."""
        caption = CaptionSegment(text="Hello world", start_time=1.0, end_time=2.5)
        assert caption.duration == 1.5

    def test_render_config_resolution_validation(self) -> None:
        """Test resolution validation."""
        config = RenderConfig(resolution="1080x1920")
        width, height = config.get_width_height()
        assert width == 1080
        assert height == 1920

    def test_render_config_invalid_resolution_fails(self) -> None:
        """Test that invalid resolution format fails."""
        with pytest.raises(ValidationError):
            RenderConfig(resolution="invalid")

        with pytest.raises(ValidationError):
            RenderConfig(resolution="0x0")

    def test_render_config_invalid_preset_fails(self) -> None:
        """Test that invalid preset fails."""
        with pytest.raises(ValidationError):
            RenderConfig(preset="invalid_preset")

    def test_video_project_total_duration(self, sample_video_project: VideoProject) -> None:
        """Test total duration calculation."""
        assert sample_video_project.total_duration == 4.5

    def test_video_project_get_segment_at_time(
        self, sample_video_project: VideoProject
    ) -> None:
        """Test getting segment at specific time."""
        segment = sample_video_project.get_segment_at_time(2.0)
        assert segment is not None
        assert segment.scene_id == "scene_hook_01"

        # Time outside range
        segment = sample_video_project.get_segment_at_time(10.0)
        assert segment is None

    def test_video_project_validate_timeline_continuity(
        self, sample_video_project: VideoProject
    ) -> None:
        """Test timeline continuity validation."""
        assert sample_video_project.validate_timeline_continuity()

    def test_video_project_discontinuous_timeline(self, tmp_path: Path) -> None:
        """Test detection of discontinuous timeline."""
        img1 = tmp_path / "img1.png"
        img2 = tmp_path / "img2.png"
        aud1 = tmp_path / "aud1.mp3"
        aud2 = tmp_path / "aud2.mp3"
        for f in [img1, img2, aud1, aud2]:
            f.touch()

        seg1 = TimelineSegment(
            scene_id="s1",
            start_time=0.0,
            end_time=5.0,
            visual_asset_path=img1,
            audio_segment_path=aud1,
        )
        seg2 = TimelineSegment(
            scene_id="s2",
            start_time=10.0,  # Gap from 5.0 to 10.0
            end_time=15.0,
            visual_asset_path=img2,
            audio_segment_path=aud2,
        )

        project = VideoProject(
            project_id="test",
            script_id="test",
            timeline=[seg1, seg2],
        )

        assert not project.validate_timeline_continuity()
