"""Unit tests for audio pipeline components."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gossiptoon.audio.audio_processor import AudioProcessor
from gossiptoon.audio.elevenlabs_client import ElevenLabsClient
from gossiptoon.audio.generator import AudioGenerator
from gossiptoon.audio.whisper import WhisperTimestampExtractor
from gossiptoon.core.constants import EmotionTone
from gossiptoon.models.audio import WordTimestamp


class TestElevenLabsClient:
    """Tests for ElevenLabs TTS client."""

    def test_client_initialization(self) -> None:
        """Test client initialization."""
        client = ElevenLabsClient(api_key="test_key")
        assert client.api_key == "test_key"
        assert client._client is None

    def test_get_voice_settings_with_emotion(self) -> None:
        """Test voice settings for emotion tones."""
        client = ElevenLabsClient(api_key="test_key")

        settings = client._get_voice_settings(EmotionTone.SHOCKED)
        assert "stability" in settings
        assert "similarity_boost" in settings
        assert "style" in settings

    def test_get_voice_settings_neutral(self) -> None:
        """Test default voice settings."""
        client = ElevenLabsClient(api_key="test_key")

        settings = client._get_voice_settings(None)
        assert settings["stability"] == 0.5
        assert settings["similarity_boost"] == 0.75

    def test_estimate_duration(self) -> None:
        """Test audio duration estimation."""
        client = ElevenLabsClient(api_key="test_key")

        text = "This is a test sentence with ten words total."
        duration = client.estimate_duration(text, "test_voice")

        # ~10 words / 2.5 words per second * 1.1 buffer
        expected = (10 / 2.5) * 1.1
        assert abs(duration - expected) < 0.5

    @pytest.mark.asyncio
    async def test_generate_speech_with_mock(self, tmp_path: Path) -> None:
        """Test speech generation with mocked API."""
        client = ElevenLabsClient(api_key="test_key")

        # Mock the ElevenLabs SDK
        mock_audio_data = [b"fake_audio_chunk_1", b"fake_audio_chunk_2"]

        with patch.object(client, "_init_client") as mock_init:
            mock_elevenlabs = MagicMock()
            mock_elevenlabs.generate.return_value = iter(mock_audio_data)
            mock_init.return_value = mock_elevenlabs

            output_path = tmp_path / "test_output.mp3"

            result_path = await client.generate_speech(
                text="Hello world",
                voice_id="test_voice",
                emotion=EmotionTone.HAPPY,
                output_path=output_path,
            )

            assert result_path == output_path
            assert output_path.exists()

            # Verify audio was written
            with open(output_path, "rb") as f:
                content = f.read()
                assert content == b"fake_audio_chunk_1fake_audio_chunk_2"


class TestWhisperTimestampExtractor:
    """Tests for Whisper timestamp extraction."""

    def test_extractor_initialization(self) -> None:
        """Test extractor initialization."""
        extractor = WhisperTimestampExtractor(model_name="base")
        assert extractor.model_name == "base"
        assert extractor._model is None

    def test_get_total_duration(self) -> None:
        """Test total duration calculation from timestamps."""
        extractor = WhisperTimestampExtractor()

        timestamps = [
            WordTimestamp(word="Hello", start=0.0, end=0.5, confidence=0.9),
            WordTimestamp(word="world", start=0.5, end=1.0, confidence=0.9),
            WordTimestamp(word="test", start=1.0, end=1.8, confidence=0.9),
        ]

        duration = extractor.get_total_duration(timestamps)
        assert duration == 1.8

    def test_get_text_from_timestamps(self) -> None:
        """Test text reconstruction from timestamps."""
        extractor = WhisperTimestampExtractor()

        timestamps = [
            WordTimestamp(word="Hello", start=0.0, end=0.5, confidence=0.9),
            WordTimestamp(word="world", start=0.5, end=1.0, confidence=0.9),
        ]

        text = extractor.get_text(timestamps)
        assert text == "Hello world"

    def test_split_by_duration(self) -> None:
        """Test splitting timestamps into chunks."""
        extractor = WhisperTimestampExtractor()

        timestamps = [
            WordTimestamp(word=f"word{i}", start=i * 0.5, end=(i + 1) * 0.5, confidence=0.9)
            for i in range(10)
        ]

        chunks = extractor.split_by_duration(timestamps, max_duration=2.0)

        assert len(chunks) > 1
        for chunk in chunks:
            duration = chunk[-1].end - chunk[0].start
            assert duration <= 2.0

    def test_align_to_scenes(self) -> None:
        """Test aligning timestamps to scene boundaries."""
        extractor = WhisperTimestampExtractor()

        timestamps = [
            WordTimestamp(word=f"word{i}", start=i * 0.5, end=(i + 1) * 0.5, confidence=0.9)
            for i in range(20)
        ]

        scene_durations = [3.0, 4.0, 3.0]  # 10 seconds total

        scene_timestamps = extractor.align_to_scenes(timestamps, scene_durations)

        assert len(scene_timestamps) == 3

        # Check that words are distributed across scenes
        total_words = sum(len(scene_words) for scene_words in scene_timestamps)
        assert total_words <= len(timestamps)


class TestAudioProcessor:
    """Tests for audio processing utilities."""

    def test_processor_initialization(self) -> None:
        """Test processor initialization."""
        processor = AudioProcessor()
        assert processor is not None

    def test_check_pydub_availability(self) -> None:
        """Test pydub availability check."""
        processor = AudioProcessor()
        # Just verify it returns a boolean
        assert isinstance(processor._pydub_available, bool)

    @pytest.mark.asyncio
    async def test_concatenate_with_ffmpeg_mock(self, tmp_path: Path) -> None:
        """Test FFmpeg concatenation with mock."""
        processor = AudioProcessor()

        # Create fake audio files
        audio1 = tmp_path / "audio1.mp3"
        audio2 = tmp_path / "audio2.mp3"
        audio1.write_bytes(b"fake_audio_1")
        audio2.write_bytes(b"fake_audio_2")

        output_path = tmp_path / "output.mp3"

        # Mock FFmpeg subprocess
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            # Force use of FFmpeg by setting pydub unavailable
            processor._pydub_available = False

            result = await processor.concatenate_audio_files(
                [audio1, audio2], output_path
            )

            assert mock_run.called
            # Verify FFmpeg was called with concat
            call_args = mock_run.call_args[0][0]
            assert "ffmpeg" in call_args
            assert "-f" in call_args
            assert "concat" in call_args


class TestAudioGenerator:
    """Tests for audio generator orchestrator."""

    @pytest.mark.asyncio
    async def test_generator_initialization(self, mock_config) -> None:
        """Test generator initialization."""
        generator = AudioGenerator(mock_config)

        assert generator.config == mock_config
        assert generator.tts_client is not None
        assert generator.whisper is not None
        assert generator.processor is not None

    @pytest.mark.asyncio
    async def test_generate_scene_audio_with_mocks(
        self, mock_config, sample_scene, tmp_path: Path
    ) -> None:
        """Test scene audio generation with mocked components."""
        generator = AudioGenerator(mock_config)

        # Mock TTS client
        mock_tts = AsyncMock()
        audio_path = tmp_path / "scene_audio.mp3"
        audio_path.write_bytes(b"fake_audio")
        mock_tts.generate_speech.return_value = audio_path

        generator.tts_client = mock_tts

        # Mock Whisper
        mock_timestamps = [
            WordTimestamp(word="You", start=0.0, end=0.2, confidence=0.9),
            WordTimestamp(word="won't", start=0.2, end=0.5, confidence=0.9),
            WordTimestamp(word="believe", start=0.5, end=0.9, confidence=0.9),
        ]

        with patch.object(
            generator.whisper, "extract_timestamps", new_callable=AsyncMock
        ) as mock_whisper:
            mock_whisper.return_value = mock_timestamps

            # Mock audio duration
            with patch.object(
                generator.processor, "get_audio_duration", return_value=0.9
            ):
                segment = await generator._generate_scene_audio(
                    sample_scene, "test_voice"
                )

                assert segment.scene_id == sample_scene.scene_id
                assert segment.duration_seconds == 0.9
                assert len(segment.timestamps) == 3
                assert segment.voice_id == "test_voice"

    @pytest.mark.asyncio
    async def test_generate_audio_project_with_mocks(
        self, mock_config, sample_script
    ) -> None:
        """Test full audio project generation with mocks."""
        generator = AudioGenerator(mock_config)

        # Mock scene audio generation
        mock_segments = []
        for scene in sample_script.get_all_scenes():
            segment = MagicMock()
            segment.scene_id = scene.scene_id
            segment.duration_seconds = scene.estimated_duration_seconds
            segment.file_path = Path(f"/fake/{scene.scene_id}.mp3")
            segment.timestamps = []
            mock_segments.append(segment)

        with patch.object(
            generator, "_generate_scene_audio", new_callable=AsyncMock
        ) as mock_gen:
            mock_gen.side_effect = mock_segments

            # Mock master audio creation
            with patch.object(
                generator, "_create_master_audio", new_callable=AsyncMock
            ) as mock_master:
                mock_master.return_value = Path("/fake/master.mp3")

                # Mock save
                with patch.object(generator, "_save_audio_project"):
                    audio_project = await generator.generate_audio_project(
                        sample_script
                    )

                    assert audio_project.script_id == sample_script.script_id
                    assert len(audio_project.segments) == len(
                        sample_script.get_all_scenes()
                    )
                    assert audio_project.total_duration > 0
