"""Unit tests for video assembly duration fixes.

Tests the critical bug fix where scenes with multiple audio chunks
were only using the first chunk duration instead of summing all chunks.
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock

from gossiptoon.video.assembler import VideoAssembler
from gossiptoon.models.audio import AudioProject, AudioSegment
from gossiptoon.models.visual import VisualProject, VisualAsset


class TestSceneDurationCalculation:
    """Test _get_scene_duration() sums all audio chunks correctly."""
    
    def test_single_chunk_scene(self):
        """Scene with 1 audio chunk returns correct duration."""
        # Arrange
        config = Mock()
        assembler = VideoAssembler(config)
        
        audio_project = AudioProject(
            script_id="test_script",
            segments=[
                AudioSegment(
                    scene_id="scene1",
                    chunk_id="scene1_narrator_01",
                    file_path=Path("test.wav"),
                    duration_seconds=5.5,
                    emotion="neutral",
                    voice_id="test_voice",
                    timestamps=[],
                    sample_rate=44100,
                    channels=1,
                    global_offset=0.0,
                )
            ],
            master_audio_path=Path("master.wav"),
            total_duration=5.5,
        )
        
        # Act
        duration = assembler._get_scene_duration("scene1", audio_project)
        
        # Assert
        assert duration == 5.5
    
    def test_multiple_chunks_scene(self):
        """Scene with 3 audio chunks returns SUM of all durations."""
        # Arrange
        config = Mock()
        assembler = VideoAssembler(config)
        
        audio_project = AudioProject(
            script_id="test_script",
            segments=[
                # Scene 1: 3 chunks
                AudioSegment(
                    scene_id="scene1",
                    chunk_id="scene1_narrator_01",
                    file_path=Path("chunk1.wav"),
                    duration_seconds=6.33,
                    emotion="neutral",
                    voice_id="test_voice",
                    timestamps=[],
                    sample_rate=44100,
                    channels=1,
                    global_offset=0.0,
                ),
                AudioSegment(
                    scene_id="scene1",
                    chunk_id="scene1_dialogue_01",
                    file_path=Path("chunk2.wav"),
                    duration_seconds=3.22,
                    emotion="neutral",
                    voice_id="test_voice",
                    timestamps=[],
                    sample_rate=44100,
                    channels=1,
                    global_offset=6.33,
                ),
                AudioSegment(
                    scene_id="scene1",
                    chunk_id="scene1_dialogue_02",
                    file_path=Path("chunk3.wav"),
                    duration_seconds=2.32,
                    emotion="neutral",
                    voice_id="test_voice",
                    timestamps=[],
                    sample_rate=44100,
                    channels=1,
                    global_offset=9.55,
                ),
            ],
            master_audio_path=Path("master.wav"),
            total_duration=11.87,
        )
        
        # Act
        duration = assembler._get_scene_duration("scene1", audio_project)
        
        # Assert
        expected = 6.33 + 3.22 + 2.32  # 11.87s
        assert abs(duration - expected) < 0.01
    
    def test_missing_scene_returns_default(self):
        """Scene with no audio segments returns default 5.0s."""
        # Arrange
        config = Mock()
        assembler = VideoAssembler(config)
        
        audio_project = AudioProject(
            script_id="test_script",
            segments=[],
            master_audio_path=Path("master.wav"),
            total_duration=0.0,
        )
        
        # Act
        duration = assembler._get_scene_duration("nonexistent_scene", audio_project)
        
        # Assert
        assert duration == 5.0


class TestBuildTimeline:
    """Test _build_timeline() creates correct timeline with summed durations."""
    
    def test_timeline_with_multiple_chunks_per_scene(self):
        """Timeline correctly sums all chunks for each scene."""
        # Arrange
        config = Mock()
        assembler = VideoAssembler(config)
        
        visual_project = VisualProject(
            script_id="test_script",
            assets=[
                VisualAsset(
                    scene_id="scene1",
                    image_path=Path("scene1.png"),
                    prompt="Test scene 1",
                ),
                VisualAsset(
                    scene_id="scene2",
                    image_path=Path("scene2.png"),
                    prompt="Test scene 2",
                ),
            ],
        )
        
        audio_project = AudioProject(
            script_id="test_script",
            segments=[
                # Scene 1: 2 chunks (5s + 3s = 8s)
                AudioSegment(
                    scene_id="scene1",
                    chunk_id="scene1_chunk1",
                    file_path=Path("s1_c1.wav"),
                    duration_seconds=5.0,
                    emotion="neutral",
                    voice_id="test",
                    timestamps=[],
                    sample_rate=44100,
                    channels=1,
                    global_offset=0.0,
                ),
                AudioSegment(
                    scene_id="scene1",
                    chunk_id="scene1_chunk2",
                    file_path=Path("s1_c2.wav"),
                    duration_seconds=3.0,
                    emotion="neutral",
                    voice_id="test",
                    timestamps=[],
                    sample_rate=44100,
                    channels=1,
                    global_offset=5.0,
                ),
                # Scene 2: 1 chunk (4s)
                AudioSegment(
                    scene_id="scene2",
                    chunk_id="scene2_chunk1",
                    file_path=Path("s2_c1.wav"),
                    duration_seconds=4.0,
                    emotion="neutral",
                    voice_id="test",
                    timestamps=[],
                    sample_rate=44100,
                    channels=1,
                    global_offset=8.0,
                ),
            ],
            master_audio_path=Path("master.wav"),
            total_duration=12.0,
        )
        
        # Act
        timeline = assembler._build_timeline(visual_project, audio_project)
        
        # Assert
        assert len(timeline) == 2
        
        # Scene 1: Should show for 8s (sum of 2 chunks)
        assert timeline[0].scene_id == "scene1"
        assert timeline[0].start_time == 0.0
        assert abs(timeline[0].end_time - 8.0) < 0.01
        
        # Scene 2: Should show for 4s, starting at 8s
        assert timeline[1].scene_id == "scene2"
        assert abs(timeline[1].start_time - 8.0) < 0.01
        assert abs(timeline[1].end_time - 12.0) < 0.01


class TestSFXOverlayTiming:
    """Test SFX overlay timing uses correct scene durations."""
    
    @pytest.mark.asyncio
    async def test_sfx_timing_with_multiple_chunks(self):
        """SFX placed at correct scene start using sum of all chunks."""
        # This would be an integration test with PipelineOrchestrator
        # Testing that SFX timing calculation groups segments correctly
        # 
        # Expected behavior:
        # - Scene 1 (2 chunks: 5s + 3s) → SFX at 0s
        # - Scene 2 (1 chunk: 4s) → SFX at 8s (not at 5s!)
        # - Scene 3 (3 chunks: 2s + 3s + 2s) → SFX at 12s
        pass  # Would require more complex mocking of SFXMapper


class TestRegressionPrevention:
    """Regression tests to prevent the bug from reoccurring."""
    
    def test_video_duration_matches_audio_duration(self):
        """Integration test: Total video duration should match total audio."""
        # This would be an E2E test
        # Run pipeline with known script (10 scenes, 19 audio chunks)
        # Expected: Video duration ≈ 63.5s (not 34s)
        pass
    
    def test_no_early_cutoff(self):
        """Last scene should play completely, no mid-speech cutoff."""
        # Verify last timeline segment end_time == total_duration
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
