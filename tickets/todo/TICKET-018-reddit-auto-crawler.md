# TICKET-018: Reddit Story Auto-Crawler

**Priority**: High (P1)  
**Status**: Todo  
**Assignee**: AI Agent  
**Created**: 2025-12-31  
**Depends On**: None

## Problem

Currently, users must manually find and provide Reddit story URLs. This is time-consuming and doesn't scale for content production.

## Goal

Implement an automated Reddit story discovery system that finds viral, high-quality stories based on configurable criteria.

## Requirements

### Functional Requirements

1. **Multi-Subreddit Support**

   - AITA (AmItheAsshole)
   - TIFU (Today I Fucked Up)
   - relationship_advice
   - ProRevenge
   - EntitledPeople
   - Configurable subreddit list

2. **Filtering Criteria**

   - Minimum upvotes (default: 1000)
   - Minimum comments (default: 100)
   - Time window (24h, week, month, all-time)
   - Content length (min/max characters)
   - Exclude removed/deleted posts

3. **Scoring Algorithm**

   - Viral score calculation (upvotes + comments weight)
   - Recency bonus
   - Story quality heuristics (length, engagement ratio)

4. **Output Format**
   - List of ranked story URLs
   - Metadata (title, score, subreddit, timestamp)
   - Deduplication (don't re-fetch processed stories)

### Non-Functional Requirements

1. **Performance**: Fetch top 100 stories in < 30 seconds
2. **Rate Limiting**: Respect Reddit API limits (60 requests/minute)
3. **Caching**: Cache results to avoid redundant API calls
4. **Logging**: Track fetched stories for audit trail

## Implementation Plan

### Phase A: Core Crawler

- [ ] Create `RedditCrawler` class in `src/gossiptoon/scrapers/reddit_crawler.py`
- [ ] Implement PRAW client initialization
- [ ] Add multi-subreddit fetching
- [ ] Implement filtering logic (upvotes, comments, length)
- [ ] Add viral score calculation

### Phase B: CLI Integration

- [ ] Add `gossiptoon discover` command
- [ ] Add CLI options:
  - `--subreddits` (comma-separated)
  - `--time-filter` (hour, day, week, month, year, all)
  - `--limit` (number of stories to return)
  - `--min-upvotes`
  - `--min-comments`
- [ ] Output formatted story list with scores

### Phase C: Storage & Tracking

- [ ] Create story queue/database (SQLite)
- [ ] Track processed stories to avoid duplicates
- [ ] Add `gossiptoon queue` command to view pending stories

## API Design

### RedditCrawler Class

```python
class RedditCrawler:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        user_agent: str,
    ):
        """Initialize crawler with Reddit credentials."""

    async def discover_stories(
        self,
        subreddits: list[str],
        time_filter: str = "week",
        limit: int = 100,
        min_upvotes: int = 1000,
        min_comments: int = 100,
    ) -> list[DiscoveredStory]:
        """Discover top stories across subreddits."""

    def calculate_viral_score(
        self,
        upvotes: int,
        comments: int,
        age_hours: float,
    ) -> float:
        """Calculate viral potential score."""
```

### DiscoveredStory Model

```python
class DiscoveredStory(BaseModel):
    url: str
    title: str
    subreddit: str
    upvotes: int
    num_comments: int
    created_utc: datetime
    viral_score: float
    content_preview: str
```

## CLI Usage Examples

```bash
# Discover top 10 AITA stories from the past week
gossiptoon discover --subreddits AITA --limit 10

# Multi-subreddit discovery
gossiptoon discover --subreddits AITA,TIFU,relationship_advice --time-filter day

# Custom thresholds
gossiptoon discover --min-upvotes 5000 --min-comments 500

# Add discovered stories to queue
gossiptoon discover --auto-queue
```

## Acceptance Criteria

- [ ] Can fetch top stories from multiple subreddits
- [ ] Correctly filters by upvotes, comments, and time
- [ ] Returns stories sorted by viral score
- [ ] CLI command works with all options
- [ ] Respects Reddit API rate limits
- [ ] No duplicate story processing
- [ ] Unit tests for scoring algorithm
- [ ] Integration test with live Reddit API

## Related Tickets

- TICKET-019: Batch Processing (will use discovered stories)
- TICKET-020: Subtitle Fix (unrelated, but testing together)

## Notes

- Use existing PRAW client from `gossiptoon.scrapers.reddit`
- Consider adding subreddit blacklist for inappropriate content
- Future: Add ML-based quality prediction
