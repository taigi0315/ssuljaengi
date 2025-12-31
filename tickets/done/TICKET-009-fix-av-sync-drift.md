# TICKET-009: Fix AV Sync Drift

**User Report**:

> "scene 2 audio --> image 1 (~ image 2)... scene changes nearly 1 step behind audio"
> "subtitle catch up in the beginning but soon it shows later than audio"

**Analysis**:
The video segments appear to be accumulating length, causing visual content (images and burnt-in subtitles) to drift "late" relative to the master audio track.
Since DDA (Dynamic Duration Adjustment) was implemented to calculate _shorter_ video segments (floored/rounded to frames) to match audio, a "late" video drift implies the generated video frames are somehow _more_ than calculated, or the audio playback is faster than expected.

**Hypothesis**:

1. `zoompan` filter or `fps` filter chain might be resetting timestamps or adding duplicate frames, extending segment duration.
2. `concat` filter might be handling precise timestamps poorly, inserting gaps/padding.
3. Master audio construction vs Segment audio duration mismatch.

## Tasks

- [ ] Reproduce drift using `manual_reassemble.py` logs (check "Drift" calculation vs reality). <!-- id: 1 -->
- [ ] Inspect FFmpeg `concat` behavior and intermediate stream lengths. <!-- id: 2 -->
- [ ] Fix `VideoAssembler` / `FFmpegBuilder` duration logic. <!-- id: 3 -->
- [ ] Verify precise sync on output video. <!-- id: 4 -->

## Acceptance Criteria

- [ ] Scene transitions happen EXACTLY when the audio for the next scene starts.
- [ ] No progressive drift over 60s video.
