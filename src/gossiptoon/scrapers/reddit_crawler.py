"""Reddit story auto-crawler for discovering viral content."""

import logging
from datetime import datetime, timezone
from typing import Optional

import praw
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DiscoveredStory(BaseModel):
    """Metadata for a discovered Reddit story."""

    url: str = Field(..., description="Full Reddit post URL")
    post_id: str = Field(..., description="Reddit post ID")
    title: str = Field(..., description="Post title")
    subreddit: str = Field(..., description="Subreddit name")
    upvotes: int = Field(..., description="Number of upvotes")
    num_comments: int = Field(..., description="Number of comments")
    created_utc: datetime = Field(..., description="Post creation timestamp")
    viral_score: float = Field(..., description="Calculated viral potential score")
    content_preview: str = Field(..., description="First 200 chars of content")
    author: str = Field(..., description="Post author username")


class RedditCrawler:
    """Automatic Reddit story discovery and ranking."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        user_agent: str,
    ):
        """Initialize Reddit crawler.

        Args:
            client_id: Reddit API client ID
            client_secret: Reddit API client secret
            user_agent: User agent string for Reddit API
        """
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )
        logger.info("Reddit crawler initialized")

    async def discover_stories(
        self,
        subreddits: list[str],
        time_filter: str = "week",
        limit: int = 100,
        min_upvotes: int = 1000,
        min_comments: int = 100,
        min_length: int = 500,
        max_length: int = 10000,
    ) -> list[DiscoveredStory]:
        """Discover top stories across multiple subreddits.

        Args:
            subreddits: List of subreddit names (without r/ prefix)
            time_filter: Time filter (hour, day, week, month, year, all)
            limit: Maximum number of posts to fetch per subreddit
            min_upvotes: Minimum upvote threshold
            min_comments: Minimum comment count threshold
            min_length: Minimum content length in characters
            max_length: Maximum content length in characters

        Returns:
            List of discovered stories, sorted by viral score (descending)
        """
        logger.info(
            f"Discovering stories from {len(subreddits)} subreddits "
            f"(time_filter={time_filter}, limit={limit})"
        )

        all_stories: list[DiscoveredStory] = []

        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                logger.info(f"Fetching from r/{subreddit_name}...")

                # Fetch top posts
                for submission in subreddit.top(time_filter=time_filter, limit=limit):
                    # Skip removed/deleted posts
                    if submission.removed_by_category or submission.selftext == "[removed]":
                        continue

                    # Apply filters
                    if submission.score < min_upvotes:
                        continue
                    if submission.num_comments < min_comments:
                        continue

                    content_length = len(submission.selftext)
                    if content_length < min_length or content_length > max_length:
                        continue

                    # Calculate viral score
                    created_dt = datetime.fromtimestamp(
                        submission.created_utc, tz=timezone.utc
                    )
                    age_hours = (datetime.now(timezone.utc) - created_dt).total_seconds() / 3600
                    viral_score = self.calculate_viral_score(
                        upvotes=submission.score,
                        comments=submission.num_comments,
                        age_hours=age_hours,
                    )

                    # Create discovered story
                    story = DiscoveredStory(
                        url=f"https://www.reddit.com{submission.permalink}",
                        post_id=submission.id,
                        title=submission.title,
                        subreddit=subreddit_name,
                        upvotes=submission.score,
                        num_comments=submission.num_comments,
                        created_utc=created_dt,
                        viral_score=viral_score,
                        content_preview=submission.selftext[:200],
                        author=str(submission.author) if submission.author else "[deleted]",
                    )
                    all_stories.append(story)

                logger.info(f"Found {len(all_stories)} stories from r/{subreddit_name}")

            except Exception as e:
                logger.error(f"Error fetching from r/{subreddit_name}: {e}")
                continue

        # Sort by viral score (descending)
        all_stories.sort(key=lambda s: s.viral_score, reverse=True)

        logger.info(
            f"Discovery complete: {len(all_stories)} total stories "
            f"(top score: {all_stories[0].viral_score:.1f})"
            if all_stories
            else "No stories found matching criteria"
        )

        return all_stories

    def calculate_viral_score(
        self,
        upvotes: int,
        comments: int,
        age_hours: float,
    ) -> float:
        """Calculate viral potential score for a story.

        Formula:
            score = (upvotes * 1.0 + comments * 2.0) / (age_hours ^ 0.5)

        - Comments weighted 2x (higher engagement)
        - Recency bonus via age penalty (square root decay)

        Args:
            upvotes: Number of upvotes
            comments: Number of comments
            age_hours: Post age in hours

        Returns:
            Viral score (higher = more viral potential)
        """
        # Engagement score (comments weighted higher)
        engagement = upvotes * 1.0 + comments * 2.0

        # Recency multiplier (newer posts get bonus)
        # Use max(1, age_hours) to avoid division by zero
        age_penalty = max(1.0, age_hours) ** 0.5

        score = engagement / age_penalty

        return score
