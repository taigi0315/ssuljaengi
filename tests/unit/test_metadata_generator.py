"""Unit tests for MetadataGeneratorAgent."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from gossiptoon.agents.metadata_generator import MetadataGeneratorAgent
from gossiptoon.models.story import Story, RedditPostMetadata, StoryCategory
from gossiptoon.models.script import Script, Act, Scene
from gossiptoon.models.metadata import YouTubeMetadata

@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    config = MagicMock()
    config.api.google_api_key = "fake_key"
    config.outputs_dir = MagicMock()
    return config

from datetime import datetime

@pytest.fixture
def sample_story():
    """Create a sample story."""
    return Story(
        id="story_123",
        title="I refused to drive my husband home from the hospital",
        content="Long story about a husband who demanded a ride from the hospital during an important work meeting. This is a detailed account of what happened and why I made the decision I did.",
        category=StoryCategory.RELATIONSHIP,
        viral_score=95.0,  # Missing field
        metadata=RedditPostMetadata(
            post_id="p1", 
            subreddit="AmItheAsshole", 
            author="wife123", 
            upvotes=5000, 
            num_comments=100, 
            created_utc=datetime.utcnow(), # Cannot be None
            url="http://reddit.com"
        )
    )

@pytest.fixture
def sample_script():
    """Create a sample script using Mocks to bypass strict Pydantic rules."""
    hook_scene = MagicMock(spec=Scene)
    hook_scene.audio_chunks = []
    hook_scene.narration = "I left him there. Was I wrong? Everyone is blowing up my phone."
    
    act = MagicMock()
    act.scenes = [hook_scene]
    
    script = MagicMock(spec=Script)
    script.acts = [act]
    return script

@pytest.mark.asyncio
async def test_generate_metadata_webtoon_hook(mock_config, sample_story):
    """Test hook extraction from AudioChunks (Webtoon style)."""
    from gossiptoon.models.audio import AudioChunk, AudioChunkType
    from gossiptoon.core.constants import EmotionTone
    
    # Create Webtoon script with chunks
    chunk1 = AudioChunk(chunk_id="c1", chunk_type=AudioChunkType.DIALOGUE, text="You left me!", speaker_id="Husband", speaker_gender="male", director_notes="angry shouting voice with high intensity", estimated_duration=2.0)
    chunk2 = AudioChunk(chunk_id="c2", chunk_type=AudioChunkType.DIALOGUE, text="You deserved it!", speaker_id="Wife", speaker_gender="female", director_notes="angry shouting voice with high intensity", estimated_duration=2.0)
    
    # Use real Scene but provide all required fields
    hook_scene = Scene(
        scene_id="hook_1",
        order=0,
        audio_chunks=[chunk1, chunk2],
        estimated_duration_seconds=5.0,
        visual_description="A tense argument between husband and wife.",
        emotion=EmotionTone.ANGRY,
        characters_present=["Husband", "Wife"]
    )
    
    # Mock Script to bypass 5-act validation
    script = MagicMock(spec=Script)
    script.acts = [MagicMock(scenes=[hook_scene])]
    
    with patch("gossiptoon.agents.metadata_generator.ChatGoogleGenerativeAI") as MockLLM:
        mock_instance = MockLLM.return_value
        mock_structured = MagicMock()
        mock_instance.with_structured_output.return_value = mock_structured
        mock_structured.ainvoke = AsyncMock(return_value=YouTubeMetadata(title="t", description="d", tags=["t"]))
        
        with patch("gossiptoon.agents.metadata_generator.ChatPromptTemplate") as MockPrompt:
             mock_prompt_instance = MockPrompt.from_messages.return_value
             mock_prompt_instance.ainvoke = AsyncMock(return_value="Prompt")
             
             agent = MetadataGeneratorAgent(mock_config)
             await agent.generate_metadata(sample_story, script)
             
             # Check if chunks were combined
             call_args = mock_prompt_instance.ainvoke.call_args[0][0]
             assert call_args["hook_content"] == "You left me! You deserved it!"
