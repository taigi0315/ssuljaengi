# TICKET-034: Expand Subreddit Source List

**Priority**: Medium (P2)
**Status**: Todo
**Assignee**: AI Agent
**Created**: 2026-01-01
**Depends On**: TICKET-018 (Reddit Auto-Crawler)

## Problem

Currently sourcing from limited subreddits makes it difficult to find stories that fit the ideal 1-2 minute video format. Need to expand to more subreddits with viral, high-engagement content.

## Goal

Update the Reddit discovery module/scraper to pull stories from additional high-quality subreddits:
- r/JUSTNOMIL
- r/EntitledParents
- r/MildlyNoMIL
- r/relationship_advice
- r/pettyrevenge & r/ProRevenge
- r/TrueOffMyChest

## Requirements

### New Subreddit Sources

1. **Family Drama**
   - r/JUSTNOMIL (Just No Mother-In-Law)
   - r/MildlyNoMIL (Mild MIL stories)

2. **Parenting & Entitlement**
   - r/EntitledParents
   - r/EntitledPeople (bonus)

3. **Relationships**
   - r/relationship_advice (already may be included)
   - r/relationships (bonus)

4. **Revenge Stories**
   - r/pettyrevenge (short, satisfying)
   - r/ProRevenge (longer, complex)

5. **Confessions**
   - r/TrueOffMyChest
   - r/confessions (bonus)

### Configuration Updates

1. **Subreddit List**
   - Add new subreddits to default config
   - Support dynamic subreddit addition
   - Allow user customization

2. **Per-Subreddit Settings**
   - Different minimum upvote thresholds
   - Different content length filters
   - Different viral score weights

### Story Length Filtering

1. **Target Duration: 1-2 minutes**
   - Narration speed: ~150 words/minute
   - Target word count: 150-300 words
   - Filter by character count: 800-2000 characters

2. **Subreddit-Specific Adjustments**
   - r/pettyrevenge: Prefer shorter (1 min)
   - r/ProRevenge: May allow longer (2 min)
   - r/JUSTNOMIL: Medium length (1.5 min)

## Implementation Plan

### Phase A: Configuration Updates

- [ ] Add new subreddits to config file
- [ ] Define per-subreddit filtering rules
- [ ] Set word count/character limits
- [ ] Test configuration loading

### Phase B: Crawler Updates

- [ ] Update RedditCrawler to support new subreddits (TICKET-018)
- [ ] Add content length filtering
- [ ] Add per-subreddit threshold customization
- [ ] Test crawler with new sources

### Phase C: Quality Filtering

- [ ] Implement content length filters
- [ ] Add "story quality" heuristics
- [ ] Filter out meta posts, questions, etc.
- [ ] Test filtering effectiveness

### Phase D: Testing & Validation

- [ ] Crawl each new subreddit
- [ ] Validate story quality
- [ ] Check content length distribution
- [ ] Measure viral scores

## File Locations (Estimated)

- Crawler: `src/gossiptoon/scrapers/reddit_crawler.py`
- Config: `config/reddit_sources.yaml`
- CLI: `src/gossiptoon/cli/discover.py`

## Configuration Schema

```yaml
reddit:
  sources:
    - subreddit: JUSTNOMIL
      min_upvotes: 1000
      min_comments: 100
      min_chars: 800
      max_chars: 2000
      time_filter: week

    - subreddit: EntitledParents
      min_upvotes: 1500
      min_comments: 150
      min_chars: 600
      max_chars: 1800
      time_filter: week

    - subreddit: pettyrevenge
      min_upvotes: 800
      min_comments: 80
      min_chars: 500
      max_chars: 1500
      time_filter: week

    - subreddit: ProRevenge
      min_upvotes: 2000
      min_comments: 200
      min_chars: 1000
      max_chars: 2500
      time_filter: week

    - subreddit: TrueOffMyChest
      min_upvotes: 1200
      min_comments: 100
      min_chars: 800
      max_chars: 2000
      time_filter: week
```

## Content Length Filtering

```python
class ContentLengthFilter:
    """Filter stories by character/word count."""

    def calculate_duration_estimate(self, text: str) -> float:
        """Estimate video duration based on text length."""
        word_count = len(text.split())
        words_per_minute = 150
        return word_count / words_per_minute

    def filter_by_duration(
        self,
        story: RedditPost,
        min_duration: float = 1.0,
        max_duration: float = 2.0,
    ) -> bool:
        """Filter stories to target duration range."""
        duration = self.calculate_duration_estimate(story.selftext)
        return min_duration <= duration <= max_duration
```

## CLI Usage

```bash
# Discover from all configured subreddits
gossiptoon discover --all-sources

# Discover from specific new subreddits
gossiptoon discover --subreddits JUSTNOMIL,EntitledParents,pettyrevenge

# Filter by duration
gossiptoon discover --min-duration 1.0 --max-duration 2.0

# Show subreddit source list
gossiptoon sources --list
```

## Acceptance Criteria

- [ ] All 6+ new subreddits added to config
- [ ] Crawler successfully fetches from new sources
- [ ] Content length filtering works correctly
- [ ] Per-subreddit thresholds customizable
- [ ] CLI supports new subreddit discovery
- [ ] Stories fit 1-2 minute target duration
- [ ] Quality filtering removes meta/question posts

## Quality Heuristics

```python
def is_story_quality(post: RedditPost) -> bool:
    """Determine if post is a quality story."""

    # Filter out questions
    if post.title.strip().endswith("?"):
        return False

    # Filter out meta posts
    meta_keywords = ["update", "meta", "question", "help", "advice needed"]
    if any(kw in post.title.lower() for kw in meta_keywords):
        return False

    # Ensure substantial content
    if len(post.selftext) < 500:
        return False

    # Check engagement ratio
    engagement_ratio = post.num_comments / max(post.score, 1)
    if engagement_ratio < 0.05:  # Low engagement
        return False

    return True
```

## Testing Checklist

- [ ] Crawl r/JUSTNOMIL - verify stories found
- [ ] Crawl r/EntitledParents - verify stories found
- [ ] Crawl r/pettyrevenge - verify short stories
- [ ] Crawl r/ProRevenge - verify longer stories
- [ ] Crawl r/TrueOffMyChest - verify confessions
- [ ] Validate character counts match targets
- [ ] Test content length filtering accuracy
- [ ] Verify no meta posts in results

## Related Tickets

- TICKET-018: Reddit Auto-Crawler (prerequisite)
- TICKET-030: Enhance Narrative Dramatization (uses diverse sources)

## Notes

- **Priority**: MEDIUM - Expands content pool significantly
- **Dependency**: Requires TICKET-018 crawler implementation
- **User Feedback**: "Difficult to find 1-2 minute stories from single source"
- **Content Diversity**: Different subreddits = different story types
- **Future**: Add more niche subreddits based on performance
