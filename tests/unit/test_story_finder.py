"""Unit tests for StoryFinder agent."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from gossiptoon.agents.story_finder import StoryFinderAgent
from gossiptoon.core.config import ConfigManager
from gossiptoon.models.story import Story
from gossiptoon.agents.tools.reddit_search import RedditPost
from datetime import datetime

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.api.reddit_client_id = "fake_id"
    config.api.reddit_client_secret = "fake_secret"
    config.api.reddit_user_agent = "fake_agent"
    config.api.tavily_api_key = "fake_tavily"
    config.stories_dir = MagicMock()
    return config

@pytest.mark.asyncio
async def test_find_story_by_url(mock_config):
    """Test finding story by specific URL."""
    agent = StoryFinderAgent(mock_config)
    
    # Mock Reddit tool
    mock_post = RedditPost(
        post_id="p123",
        title="Test Post Title Must Be Long Enough To Pass Validation",
        content="Test Content " * 20, # > 100 chars
        subreddit="test_sub",
        author="author",
        upvotes=1000,
        num_comments=100,
        created_utc=1234567890.0,
        url="https://reddit.com/r/test/comments/p123",
        flair="Test Flair"
    )
    
    agent.reddit_tool.fetch_post_by_url = AsyncMock(return_value=mock_post)
    agent.reddit_tool.calculate_virality_score = MagicMock(return_value=95.0)
    
    # Mock save
    agent._save_story = MagicMock()
    
    story = await agent.find_story(story_url="https://reddit.com/r/test/comments/p123")
    
    assert isinstance(story, Story)
    assert story.title == "Test Post Title Must Be Long Enough To Pass Validation"
    assert story.viral_score == 95.0
    agent.reddit_tool.fetch_post_by_url.assert_called_once_with("https://reddit.com/r/test/comments/p123")

@pytest.mark.asyncio
async def test_find_story_search(mock_config):
    """Test searching for viral stories."""
    agent = StoryFinderAgent(mock_config)
    
    mock_posts = [MagicMock()] # Only needed to verify count passed to filter
    agent.reddit_tool.search_multiple_subreddits = AsyncMock(return_value=mock_posts)
    
    selected_post = RedditPost(
        post_id="p123",
        title="My wife left me and it is a very sad story indeed",
        content="Sad story " * 20, # > 100 chars
        subreddit="relationships",
        author="author",
        upvotes=5000,
        num_comments=500,
        created_utc=1234567890.0,
        url="https://reddit.com/r/relationships/comments/p123",
        flair=None
    )
    
    # Return list of (post, score) tuples for filter_suitable_posts
    agent.reddit_tool.filter_suitable_posts = MagicMock(return_value=[(selected_post, 98.0)])
    agent._save_story = MagicMock()
    
    story = await agent.find_story(min_virality=80.0)
    
    assert story.title == "My wife left me and it is a very sad story indeed"
    assert story.viral_score == 98.0
    agent.reddit_tool.search_multiple_subreddits.assert_called_once()


@pytest.mark.asyncio
async def test_find_story_no_results(mock_config):
    """Test exception when no stories found."""
    agent = StoryFinderAgent(mock_config)
    
    agent.reddit_tool.search_multiple_subreddits = AsyncMock(return_value=[])
    agent.reddit_tool.filter_suitable_posts = MagicMock(return_value=[])
    
    with pytest.raises(Exception, match="No suitable stories found"):
        await agent.find_story()
