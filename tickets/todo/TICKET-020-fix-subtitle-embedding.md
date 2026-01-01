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
- [x] Check FFmpeg command used for video assembly
- [x] Verify subtitle stream is embedded in output MP4
- [ ] Test playback in multiple players (QuickTime, VLC, Browser) - **Pending E2E test**

## Root Cause Analysis

**Confirmed**: FFmpeg filter chain was broken. Multiple `-vf` options overwrote each other.

**Original Bug**:

```python
for subtitle_file in subtitle_filters:
    command.output_options.extend(["-vf", f"subtitles={subtitle_file}"])
    # Second -vf overwrites the first!
```

**Fix Applied**:

```python
combined_filter = ",".join(subtitle_filters)
command.output_options.extend(["-vf", combined_filter])
# Now both subtitles are chained properly
```

## Implementation Status

- [x] **Root cause identified**: Multiple `-vf` options overwriting
- [x] **Fix implemented**: Chain filters with comma separator
- [x] **Code committed**: `30a03ce` - "fix(video): properly chain subtitle filters"
- [x] **Import cleanup**: Fixed EffectType → CameraEffect migration
- [ ] **E2E test**: Awaiting full pipeline test with all 3 tickets

## Testing Plan (Post-Implementation)

After TICKET-018 and TICKET-019 are complete:

1. Generate new test video with all features
2. Verify subtitles visible in QuickTime
3. Verify subtitles visible in VLC
4. Verify engagement overlays (if enabled)

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
