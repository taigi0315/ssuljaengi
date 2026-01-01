# TICKET-023: YouTube Auto-Upload

**Priority**: Low (P3)  
**Status**: Todo  
**Assignee**: AI Agent  
**Created**: 2026-01-01  
**Depends On**: TICKET-022 (YouTube Metadata Generator)

## Problem

YouTube API is complex and requires OAuth authentication. Manual upload is still needed after video generation.

## Goal

Automate YouTube video upload with proper authentication and metadata.

## Requirements

1. **OAuth 2.0 Setup**

   - Google Cloud Project setup guide
   - OAuth credentials management
   - Token refresh handling

2. **Upload Features**

   - Direct upload to YouTube
   - Use metadata from TICKET-022
   - Schedule publishing (optional)
   - Privacy settings (public/unlisted/private)

3. **CLI Integration**
   ```bash
   gossiptoon upload <project_id>
   gossiptoon upload <project_id> --public --schedule "2026-01-02 10:00"
   ```

## Implementation Plan

### Phase A: Research & Setup

- [ ] Research YouTube Data API v3
- [ ] Document OAuth 2.0 flow
- [ ] Create setup guide for users
- [ ] Test with sample uploads

### Phase B: Implementation

- [ ] OAuth authentication flow
- [ ] Video upload endpoint
- [ ] Metadata integration (from TICKET-022)
- [ ] Error handling & retry logic

### Phase C: CLI Integration

- [ ] Add `upload` command
- [ ] Interactive auth flow
- [ ] Progress tracking
- [ ] Upload confirmation

## Notes

- **Complexity**: High (OAuth + large file handling)
- **User Action Required**: Google Cloud setup
- **Dependency**: TICKET-022 must be completed first
- **Alternative**: Keep manual upload workflow (simpler for MVP)

## Related Tickets

- TICKET-022: YouTube Metadata Generator (prerequisite)

## Decision

Mark as **LOW PRIORITY** - Manual upload is acceptable for MVP.
Consider this feature only if there's strong user demand.
