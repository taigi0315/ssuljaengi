# TICKET-020: Fix Subtitle Embedding

**Priority**: High (P0 - Blocker)  
**Status**: Todo  
**Assignee**: AI Agent  
**Created**: 2025-12-31

## Problem

User reports that subtitles (narration captions) are not visible in the generated video, despite the ASS file being created correctly.

## Investigation

- [x] ASS file exists: `outputs/project_20251231_230509/videos/shorts_condo_betrayal_001_captions.ass`
- [x] ASS content is valid (100 dialogue lines with proper formatting)
- [ ] Check FFmpeg command used for video assembly
- [ ] Verify subtitle stream is embedded in output MP4
- [ ] Test playback in multiple players (QuickTime, VLC, Browser)

## Root Cause Analysis

**Hypothesis 1**: Subtitles are soft-embedded but player doesn't support ASS
**Hypothesis 2**: FFmpeg filter not applied correctly
**Hypothesis 3**: Subtitle track missing from output file

## Solution Options

### Option A: Hard-burn Subtitles (Recommended)

- Use FFmpeg `-vf subtitles=file.ass` to burn subtitles into video
- Pros: Universal compatibility, always visible
- Cons: Cannot be disabled, slightly slower encoding

### Option B: Soft-embed with MP4 format

- Keep ASS as separate track
- Pros: User can toggle on/off
- Cons: Limited player support for ASS in MP4

## Implementation Plan

1. **Investigate Current FFmpeg Command**

   - Check `ffmpeg_builder.py` subtitle handling
   - Verify filter chain construction

2. **Modify FFmpeg Builder**

   - Ensure `subtitles` filter is properly applied
   - Add validation for subtitle file existence
   - Test with sample video

3. **Testing**

   - Generate new test video
   - Verify subtitles visible in:
     - macOS QuickTime Player
     - VLC Media Player
     - Browser (HTML5 video)

4. **Edge Cases**
   - Handle missing subtitle files gracefully
   - Support both single subtitle and dual subtitle (captions + engagement)

## Acceptance Criteria

- [ ] Subtitles are hard-burned into video
- [ ] Visible in all major players (QuickTime, VLC, browser)
- [ ] No performance degradation
- [ ] Existing tests pass
- [ ] E2E test generates video with visible subtitles

## Related Tickets

- TICKET-017: Engagement Text Overlay (uses same subtitle system)
