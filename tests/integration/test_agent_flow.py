"""Integration tests for agent workflows."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import HttpUrl

from gossiptoon.agents.script_writer import ScriptWriterAgent
from gossiptoon.agents.state import WorkflowBuilder, create_initial_state
from gossiptoon.agents.story_finder import StoryFinderAgent
from gossiptoon.agents.tools.reddit_search import RedditPost
from gossiptoon.core.config import ConfigManager
from gossiptoon.core.constants import ActType, EmotionTone, StoryCategory
from gossiptoon.models.script import Act, Scene, Script
from gossiptoon.models.story import RedditPostMetadata, Story


@pytest.fixture
def mock_config(tmp_path: Path) -> ConfigManager:
    """Create mock configuration."""
    # Create temporary .env file
    env_file = tmp_path / ".env"
    env_file.write_text(
        """
OPENAI_API_KEY=test_openai_key
GOOGLE_API_KEY=test_google_key
ELEVENLABS_API_KEY=test_elevenlabs_key
OUTPUT_DIR={}
""".format(
            tmp_path / "outputs"
        )
    )

    return ConfigManager(env_file=env_file)


@pytest.fixture
def sample_reddit_post() -> RedditPost:
    """Create sample Reddit post for testing."""
    return RedditPost(
        post_id="test123",
        title="AITA for refusing to attend my sister's wedding?",
        content="So this happened last week. My sister (28F) is getting married to her fiancé (30M). "
        "I (25F) have always been close with my sister, but recently things have been tense. "
        "She asked me to be her maid of honor, but then uninvited me after an argument. "
        "Now she wants me back as a regular guest. I told her I won't be attending at all. "
        "My family says I'm being petty and should just go. AITA?",
        subreddit="AmItheAsshole",
        author="throwaway123",
        upvotes=15000,
        num_comments=892,
        created_utc=datetime.utcnow(),
        url="https://reddit.com/r/AmItheAsshole/comments/test123",
        flair="Not the A-hole",
    )


@pytest.fixture
def sample_script_json() -> dict:
    """Create sample script JSON response from LLM."""
    return {
        "script_id": "script_test",
        "story_id": "story_test",
        "title": "The Wedding Disaster",
        "acts": [
            {
                "act_type": "hook",
                "target_duration_seconds": 4.0,
                "scenes": [
                    {
                        "scene_id": "scene_hook_01",
                        "act": "hook",
                        "order": 0,
                        "narration": "You won't believe what my sister did at her own wedding.",
                        "emotion": "shocked",
                        "visual_description": "Shocked young woman in living room, hands on face",
                        "characters_present": ["narrator"],
                        "estimated_duration_seconds": 4.0,
                    }
                ],
            },
            {
                "act_type": "build",
                "target_duration_seconds": 10.0,
                "scenes": [
                    {
                        "scene_id": "scene_build_01",
                        "act": "build",
                        "order": 0,
                        "narration": "My sister and I were always close, until she met her fiancé.",
                        "emotion": "sad",
                        "visual_description": "Two sisters hugging in warm family photo",
                        "characters_present": ["narrator", "sister"],
                        "estimated_duration_seconds": 10.0,
                    }
                ],
            },
            {
                "act_type": "crisis",
                "target_duration_seconds": 15.0,
                "scenes": [
                    {
                        "scene_id": "scene_crisis_01",
                        "act": "crisis",
                        "order": 0,
                        "narration": "She uninvited me as maid of honor after one stupid argument.",
                        "emotion": "angry",
                        "visual_description": "Tense confrontation between sisters",
                        "characters_present": ["narrator", "sister"],
                        "estimated_duration_seconds": 15.0,
                    }
                ],
            },
            {
                "act_type": "climax",
                "target_duration_seconds": 15.0,
                "scenes": [
                    {
                        "scene_id": "scene_climax_01",
                        "act": "climax",
                        "order": 0,
                        "narration": "When she asked me to come as a guest, I finally snapped.",
                        "emotion": "dramatic",
                        "visual_description": "Intense emotional confrontation scene",
                        "characters_present": ["narrator", "sister"],
                        "estimated_duration_seconds": 15.0,
                    }
                ],
            },
            {
                "act_type": "resolution",
                "target_duration_seconds": 11.0,
                "scenes": [
                    {
                        "scene_id": "scene_resolution_01",
                        "act": "resolution",
                        "order": 0,
                        "narration": "I told her I won't be attending. Best decision ever.",
                        "emotion": "neutral",
                        "visual_description": "Woman looking relieved and confident",
                        "characters_present": ["narrator"],
                        "estimated_duration_seconds": 11.0,
                    }
                ],
            },
        ],
        "total_estimated_duration": 55.0,
        "target_audience": "18-35 years old",
        "content_warnings": [],
    }


class TestStoryFinderAgent:
    """Tests for Story Finder Agent."""

    @pytest.mark.asyncio
    async def test_convert_reddit_post_to_story(
        self, mock_config: ConfigManager, sample_reddit_post: RedditPost
    ) -> None:
        """Test converting Reddit post to Story model."""
        agent = StoryFinderAgent(mock_config)

        story = agent._convert_to_story(sample_reddit_post, virality_score=85.5)

        assert story.title == sample_reddit_post.title
        assert story.content == sample_reddit_post.content
        assert story.category == StoryCategory.AITA
        assert story.viral_score == 85.5
        assert story.metadata.post_id == sample_reddit_post.post_id
        assert story.metadata.upvotes == sample_reddit_post.upvotes

    def test_categorize_story_aita(
        self, mock_config: ConfigManager, sample_reddit_post: RedditPost
    ) -> None:
        """Test AITA story categorization."""
        agent = StoryFinderAgent(mock_config)

        category = agent._categorize_story(sample_reddit_post)

        assert category == StoryCategory.AITA

    @pytest.mark.asyncio
    async def test_find_story_with_mocked_reddit(
        self, mock_config: ConfigManager, sample_reddit_post: RedditPost
    ) -> None:
        """Test finding story with mocked Reddit API."""
        agent = StoryFinderAgent(mock_config)

        # Mock Reddit search to return sample post
        with patch.object(
            agent.reddit_tool,
            "search_multiple_subreddits",
            new_callable=AsyncMock,
        ) as mock_search:
            mock_search.return_value = [sample_reddit_post]

            story = await agent.find_story(min_virality=50.0)

            assert story is not None
            assert story.category == StoryCategory.AITA
            assert story.viral_score >= 50.0

            # Verify story was saved
            assert (mock_config.stories_dir / f"{story.id}.json").exists()


class TestScriptWriterAgent:
    """Tests for Script Writer Agent."""

    @pytest.mark.asyncio
    async def test_write_script_with_mocked_llm(
        self, mock_config: ConfigManager, sample_story: Story, sample_script_json: dict
    ) -> None:
        """Test script writing with mocked LLM response."""
        agent = ScriptWriterAgent(mock_config)

        # Mock OpenAI LLM response
        mock_response = Script.model_validate(sample_script_json)

        with patch.object(agent.llm, "ainvoke", new_callable=AsyncMock) as mock_llm:
            # Return a mock AIMessage with the content
            mock_message = MagicMock()
            mock_message.content = json.dumps(sample_script_json)
            mock_llm.return_value = mock_message

            # Also patch the parser to return the validated script
            with patch.object(agent.parser, "parse", return_value=mock_response):
                script = await agent.write_script(sample_story)

                assert script is not None
                assert len(script.acts) == 5
                assert script.acts[0].act_type == ActType.HOOK
                assert script.acts[-1].act_type == ActType.RESOLUTION
                assert 50 <= script.total_estimated_duration <= 65

    def test_validate_five_acts(
        self, mock_config: ConfigManager, sample_script: Script
    ) -> None:
        """Test five-act validation."""
        agent = ScriptWriterAgent(mock_config)

        # Should not raise
        agent._validate_five_acts(sample_script)

    def test_validate_five_acts_wrong_order_fails(
        self, mock_config: ConfigManager, sample_script: Script
    ) -> None:
        """Test that wrong act order fails validation."""
        agent = ScriptWriterAgent(mock_config)

        # Swap acts to break order
        sample_script.acts[0], sample_script.acts[1] = (
            sample_script.acts[1],
            sample_script.acts[0],
        )

        with pytest.raises(Exception, match="order"):
            agent._validate_five_acts(sample_script)

    def test_validate_characters(
        self, mock_config: ConfigManager, sample_script: Script
    ) -> None:
        """Test character validation."""
        agent = ScriptWriterAgent(mock_config)

        # Should not raise
        agent._validate_characters(sample_script)

        characters = sample_script.get_characters()
        assert len(characters) <= 5


class TestWorkflowState:
    """Tests for LangGraph workflow state."""

    def test_create_initial_state(self) -> None:
        """Test creating initial workflow state."""
        state = create_initial_state()

        assert state["current_step"] == "init"
        assert state["retry_count"] == 0
        assert len(state["errors"]) == 0
        assert state["story"] is None
        assert state["script"] is None

    def test_workflow_builder_creation(self) -> None:
        """Test workflow builder creates graph."""
        builder = WorkflowBuilder()
        graph = builder.build()

        assert graph is not None

    def test_state_mutation(self) -> None:
        """Test that state can be mutated between nodes."""
        state = create_initial_state()

        # Simulate story finding
        state["current_step"] = "find_story"
        state["story"] = Story(
            id="test",
            title="Test Story",
            content="This is a test story with enough content to meet the minimum requirements.",
            category=StoryCategory.OTHER,
            metadata=RedditPostMetadata(
                post_id="test",
                subreddit="test",
                author="test",
                upvotes=100,
                num_comments=10,
                created_utc=datetime.utcnow(),
                url=HttpUrl("https://reddit.com/test"),
            ),
            viral_score=50.0,
        )

        assert state["story"] is not None
        assert state["current_step"] == "find_story"

    def test_error_handling_state(self) -> None:
        """Test error state management."""
        state = create_initial_state()

        state["errors"].append("Test error")
        state["retry_count"] += 1

        assert len(state["errors"]) == 1
        assert state["retry_count"] == 1
