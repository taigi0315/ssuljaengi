"""Story data models for Reddit gossip content."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl

from gossiptoon.core.constants import StoryCategory


class RedditPostMetadata(BaseModel):
    """Metadata for a Reddit post."""

    post_id: str = Field(..., description="Reddit post ID")
    subreddit: str = Field(..., description="Subreddit name")
    author: str = Field(..., description="Post author")
    upvotes: int = Field(ge=0, description="Number of upvotes")
    num_comments: int = Field(ge=0, description="Number of comments")
    created_utc: datetime = Field(..., description="Post creation time")
    url: HttpUrl = Field(..., description="Reddit post URL")
    flair: Optional[str] = Field(None, description="Post flair")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "post_id": "abc123",
                "subreddit": "AmItheAsshole",
                "author": "throwaway12345",
                "upvotes": 15420,
                "num_comments": 892,
                "created_utc": "2025-01-01T12:00:00Z",
                "url": "https://reddit.com/r/AmItheAsshole/comments/abc123",
                "flair": "Not the A-hole",
            }
        }


class Story(BaseModel):
    """A Reddit story selected for video conversion."""

    id: str = Field(..., description="Unique story ID")
    title: str = Field(..., min_length=10, max_length=300, description="Story title")
    content: str = Field(..., min_length=100, description="Story content")
    category: StoryCategory = Field(..., description="Story category")
    metadata: RedditPostMetadata = Field(..., description="Reddit post metadata")
    viral_score: float = Field(
        ge=0, le=100, description="Calculated virality score (0-100)"
    )
    selected_at: datetime = Field(
        default_factory=datetime.utcnow, description="When story was selected"
    )
    tags: list[str] = Field(default_factory=list, description="Content tags")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "story_20250101_abc123",
                "title": "AITA for refusing to attend my sister's wedding?",
                "content": "So this happened last week. My sister (28F) is getting married...",
                "category": "aita",
                "viral_score": 87.5,
                "tags": ["wedding", "family", "drama"],
            }
        }

    def get_word_count(self) -> int:
        """Get word count of story content.

        Returns:
            Number of words in content
        """
        return len(self.content.split())

    def get_reading_time_seconds(self, words_per_minute: int = 150) -> float:
        """Estimate reading time in seconds.

        Args:
            words_per_minute: Average reading speed

        Returns:
            Estimated reading time in seconds
        """
        return (self.get_word_count() / words_per_minute) * 60

    def is_suitable_for_shorts(self, max_words: int = 500) -> bool:
        """Check if story is suitable for YouTube Shorts.

        Args:
            max_words: Maximum word count for shorts

        Returns:
            True if story is suitable
        """
        word_count = self.get_word_count()
        return 100 <= word_count <= max_words
