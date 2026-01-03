"""Unit tests for VisualDetailerAgent."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from gossiptoon.agents.visual_detailer import VisualDetailerAgent
from gossiptoon.models.script import Script, Scene, Act, CharacterProfile
from gossiptoon.models.story import Story
from gossiptoon.core.constants import ActType, EmotionTone

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.api.google_api_key = "test_key"
    return config

@pytest.mark.asyncio
async def test_enrich_script_visuals(mock_config):
    """Test visual enrichment flow."""
    
    # Mock LLM
    mock_llm = MagicMock()
    
    # Input script
    script = Script(
        script_id="test_script",
        story_id="story1",
        title="Test Script Title Must Be Long Enough",
        acts=[
            Act(
                act_type=ActType.HOOK,
                target_duration_seconds=10.0,
                scenes=[
                    Scene(
                        scene_id="s1",
                        order=0,
                        act=ActType.HOOK,
                        narration="First narration text is long enough.",
                        visual_description="A dark room with shadows casting long silhouettes on the floor.",
                        emotion=EmotionTone.NEUTRAL,
                        estimated_duration_seconds=5.0
                    )
                ]
            ),
             Act(act_type=ActType.BUILD, target_duration_seconds=10.0, scenes=[Scene(scene_id="s2", order=0, act=ActType.BUILD, narration="Second narration text is long enough.", visual_description="A very long visual description to satisfy the validator.", emotion=EmotionTone.NEUTRAL, estimated_duration_seconds=5.0)]),
             Act(act_type=ActType.CRISIS, target_duration_seconds=10.0, scenes=[Scene(scene_id="s3", order=0, act=ActType.CRISIS, narration="Third narration text is long enough.", visual_description="A very long visual description to satisfy the validator.", emotion=EmotionTone.NEUTRAL, estimated_duration_seconds=5.0)]),
             Act(act_type=ActType.CLIMAX, target_duration_seconds=10.0, scenes=[Scene(scene_id="s4", order=0, act=ActType.CLIMAX, narration="Fourth narration text is long enough.", visual_description="A very long visual description to satisfy the validator.", emotion=EmotionTone.NEUTRAL, estimated_duration_seconds=5.0)]),
             Act(act_type=ActType.RESOLUTION, target_duration_seconds=10.0, scenes=[Scene(scene_id="s5", order=0, act=ActType.RESOLUTION, narration="Fifth narration text is long enough.", visual_description="A very long visual description to satisfy the validator.", emotion=EmotionTone.NEUTRAL, estimated_duration_seconds=5.0)]),
        ],
        total_estimated_duration=50.0
    )
    
    # Enriched script (Mock output)
    enriched_script = script.model_copy(deep=True)
    enriched_script.acts[0].scenes[0].visual_description = "A grim, dimly lit room with harsh shadows casting across the floor."

    # Setup mock
    mock_llm.with_structured_output.return_value.ainvoke = AsyncMock(return_value=enriched_script)
    
    with patch("gossiptoon.agents.visual_detailer.ChatGoogleGenerativeAI", return_value=mock_llm):
        agent = VisualDetailerAgent(mock_config)
        agent.llm = mock_llm  # Inject manually as init creates new instance
        
        result = await agent.enrich_script_visuals(
            script,
            Story(
                id="1", 
                title="Test Story Title Must Be Long Enough", 
                url="http://example.com", 
                content="This is a very long content string to satisfy the minimum length requirement of 100 characters properly. " * 5,
                category="other",
                metadata={
                    "video_type": "short",
                    "author": "author1",
                    "upvotes": 100,
                    "num_comments": 10,
                    "created_utc": 1234567890,
                    "url": "http://example.com",
                    "post_id": "post123",
                    "subreddit": "subreddit"
                },
                viral_score=8.5
            )
        )
        
        assert result.acts[0].scenes[0].visual_description == "A grim, dimly lit room with harsh shadows casting across the floor."
