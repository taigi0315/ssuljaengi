# TICKET-032: Add Reddit Source Attribution to YouTube Metadata

**Priority**: Low (P3)
**Status**: Todo
**Assignee**: AI Agent
**Created**: 2026-01-01
**Depends On**: TICKET-022 (YouTube Metadata Generator)

## Problem

Currently, the original Reddit thread URL is not included in YouTube video descriptions. This creates:
- Attribution issues (ethical/legal)
- Missed opportunity to drive engagement to original content
- Potential copyright/fair use concerns

## Goal

Automatically include the original Reddit thread URL in the YouTube video description with proper formatting.

## Requirements

### Metadata Changes

1. **Description Format**
   ```
   [Existing video description]

   ---

   📖 Original Story: [Reddit Thread URL]

   💬 Read the full discussion and updates on Reddit!

   #RedditStories #AITA #[Subreddit]
   ```

2. **Required Information**
   - Original Reddit post URL
   - Subreddit name (for hashtags)
   - Optional: Post title
   - Optional: Post date

3. **Placement**
   - Source link in description (primary)
   - Optional: Pin comment with link (see TICKET-033)

### Technical Requirements

1. **Source Tracking**
   - Store original Reddit URL in project metadata
   - Pass URL through pipeline (scraper → metadata generator)
   - Validate URL format

2. **Description Template**
   - Update YouTube description template
   - Add source attribution section
   - Include relevant hashtags

3. **Configuration**
   - Enable/disable source attribution
   - Customize attribution message
   - Toggle hashtag generation

## Implementation Plan

### Phase A: Metadata Storage

- [ ] Update project metadata schema to include source_url
- [ ] Ensure Reddit scraper saves source URL
- [ ] Verify URL propagates through pipeline

### Phase B: Description Template Update

- [ ] Update YouTube description generator (TICKET-022)
- [ ] Add source attribution section to template
- [ ] Add subreddit-based hashtag generation
- [ ] Format URL with proper markdown/text

### Phase C: Configuration

- [ ] Add source attribution config options
- [ ] Add custom message template support
- [ ] Add hashtag enable/disable toggle

### Phase D: Testing

- [ ] Test with various subreddit sources
- [ ] Verify URL formatting in YouTube
- [ ] Check description length limits (5000 chars)
- [ ] Validate hashtag formatting

## File Locations (Estimated)

- Metadata generator: `src/gossiptoon/youtube/metadata_generator.py`
- Project schema: `src/gossiptoon/models/project.py`
- Config: `config/youtube_config.yaml`

## Data Schema Updates

### Project Metadata

```python
class ProjectMetadata(BaseModel):
    # ... existing fields ...
    source_url: str | None = None
    source_subreddit: str | None = None
    source_title: str | None = None
    source_date: datetime | None = None
```

### YouTube Description Template

```python
DESCRIPTION_TEMPLATE = """
{video_description}

{description_body}

---

📖 Original Story: {source_url}

💬 Read the full discussion and updates on Reddit!

{hashtags}

---

{footer}
"""
```

## Configuration

```yaml
youtube:
  metadata:
    source_attribution:
      enabled: true
      message: "📖 Original Story: {source_url}\n\n💬 Read the full discussion and updates on Reddit!"
      include_hashtags: true
      hashtag_prefix: "#RedditStories"
```

## Example Output

### Description Example

```
Ever wonder what happens when family drama goes too far? This story will shock you.

---

📖 Original Story: https://reddit.com/r/AITA/comments/abc123/aita_for_refusing_to_go_to_my_sisters_wedding

💬 Read the full discussion and updates on Reddit!

#RedditStories #AITA #FamilyDrama

---

Like and subscribe for more Reddit stories!
```

## Acceptance Criteria

- [ ] Source URL included in all YouTube descriptions
- [ ] URL is properly formatted and clickable
- [ ] Subreddit hashtags generated automatically
- [ ] Description stays under 5000 character limit
- [ ] Configuration toggle works
- [ ] Works with TICKET-022 metadata generator

## Legal/Ethical Considerations

- **Fair Use**: Proper attribution strengthens fair use claim
- **Community Guidelines**: Linking to original shows good faith
- **Copyright**: Transformative work with clear source attribution
- **Reddit TOS**: Check compliance with Reddit's terms

## Related Tickets

- TICKET-022: YouTube Metadata Generator (prerequisite)
- TICKET-033: Implement Pinned Comment Strategy (complementary)
- TICKET-018: Reddit Auto-Crawler (provides source URLs)

## Notes

- **Priority**: LOW - Not blocking, but improves ethics and legal standing
- **Dependency**: Requires TICKET-022 to be completed first
- **Future**: Could add "story update" detection (check Reddit for updates)
