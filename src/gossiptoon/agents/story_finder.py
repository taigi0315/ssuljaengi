"""Story Finder Agent for discovering viral Reddit stories."""

import logging
from datetime import datetime
from typing import Optional

from pydantic import HttpUrl

from gossiptoon.agents.tools.reddit_search import RedditPost, RedditSearchTool
from gossiptoon.agents.tools.tavily_search import TavilySearchTool
from gossiptoon.core.config import ConfigManager
from gossiptoon.core.constants import StoryCategory
from gossiptoon.models.story import RedditPostMetadata, Story

logger = logging.getLogger(__name__)


class StoryFinderAgent:
    """Agent for finding viral Reddit stories suitable for video creation."""

    # Keyword mapping for story categorization
    CATEGORY_KEYWORDS = {
        StoryCategory.AITA: ["AITA", "am I the asshole", "the asshole"],
        StoryCategory.RELATIONSHIP: [
            "boyfriend",
            "girlfriend",
            "husband",
            "wife",
            "dating",
            "relationship",
        ],
        StoryCategory.WORKPLACE: ["coworker", "boss", "manager", "work", "job", "office"],
        StoryCategory.FAMILY: [
            "mother",
            "father",
            "sister",
            "brother",
            "parent",
            "family",
        ],
        StoryCategory.REVENGE: ["revenge", "petty", "malicious compliance"],
        StoryCategory.WEDDING: ["wedding", "bride", "groom", "marriage"],
    }

    def __init__(self, config: ConfigManager) -> None:
        """Initialize Story Finder Agent.

        Args:
            config: Configuration manager
        """
        self.config = config
        self.reddit_tool = RedditSearchTool(
            client_id=config.api.reddit_client_id,
            client_secret=config.api.reddit_client_secret,
            user_agent=config.api.reddit_user_agent,
        )
        self.tavily_tool = TavilySearchTool(api_key=config.api.tavily_api_key)

    async def find_story(
        self,
        story_url: Optional[str] = None,
        min_virality: float = 70.0,
        time_filter: str = "week",
        use_tavily: bool = False,
    ) -> Story:
        """Find a viral story suitable for video creation.

        Args:
            story_url: Optional Reddit post URL (if provided, fetches this specific post)
            min_virality: Minimum virality score (0-100) - used when searching
            time_filter: Time filter for Reddit search
            use_tavily: Whether to use Tavily for additional search

        Returns:
            Selected story

        Raises:
            Exception: If no suitable story is found
        """
        # If a specific URL is provided, fetch that post directly
        if story_url:
            logger.info(f"Fetching story from URL: {story_url}")
            post = await self.reddit_tool.fetch_post_by_url(story_url)
            virality_score = self.reddit_tool.calculate_virality_score(post)

            # Convert to Story model
            story = self._convert_to_story(post, virality_score)

            logger.info(
                f"Fetched story: {story.title[:50]}... (virality: {virality_score:.1f})"
            )

            # Save story to output directory
            self._save_story(story)

            return story

        # Otherwise, search for viral stories
        logger.info(f"Searching for stories with min_virality={min_virality}")

        # Search Reddit
        reddit_posts = await self.reddit_tool.search_multiple_subreddits(
            subreddits=self.config.reddit.subreddits,
            time_filter=self.config.reddit.time_filter,
            limit_per_subreddit=15,
        )

        logger.info(f"Found {len(reddit_posts)} total posts from Reddit")

        # Filter for suitable posts
        suitable_posts = self.reddit_tool.filter_suitable_posts(
            reddit_posts,
            min_upvotes=self.config.reddit.min_upvotes,
            min_comments=self.config.reddit.min_comments,
            min_length=self.config.reddit.min_chars,
            max_length=self.config.reddit.max_chars,
            min_virality=min_virality,
        )

        logger.info(f"Filtered to {len(suitable_posts)} suitable posts")

        if not suitable_posts:
            raise Exception("No suitable stories found meeting criteria")

        # Get top story
        top_post, virality_score = suitable_posts[0]

        # Convert to Story model
        story = self._convert_to_story(top_post, virality_score)

        logger.info(
            f"Selected story: {story.title[:50]}... (virality: {virality_score:.1f})"
        )

        # Save story to output directory
        self._save_story(story)

        return story

    def _convert_to_story(self, post: RedditPost, virality_score: float) -> Story:
        """Convert RedditPost to Story model.

        Args:
            post: Reddit post
            virality_score: Calculated virality score

        Returns:
            Story model
        """
        # Categorize story
        category = self._categorize_story(post)

        # Generate story ID
        story_id = f"story_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{post.post_id}"

        # Create metadata
        metadata = RedditPostMetadata(
            post_id=post.post_id,
            subreddit=post.subreddit,
            author=post.author,
            upvotes=post.upvotes,
            num_comments=post.num_comments,
            created_utc=post.created_utc,
            url=HttpUrl(post.url),
            flair=post.flair,
        )

        # Generate tags
        tags = self._generate_tags(post, category)

        return Story(
            id=story_id,
            title=post.title,
            content=post.content,
            category=category,
            metadata=metadata,
            viral_score=virality_score,
            tags=tags,
        )

    def _categorize_story(self, post: RedditPost) -> StoryCategory:
        """Categorize story based on title and content.

        Args:
            post: Reddit post

        Returns:
            Story category
        """
        text = (post.title + " " + post.content).lower()

        # Check each category's keywords
        category_scores: dict[StoryCategory, int] = {}

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword.lower() in text)
            if score > 0:
                category_scores[category] = score

        # Return category with highest score
        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]

        # Default category
        return StoryCategory.OTHER

    def _generate_tags(self, post: RedditPost, category: StoryCategory) -> list[str]:
        """Generate content tags for story.

        Args:
            post: Reddit post
            category: Story category

        Returns:
            List of tags
        """
        tags = [category.value]

        # Add flair as tag if available
        if post.flair:
            tags.append(post.flair.lower().replace(" ", "_"))

        # Add subreddit
        tags.append(post.subreddit.lower())

        return tags

    def _save_story(self, story: Story) -> None:
        """Save story to output directory.

        Args:
            story: Story to save
        """
        import json

        output_path = self.config.stories_dir / f"{story.id}.json"

        with open(output_path, "w") as f:
            json.dump(story.model_dump(mode="json"), f, indent=2, default=str)

        logger.info(f"Story saved to {output_path}")
