# TICKET-033: Implement Pinned Comment Strategy

**Priority**: Low (P3)
**Status**: Todo
**Assignee**: AI Agent
**Created**: 2026-01-01
**Depends On**: TICKET-023 (YouTube Auto-Upload)

## Problem

Need to drive engagement by directing viewers to the original Reddit story and encouraging comments. A pinned comment asking for viewer thoughts is an effective engagement tactic.

## Goal

Implement automated pinning of engagement comment after YouTube video upload, linking to original story and requesting viewer opinions.

## Requirements

### Comment Content

1. **Primary Message**
   - Link to original Reddit thread
   - Ask for viewer opinions
   - Encourage discussion

2. **Example Templates**
   ```
   🔗 Read the original story and all the updates: [Reddit URL]

   What do you think? Was OP right or wrong? Let me know! 👇
   ```

   ```
   Want to see what happened next? Check out the full Reddit thread: [URL]

   Drop your verdict in the replies! 💬
   ```

3. **Engagement Triggers**
   - Questions to viewers
   - Call-to-action (CTA)
   - Emoji usage for visibility
   - Controversial framing

### Implementation Approaches

#### Phase 1: Manual Process (Immediate)

- Document manual pinning workflow
- Create comment templates
- Add to upload checklist

#### Phase 2: Automated Process (This Ticket)

- Use YouTube Data API
- Auto-pin comment after upload
- Use configurable comment template

### Technical Requirements

1. **YouTube API Integration**
   - Insert comment via API
   - Pin comment via API
   - Handle authentication (OAuth)
   - Error handling and retry logic

2. **Comment Template System**
   - Configurable templates
   - Variable substitution (URL, title, etc.)
   - Multiple template options
   - A/B testing capability

3. **Timing**
   - Post comment immediately after upload
   - Pin as first comment
   - Optional: Delay pinning (first few minutes)

## Implementation Plan

### Phase A: Manual Workflow (Quick Win)

- [ ] Document manual comment posting process
- [ ] Create comment template library
- [ ] Add to upload documentation
- [ ] Train user on manual workflow

### Phase B: API Research

- [ ] Research YouTube Data API comments endpoint
- [ ] Research pinning API requirements
- [ ] Test API with sample video
- [ ] Document API limitations

### Phase C: Automation Implementation

- [ ] Implement comment posting module
- [ ] Implement comment pinning module
- [ ] Add template system
- [ ] Integrate with upload workflow (TICKET-023)

### Phase D: Testing

- [ ] Test comment posting
- [ ] Test comment pinning
- [ ] Verify template substitution
- [ ] End-to-end test with upload

## File Locations (Estimated)

- YouTube API: `src/gossiptoon/youtube/api_client.py`
- Comment module: `src/gossiptoon/youtube/comments.py` (new)
- Templates: `config/comment_templates.yaml`
- Upload integration: `src/gossiptoon/youtube/uploader.py`

## API Design

### Comment Templates

```yaml
comment_templates:
  engagement_default:
    template: |
      🔗 Read the original story: {source_url}

      What's your take? Was {protagonist} right? Let me know! 👇

  engagement_controversial:
    template: |
      This one divided the internet. Check the original: {source_url}

      Which side are you on? Comment below! 💬

  engagement_update:
    template: |
      Want to know what happened next? Full story + updates: {source_url}

      Drop your reaction! 👇
```

### YouTube API Usage

```python
class YouTubeCommentManager:
    def post_comment(
        self,
        video_id: str,
        text: str,
    ) -> str:
        """Post a comment on a video. Returns comment ID."""

    def pin_comment(
        self,
        comment_id: str,
    ) -> bool:
        """Pin a comment as the top comment."""

    def post_and_pin(
        self,
        video_id: str,
        template_name: str,
        template_vars: dict,
    ) -> str:
        """Post and pin a comment using template."""
```

## CLI Integration

```bash
# Manual comment posting
gossiptoon comment <video_id> --template engagement_default

# Auto-pin during upload
gossiptoon upload <project_id> --auto-pin-comment
```

## Acceptance Criteria

### Manual Workflow (Phase 1)
- [ ] Comment templates documented
- [ ] Manual process documented
- [ ] User can successfully post and pin manually

### Automated Workflow (Phase 2)
- [ ] Can post comment via API
- [ ] Can pin comment via API
- [ ] Template system works
- [ ] Integration with upload workflow
- [ ] Error handling for API failures
- [ ] OAuth authentication works

## YouTube API Endpoints

1. **Post Comment**
   - Endpoint: `commentThreads.insert`
   - Requires: OAuth 2.0 scope `youtube.force-ssl`

2. **Pin Comment**
   - Endpoint: `comments.update`
   - Set `moderationStatus` to pinned

## Limitations & Considerations

1. **API Quota**: YouTube API has daily quota limits
2. **Authentication**: Requires OAuth (same as upload)
3. **Channel Ownership**: Can only pin on own channel
4. **Spam Detection**: YouTube may flag automated comments

## Related Tickets

- TICKET-023: YouTube Auto-Upload (prerequisite for automation)
- TICKET-032: Reddit Source Attribution (provides source URL for comment)

## Notes

- **Two-Phase Approach**: Start with manual, automate later
- **Priority**: LOW - Nice to have, not critical for MVP
- **User Feedback**: "Manual first, then automate"
- **Engagement Impact**: Can significantly boost comment counts
