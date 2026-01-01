"""Unit tests for ScriptWriterAgent with Webtoon enhancements."""

import logging
from unittest.mock import MagicMock, patch

import pytest
from gossiptoon.agents.script_writer import ScriptWriterAgent
from gossiptoon.core.config import ConfigManager
from gossiptoon.models.audio import AudioChunk, AudioChunkType
from gossiptoon.models.script import Act, Scene, Script
from gossiptoon.core.constants import ActType, EmotionTone

@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    config = MagicMock()
    config.api.google_api_key = "fake_key"
    config.script.webtoon_mode = True
    config.script.max_dialogue_chars = 100
    config.script.min_dialogue_chars = 5
    config.script.max_narration_chars = 200
    config.scripts_dir = MagicMock()
    return config

@pytest.fixture
def agent(mock_config):
    """Create ScriptWriterAgent instance."""
    with patch("gossiptoon.agents.script_writer.ChatGoogleGenerativeAI"):
        with patch("gossiptoon.agents.script_writer.ScriptEvaluator"):
            return ScriptWriterAgent(mock_config)

def test_create_prompt_webtoon_mode(agent):
    """Test that webtoon mode uses the correct prompt."""
    agent.config.script.webtoon_mode = True
    agent.config.script.max_dialogue_chars = 150
    
    prompt = agent._create_prompt()
    
    messages = prompt.format_messages(
        title="Test", content="Content", category="AITA", format_instructions=""
    )
    system_message = messages[0].content
    
    assert "Korean Webtoon scriptwriter" in system_message
    assert "MAX 150 characters" in system_message
    assert "audio_chunks" in system_message

def test_create_prompt_legacy_mode(agent):
    """Test that legacy mode uses the legacy prompt."""
    agent.config.script.webtoon_mode = False
    
    prompt = agent._create_prompt()
    
    messages = prompt.format_messages(
        title="Test", content="Content", category="AITA", format_instructions=""
    )
    system_message = messages[0].content
    
    assert "expert scriptwriter for YouTube Shorts" in system_message
    assert "Narrated story with minimal dialogue" in system_message
    assert "Korean Webtoon conversation" not in system_message

def test_validate_audio_chunks_limits(agent, caplog):
    """Test character limit validation for webtoon audio chunks."""
    # Create a scene with a long dialogue chunk
    long_text = "A" * 200 # 200 chars, limit is 100
    
    chunk = AudioChunk(
        chunk_id="test_chunk",
        chunk_type=AudioChunkType.DIALOGUE,
        speaker_id="TestChar",
        text=long_text,
        director_notes="test notes",
        estimated_duration=5.0
    )
    
    scene = Scene(
        scene_id="test_scene",
        act=ActType.HOOK,
        order=0,
        audio_chunks=[chunk],
        visual_description="This is a valid visual description with enough words to pass validation.",
        emotion=EmotionTone.NEUTRAL,
        estimated_duration_seconds=5.0,
        bubble_metadata=[]
    )
    
    script = MagicMock(spec=Script)
    script.get_all_scenes.return_value = [scene]
    
    with caplog.at_level(logging.WARNING):
        agent._validate_audio_chunks(script)
        
    assert "text is long" in caplog.text
    assert "(200 chars, max 100)" in caplog.text

def test_validate_legacy_limits(agent, caplog):
    """Test character limit validation for legacy narration."""
    agent.config.script.webtoon_mode = False
    
    long_narration = "word " * 50 # 50 words, approx 250 chars. Config limit 200 chars approx 40 words.
    
    long_narration = "word " * 50 # 50 words
    
    scene = MagicMock(spec=Scene)
    scene.scene_id = "test_scene_legacy"
    scene.narration = long_narration
    scene.is_webtoon_style.return_value = False
    
    # Ensure it doesn't look like webtoon style
    scene.audio_chunks = None 
    
    script = MagicMock(spec=Script)
    script.get_all_scenes.return_value = [scene]
    
    with caplog.at_level(logging.WARNING):
        agent._validate_audio_chunks(script)
        
    assert "narration is long" in caplog.text

def test_save_readable_script_webtoon(agent, tmp_path):
    """Test saving readable script in webtoon format."""
    output_path = tmp_path / "test_readable.txt"
    
    chunk = AudioChunk(
        chunk_id="c1",
        chunk_type=AudioChunkType.DIALOGUE,
        speaker_id="Mom",
        speaker_gender="female",
        text="Hello world",
        director_notes="warm greeting",
        estimated_duration=3.0,
        bubble_position="top-left",
        bubble_style="speech"
    )
    
    scene = Scene(
        scene_id="s1",
        act=ActType.HOOK,
        order=0,
        audio_chunks=[chunk],
        panel_layout="Close up on Mom smiling with warm background lighting.",
        bubble_metadata=[],
        visual_description="Mom smiling nicely in a close-up shot with warm lighting.",
        emotion=EmotionTone.HAPPY,
        estimated_duration_seconds=3.0,
        characters_present=["Mom"]
    )
    
    act = MagicMock(spec=Act)
    act.act_type = ActType.HOOK
    act.target_duration_seconds = 5.0
    act.scenes = [scene]
    
    script = MagicMock(spec=Script)
    script.script_id = "test_script"
    script.story_id = "story_1"
    script.title = "Test Story"
    script.acts = [act]
    script.total_estimated_duration = 5.0
    script.get_characters.return_value = ["Mom"]
    
    agent._save_readable_script(script, output_path)
    
    content = output_path.read_text()
    
    assert "Script: Test Story" in content
    assert "PANEL LAYOUT:" in content
    assert "Close up on Mom" in content
    assert "AUDIO CHUNKS (1):" in content
    assert "[1] DIALOGUE - Mom (female)" in content
    assert "Director: warm greeting" in content
    assert "Bubble: top-left (speech)" in content
