# Ticket: TICKET-001-fix-video-pipeline

## Context

Video pipeline has multiple issues: excessive duration (1h+), freeze after 3s, and file corruption.
This ticket consolidates all fixes related to producing a stable, 30-40s dynamic video.

## Design / Architecture

- **Output Organization**: `outputs/{job_id}/` structure.
- **Video Dynamics**:
  - `KenBurnsEffect`: Fixed duration calculation (`d=1` for video inputs).
  - `FFmpegBuilder`: Added `-shortest` constraint.
  - Scripting: Updated system prompts for high tempo (12+ scenes, 30-40s).
- **Stability Fixes**:
  - Enforced `setsar=1`, `format=yuv420p`, and `fps=30` on ALL segments to prevent freeze/corruption.
  - Fixed label collision in `_apply_effects` with `unique_id`.

## Tasks & Tests

### Duration Fixes (Done)

- [x] Add `target_duration` and `min_scenes` to VideoConfig
- [x] Implement `atempo` 1.1x speedup for audio
- [x] Fix Ken Burns effect loop issue (`d=1`)
- [x] Add `-shortest` to FFmpeg builder

### Freeze/Corruption Fixes (Done)

- [x] Analyze `VideoAssembler` and `FFmpegBuilder` logic
- [x] Fix video/audio duration mismatch in effects
- [x] Enforce consistent stream properties (SAR, Format, FPS)
- [x] Verify with `repro_broken_video.py` and real assets

### AV Sync Fixes (TICKET-005)

- [x] Implement Frame-Accurate Duration Calculation (DDA) in `VideoAssembler`
- [x] Verify drift elimination (< 1 frame error)

## Acceptance Criteria

- [x] All tests passed
- [x] Video duration ~30-40s
- [x] Video plays without freezing or corruption
- [x] Audio and Video are perfectly synchronized
