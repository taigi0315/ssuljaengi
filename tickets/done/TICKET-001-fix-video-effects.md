# Ticket: TICKET-001-fix-video-effects

## Context

The video generation pipeline was producing videos with excessive duration (1h+) and infinite loops in effects. We needed to fix this to produce "dopamine spiking" 30-40s videos with dynamic effects.

## Design / Architecture

- **Output Organization**: `outputs/{job_id}/` structure.
- **Video Dynamics**:
  - `KenBurnsEffect`: Fixed duration calculation (`d=1` for video inputs).
  - `FFmpegBuilder`: Added `-shortest` constraint.
  - Scripting: Updated system prompts for high tempo (12+ scenes, 30-40s).

## Tasks & Tests

- [x] Add `target_duration` and `min_scenes` to VideoConfig
- [x] Update System Prompt for high tempo and emotional dialogue
- [x] Implement `atempo` 1.1x speedup for audio
- [x] Fix Ken Burns effect loop issue (`d=1`)
- [x] Add `-shortest` to FFmpeg builder
- [x] Verify total duration is ~30-40s
- [x] Verify output organization

## Acceptance Criteria

- [x] All tests passed
- [x] No hardcoded values (Config setup)
