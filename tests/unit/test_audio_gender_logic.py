"""Unit tests for AudioGenerator gender logic."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from gossiptoon.audio.generator import AudioGenerator
from gossiptoon.audio.google_tts_client import GoogleTTSClient
from gossiptoon.models.audio import AudioChunk, AudioChunkType
from gossiptoon.models.script import Script, CharacterProfile

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.audio.tts_provider = "google"
    config.audio.google_tts_model = "model"
    config.audio.google_tts_voice = "default_voice"
    config.api.google_api_key = "test_key"
    return config

@pytest.fixture
def mock_tts_client():
    client = MagicMock(spec=GoogleTTSClient)
    client.generate_speech = AsyncMock(return_value="path/to/audio.mp3")
    client.get_recommended_voice_for_gender = MagicMock(return_value="gender_voice")
    return client

@pytest.mark.asyncio
async def test_select_voice_fallback_to_map(mock_config, mock_tts_client):
    """Test that voice selection falls back to gender map if speaker_gender is None."""
    
    generator = AudioGenerator(mock_config, tts_client=mock_tts_client)
    
    # Scenario: AudioChunk has missing gender
    chunk = AudioChunk(
        chunk_id="chk1",
        chunk_type=AudioChunkType.DIALOGUE,
        speaker_id="John",
        speaker_gender=None, # Missing
        text="Hello",
        director_notes="Calm voice with a gentle tone.",
        estimated_duration=1.0
    )
    
    gender_map = {"John": "male", "Jane": "female"}
    
    # Test selection
    voice_id = generator._select_voice_for_speaker(
        speaker_id=chunk.speaker_id,
        speaker_gender=chunk.speaker_gender,
        chunk_type=chunk.chunk_type,
        gender_map=gender_map
    )
    
    # Verify it used the map ("male")
    mock_tts_client.get_recommended_voice_for_gender.assert_called_with(
        gender="male", 
        index=hash("John") % 5
    )

@pytest.mark.asyncio
async def test_select_voice_defaults_to_female_if_unknown(mock_config, mock_tts_client):
    """Test defaults to female if character not in map."""
    
    generator = AudioGenerator(mock_config, tts_client=mock_tts_client)
    
    chunk = AudioChunk(
        chunk_id="chk1",
        chunk_type=AudioChunkType.DIALOGUE,
        speaker_id="UnknownChar",
        speaker_gender=None,
        text="Hello",
        director_notes="Calm voice with a gentle tone.",
        estimated_duration=1.0
    )
    
    gender_map = {"John": "male"}
    
    voice_id = generator._select_voice_for_speaker(
        speaker_id=chunk.speaker_id,
        speaker_gender=chunk.speaker_gender,
        chunk_type=chunk.chunk_type,
        gender_map=gender_map
    )
    
    # Verify it defaulted to "female"
    mock_tts_client.get_recommended_voice_for_gender.assert_called_with(
        gender="female", 
        index=hash("UnknownChar") % 5
    )
