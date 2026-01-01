# TICKET-017: Engagement Text Overlay Rendering

**Goal**: Render EngagementWriter's generated hooks as visible text overlays in the video.

## Background

TICKET-016 generates 2-3 engagement hooks (questions, comments, polls) but they're not yet displayed in the video. Need to render them as top-positioned text overlays.

## Requirements

- **Format**: ASS subtitle format (like existing subtitles)
- **Position**: Top 10% of screen (subtitles are at bottom)
- **Styles**: Different colors/fonts based on EngagementStyle
- **Timing**: Appear at specified scene + relative timing
- **Animation**: Fade in/out (optional but nice)

## Tasks

- [ ] Create `EngagementOverlayGenerator` class <!-- id: 1 -->
- [ ] Define ASS styles for each EngagementStyle <!-- id: 2 -->
- [ ] Implement timing calculation (scene offset + relative timing) <!-- id: 3 -->
- [ ] Add to VideoAssembler pipeline <!-- id: 4 -->
- [ ] Test with sample engagement project <!-- id: 5 -->

## Acceptance Criteria

- [ ] Engagement hooks visible at top of video
- [ ] Correct timing (aligned with specified scenes)
- [ ] Style differentiation (colors based on type)
- [ ] No overlap with bottom subtitles
- [ ] Readable for 2-3 seconds
