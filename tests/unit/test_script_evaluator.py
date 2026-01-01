"""Unit tests for ScriptEvaluator agent."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from gossiptoon.agents.script_evaluator import ScriptEvaluator
from gossiptoon.models.story import Story
from gossiptoon.models.script import Script, Act, Scene, ActType, EmotionTone
from gossiptoon.core.config import ConfigManager

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.api.google_api_key = "fake_key"
    config.scripts_dir = MagicMock()
    # Mock parent because LLMDebugger uses config.scripts_dir.parent
    config.scripts_dir.parent = MagicMock()
    return config

@pytest.fixture
def mock_llm_chain():
    with patch("gossiptoon.agents.script_evaluator.ChatGoogleGenerativeAI") as MockLLM:
        mock_instance = MockLLM.return_value
        # Mock structured output
        mock_structured = MagicMock()
        mock_instance.with_structured_output.return_value = mock_structured
        
        # Mock the chain invocation
        # Chain is prompt | structured_llm
        # But we split it in code: prompt.ainvoke, then structured_llm.ainvoke
        
        yield mock_instance, mock_structured

from gossiptoon.models.story import RedditPostMetadata
from gossiptoon.core.constants import StoryCategory
from datetime import datetime

@pytest.fixture
def sample_story():
    metadata = RedditPostMetadata(
        post_id="p123",
        subreddit="test_sub",
        author="test_author",
        upvotes=100,
        num_comments=10,
        created_utc=datetime.utcnow(),
        url="https://reddit.com/r/test/comments/p123",
        flair="test"
    )
    return Story(
        id="test_story",
        title="Test Title" + "A" * 10, # min_length=10
        content="Test Content" + " " * 100, # min_length=100
        category=StoryCategory.OTHER,
        metadata=metadata,
        viral_score=90.0
    )

@pytest.mark.asyncio
async def test_evaluate_and_fix_success(mock_config, mock_llm_chain, sample_story):
    """Test successful script evaluation."""
    mock_llm, mock_structured = mock_llm_chain
    
    # Create valid dummy scenes
    dummy_scene = Scene(
        scene_id="s1",
        order=0,
        narration="Narration must be long enough.", 
        visual_description="Visual description must be at least five words long.",
        emotion=EmotionTone.NEUTRAL,
        estimated_duration_seconds=3.0,
        characters_present=["Char1"]
    )
    
    # Mock return script
    expected_script = Script(
        title="Test Title Long Enough", # > 10 chars
        story_id="test_story",
        script_id="script_123",
        acts=[
             Act(act_type=ActType.HOOK, scene_ids=["s1"], target_duration_seconds=3.0, scenes=[dummy_scene]),
             Act(act_type=ActType.BUILD, scene_ids=["s2"], target_duration_seconds=10.0, scenes=[dummy_scene]),
             Act(act_type=ActType.CRISIS, scene_ids=["s3"], target_duration_seconds=15.0, scenes=[dummy_scene]),
             Act(act_type=ActType.CLIMAX, scene_ids=["s4"], target_duration_seconds=15.0, scenes=[dummy_scene]),
             Act(act_type=ActType.RESOLUTION, scene_ids=["s5"], target_duration_seconds=10.0, scenes=[dummy_scene]),
        ],
        total_estimated_duration=53.0,
        characters=["Char1"]
    )
    
    mock_structured.ainvoke = AsyncMock(return_value=expected_script)
    
    evaluator = ScriptEvaluator(mock_config)
    
    # Needs to mock ChatPromptTemplate.from_messages to avoid real chaining issues during test?
    # Our code does prompt.ainvoke separately.
    # The real prompt is created inside the method. using ChatPromptTemplate.from_messages
    # We should mock prompt.ainvoke result.
    
    with patch("gossiptoon.agents.script_evaluator.ChatPromptTemplate") as MockPrompt:
         mock_prompt_instance = MockPrompt.from_messages.return_value
         mock_prompt_instance.ainvoke = AsyncMock(return_value="Formatted Prompt")
         
         result = await evaluator.evaluate_and_fix("Draft Script Content", sample_story)
         
         assert result == expected_script
         mock_prompt_instance.ainvoke.assert_called_once()
         mock_structured.ainvoke.assert_called_once_with("Formatted Prompt")

@pytest.mark.asyncio
async def test_evaluate_and_fix_failure(mock_config, mock_llm_chain, sample_story):
    """Test script evaluation failure."""
    mock_llm, mock_structured = mock_llm_chain
    mock_structured.ainvoke = AsyncMock(side_effect=Exception("LLM Error"))
    
    evaluator = ScriptEvaluator(mock_config)
    
    with patch("gossiptoon.agents.script_evaluator.ChatPromptTemplate") as MockPrompt:
         mock_prompt_instance = MockPrompt.from_messages.return_value
         mock_prompt_instance.ainvoke = AsyncMock(return_value="Formatted Prompt")
         
         with pytest.raises(Exception, match="LLM Error"):
             await evaluator.evaluate_and_fix("Draft", sample_story)
