"""Reddit search tool for finding viral stories."""

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from pydantic import BaseModel, Field

from gossiptoon.core.exceptions import RedditAPIError
from gossiptoon.utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)


class RedditPost(BaseModel):
    """Reddit post data."""

    post_id: str
    title: str
    content: str
    subreddit: str
    author: str
    upvotes: int
    num_comments: int
    created_utc: datetime
    url: str
    flair: Optional[str] = None


class RedditSearchTool:
    """Tool for searching Reddit for viral stories."""

    # Target subreddits for gossip content
    DEFAULT_SUBREDDITS = [
        "AmItheAsshole",
        "relationship_advice",
        "relationships",
        "tifu",
        "TrueOffMyChest",
        "EntitledPeople",
        "MaliciousCompliance",
        "ProRevenge",
        "NuclearRevenge",
        "BestofRedditorUpdates",
    ]

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        user_agent: str = "GossipToon/0.1.0",
    ) -> None:
        """Initialize Reddit search tool.

        Args:
            client_id: Reddit API client ID
            client_secret: Reddit API client secret
            user_agent: User agent string
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent
        self._reddit: Optional[Any] = None

    def _init_reddit(self) -> Any:
        """Initialize Reddit API client (lazy loading).

        Returns:
            PRAW Reddit instance

        Raises:
            RedditAPIError: If initialization fails
        """
        if self._reddit is not None:
            return self._reddit

        if not self.client_id or not self.client_secret:
            raise RedditAPIError(
                "Reddit API credentials not configured. "
                "Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env"
            )

        try:
            import praw

            self._reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent,
            )
            logger.info("Reddit API client initialized")
            return self._reddit
        except Exception as e:
            raise RedditAPIError(f"Failed to initialize Reddit API: {e}") from e

    @retry_with_backoff(max_retries=3, exceptions=(RedditAPIError,))
    async def fetch_post_by_url(self, url: str) -> RedditPost:
        """Fetch a specific Reddit post by URL.

        Args:
            url: Reddit post URL

        Returns:
            RedditPost object

        Raises:
            RedditAPIError: If post cannot be fetched
        """
        reddit = self._init_reddit()

        try:
            submission = reddit.submission(url=url)

            # Get the post content
            content = submission.selftext if submission.selftext else ""

            post = RedditPost(
                post_id=submission.id,
                title=submission.title,
                content=content,
                subreddit=submission.subreddit.display_name,
                author=str(submission.author) if submission.author else "[deleted]",
                upvotes=submission.score,
                num_comments=submission.num_comments,
                created_utc=datetime.fromtimestamp(submission.created_utc),
                url=url,
                flair=submission.link_flair_text,
            )

            logger.info(f"Fetched post: {post.title[:50]}... from r/{post.subreddit}")
            return post

        except Exception as e:
            raise RedditAPIError(f"Failed to fetch Reddit post from URL: {e}") from e

    @retry_with_backoff(max_retries=3, exceptions=(RedditAPIError,))
    async def search_subreddit(
        self,
        subreddit: str,
        time_filter: str = "week",
        limit: int = 25,
        sort: str = "hot",
    ) -> list[RedditPost]:
        """Search a subreddit for posts.

        Args:
            subreddit: Subreddit name
            time_filter: Time filter (hour, day, week, month, year, all)
            limit: Maximum number of posts to return
            sort: Sort method (hot, new, top, rising)

        Returns:
            List of Reddit posts

        Raises:
            RedditAPIError: If search fails
        """
        try:
            reddit = self._init_reddit()
            subreddit_obj = reddit.subreddit(subreddit)

            posts = []
            if sort == "hot":
                submissions = subreddit_obj.hot(limit=limit)
            elif sort == "new":
                submissions = subreddit_obj.new(limit=limit)
            elif sort == "top":
                submissions = subreddit_obj.top(time_filter=time_filter, limit=limit)
            elif sort == "rising":
                submissions = subreddit_obj.rising(limit=limit)
            else:
                raise ValueError(f"Invalid sort method: {sort}")

            for submission in submissions:
                # Skip stickied posts and very short posts
                if submission.stickied or len(submission.selftext) < 100:
                    continue

                posts.append(
                    RedditPost(
                        post_id=submission.id,
                        title=submission.title,
                        content=submission.selftext,
                        subreddit=submission.subreddit.display_name,
                        author=str(submission.author) if submission.author else "[deleted]",
                        upvotes=submission.score,
                        num_comments=submission.num_comments,
                        created_utc=datetime.fromtimestamp(submission.created_utc),
                        url=f"https://reddit.com{submission.permalink}",
                        flair=submission.link_flair_text,
                    )
                )

            logger.info(f"Found {len(posts)} posts in r/{subreddit}")
            return posts

        except Exception as e:
            raise RedditAPIError(f"Reddit search failed: {e}") from e

    async def search_multiple_subreddits(
        self,
        subreddits: Optional[list[str]] = None,
        time_filter: str = "week",
        limit_per_subreddit: int = 10,
    ) -> list[RedditPost]:
        """Search multiple subreddits.

        Args:
            subreddits: List of subreddit names (uses defaults if None)
            time_filter: Time filter
            limit_per_subreddit: Max posts per subreddit

        Returns:
            Combined list of posts from all subreddits
        """
        if subreddits is None:
            subreddits = self.DEFAULT_SUBREDDITS

        all_posts = []
        for subreddit in subreddits:
            try:
                posts = await self.search_subreddit(
                    subreddit=subreddit,
                    time_filter=time_filter,
                    limit=limit_per_subreddit,
                    sort="top",
                )
                all_posts.extend(posts)
            except RedditAPIError as e:
                logger.warning(f"Failed to search r/{subreddit}: {e}")
                continue

        # Sort by upvotes
        all_posts.sort(key=lambda p: p.upvotes, reverse=True)
        return all_posts

    def calculate_virality_score(
        self,
        post: RedditPost,
        upvote_weight: float = 0.4,
        comment_weight: float = 0.3,
        recency_weight: float = 0.3,
    ) -> float:
        """Calculate virality score for a post.

        Args:
            post: Reddit post
            upvote_weight: Weight for upvote score
            comment_weight: Weight for comment score
            recency_weight: Weight for recency score

        Returns:
            Virality score (0-100)
        """
        # Normalize upvotes (log scale, cap at 50k)
        import math

        upvote_score = min(math.log10(max(post.upvotes, 1)) / math.log10(50000), 1.0)

        # Normalize comments (log scale, cap at 5k)
        comment_score = min(math.log10(max(post.num_comments, 1)) / math.log10(5000), 1.0)

        # Recency score (decays over 7 days)
        days_old = (datetime.utcnow() - post.created_utc).days
        recency_score = max(1.0 - (days_old / 7.0), 0.0)

        # Weighted sum
        total_score = (
            upvote_score * upvote_weight
            + comment_score * comment_weight
            + recency_score * recency_weight
        )

        return round(total_score * 100, 2)

    def filter_suitable_posts(
        self,
        posts: list[RedditPost],
        min_upvotes: int = 1000,
        min_comments: int = 50,
        min_length: int = 100,
        max_length: int = 2000,
        min_virality: float = 50.0,
    ) -> list[tuple[RedditPost, float]]:
        """Filter posts suitable for video creation.

        Args:
            posts: List of Reddit posts
            min_upvotes: Minimum upvotes
            min_comments: Minimum comments
            min_length: Minimum content length
            max_length: Maximum content length
            min_virality: Minimum virality score

        Returns:
            List of (post, virality_score) tuples, sorted by virality
        """
        suitable = []

        for post in posts:
            # Check basic criteria
            if post.upvotes < min_upvotes:
                continue
            if post.num_comments < min_comments:
                continue

            content_length = len(post.content)
            if content_length < min_length or content_length > max_length:
                continue

            # Calculate virality
            virality = self.calculate_virality_score(post)
            if virality < min_virality:
                continue

            suitable.append((post, virality))

        # Sort by virality
        suitable.sort(key=lambda x: x[1], reverse=True)
        return suitable
