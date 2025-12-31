# Ticket: TICKET-004-fix-persistent-corruption

## Context

Video file `shorts_vegetarian_oven_drama_001.mp4` generated with "Video Freeze Fix" (TICKET-003) is unopenable/corrupt, despite successful FFmpeg exit code and valid synthetic repro.
File size is 7.6MB.

## Hypothesis

1. **Timebase explosion**: `zoompan` outputting massive PTS gaps.
2. **Audio/Video Drift**: `concat` failing to sync streams properly.
3. **Double Encoding**: The `format=yuv420p` being applied twice or conflicting.
4. **Resolution Mismatch**: `pad` vs `zoompan` output size.

## Tasks

- [ ] Inspect broken file with `ffprobe` <!-- id: 1 -->
- [ ] Inspect `manual_reassemble.py` logs (stdout) to see the EXACT command run <!-- id: 2 -->
- [ ] Verify `zoompan` `d` (duration) calculation logic in `KenBurnsEffect` vs `FFmpegBuilder` <!-- id: 3 -->
- [ ] Try simplifying the filter chain (remove `fps` force?) <!-- id: 4 -->

## Acceptance Criteria

- [ ] File plays in QuickTime/VLC <!-- id: 5 -->
