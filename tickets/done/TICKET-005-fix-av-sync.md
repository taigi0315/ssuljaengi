# Ticket: TICKET-005-fix-av-sync

## Context

The user reports a significant lag where the image appears AFTER the corresponding audio narration (e.g., "microwave" mentioned, then image appears later).
This implies the video duration for preceding segments is consistently LONGER than the audio duration, causing drift.

## Hypothesis

1. **Pad Duration**: `KenBurnsEffect` or `zoompan` might be outputting slightly more frames than requested due to rounding errors, accumulating drift.
2. **Audio/Video Mismatch**: The Assembler uses `audio_segment.duration_seconds` to set video duration. If the actual audio file is slightly shorter than the metadata duration, or if FFmpeg padding adds frames, video will lag.
3. **Transition Delay**: No transitions are implemented, but if there were, they would eat time.

## Tasks

- [x] Inspect `manual_reassemble.py` logic to see how segment durations are calculated <!-- id: 1 -->
- [x] Debug `VideoAssembler._get_scene_duration` vs actual audio file duration <!-- id: 2 -->
- [x] Check if `zoompan` adds an extra frame or rounding error <!-- id: 3 -->
- [x] Fix logic to sync video strictly to audio timestamps <!-- id: 4 -->

## Acceptance Criteria

- [x] Image changes exactly when audio narration changes <!-- id: 5 -->
- [x] No accumulated drift over 30s <!-- id: 6 -->
