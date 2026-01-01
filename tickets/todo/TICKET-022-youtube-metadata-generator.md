# TICKET-022: YouTube Metadata Generator

**Priority**: Medium (P2)  
**Status**: Todo  
**Assignee**: AI Agent  
**Created**: 2026-01-01  
**Depends On**: None

## Problem

After generating videos, users need to manually create YouTube titles, descriptions, and tags for upload. This is time-consuming and inconsistent.

## Goal

Automatically generate YouTube-optimized metadata (title, description, tags) for each video and save them in a standardized format for easy copy-paste during upload.

## Requirements

### Functional Requirements

1. **YouTube Folder Structure**

   ```
   outputs/project_YYYYMMDD_HHMMSS/
   ├── youtube/
   │   ├── metadata.md          # Human-readable markdown
   │   ├── metadata.txt          # Plain text format
   │   └── metadata.json         # Machine-readable JSON
   ```

2. **Metadata Fields**

   - **Title**: SEO-optimized, 60 chars max (YouTube limit: 100)
   - **Description**: Story summary + hashtags
   - **Tags**: Relevant keywords (max 500 chars total)
   - **Thumbnail Text** (optional): Suggested overlay text

3. **Auto-Generation Logic**
   - Extract from Script (hook, climax)
   - SEO keywords from subreddit/category
   - Hashtags: #Shorts, #Reddit, #AITA, etc.

### Output Format Examples

#### metadata.md

```markdown
# YouTube Upload Metadata

## Title

🚨 AITA: I Refused to Drive My Husband Home!

## Description

My husband demanded I pick him up from his colonoscopy during my busiest work day. I said NO. Was I wrong? 😱

Full story from r/AmItheAsshole

#Shorts #Reddit #AITA #RedditStories #Relationships

## Tags

aita, reddit stories, relationship advice, family drama, reddit aita, am i the asshole, shorts

## Thumbnail Text (Suggestion)

"I SAID NO!"
"AITA?"
```

#### metadata.txt

```
TITLE:
🚨 AITA: I Refused to Drive My Husband Home!

DESCRIPTION:
My husband demanded I pick him up from his colonoscopy during my busiest work day. I said NO. Was I wrong? 😱

Full story from r/AmItheAsshole

#Shorts #Reddit #AITA #RedditStories #Relationships

TAGS:
aita, reddit stories, relationship advice, family drama, reddit aita, am i the asshole, shorts
```

#### metadata.json

```json
{
  "title": "🚨 AITA: I Refused to Drive My Husband Home!",
  "description": "My husband demanded I pick him up from his colonoscopy during my busiest work day. I said NO. Was I wrong? 😱\n\nFull story from r/AmItheAsshole\n\n#Shorts #Reddit #AITA #RedditStories #Relationships",
  "tags": [
    "aita",
    "reddit stories",
    "relationship advice",
    "family drama",
    "reddit aita",
    "am i the asshole",
    "shorts"
  ],
  "category": "24",
  "thumbnail_text": "I SAID NO!"
}
```

## Implementation Plan

### Phase A: Metadata Generator Agent

- [ ] Create `YouTubeMetadataGenerator` class
- [ ] Implement title generation (extract from hook/climax)
- [ ] Implement description generation (summary + hashtags)
- [ ] Implement tag generation (keywords extraction)
- [ ] Add emoji support for viral appeal

### Phase B: Pipeline Integration

- [ ] Add `YOUTUBE_METADATA_GENERATED` stage to pipeline
- [ ] Create `youtube/` folder in output directory
- [ ] Generate 3 formats: `.md`, `.txt`, `.json`
- [ ] Add to checkpoint system

### Phase C: SEO Optimization

- [ ] Keyword research integration (optional)
- [ ] Trending hashtag suggestions
- [ ] A/B title variations (optional)

## API Design

```python
class YouTubeMetadataGenerator:
    def __init__(self, llm: ChatGoogleGenerativeAI):
        """Initialize metadata generator."""

    def generate_metadata(
        self,
        script: Script,
        story: Story,
    ) -> YouTubeMetadata:
        """Generate YouTube metadata from script and story."""

class YouTubeMetadata(BaseModel):
    title: str = Field(..., max_length=100)
    description: str = Field(..., max_length=5000)
    tags: List[str] = Field(..., max_items=500)  # YouTube limit
    category_id: str = "24"  # Entertainment
    thumbnail_text: Optional[str] = None
```

## CLI Usage

```bash
# Auto-generated during video creation
gossiptoon run <url>
# → Creates outputs/project_XXX/youtube/metadata.{md,txt,json}

# View metadata
cat outputs/project_XXX/youtube/metadata.md

# Copy to clipboard (macOS)
cat outputs/project_XXX/youtube/metadata.txt | pbcopy
```

## Acceptance Criteria

- [ ] YouTube folder created for each project
- [ ] 3 metadata files generated (md, txt, json)
- [ ] Title is SEO-optimized and under 100 chars
- [ ] Description includes story summary and hashtags
- [ ] Tags are relevant and under 500 chars total
- [ ] Files are human-readable and easy to copy-paste
- [ ] Integration test with full pipeline

## Future Enhancements

- **Thumbnail Generator**: Auto-generate thumbnails with text overlay
- **YouTube API Upload**: Direct upload to YouTube (TICKET-023)
- **Analytics Tracking**: Track which metadata performs best
- **Multi-language Support**: Generate metadata in multiple languages

## Related Tickets

- TICKET-020: Subtitle Fix
- TICKET-018: Auto-Crawler
- TICKET-023: YouTube Auto-Upload (future)

## Notes

- Keep titles punchy and clickable
- Use emojis strategically (1-2 max)
- Follow YouTube Shorts best practices
- Consider thumbnail text readability on mobile
