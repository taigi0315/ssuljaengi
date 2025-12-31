# Project Work Log

This document records the narrative of changes for the Ssuljaengi project.

## [2025-12-31] Workflow Initialization

- **Action**: Adopted new Agent Behavior Guidelines (`agent/rule.md`) and Workflow (`agent/workflow.md`).
- **Setup**: Initialized `tickets/todo/` and `tickets/done/` directories.
- **Previous Context**:
  - Resolved video duration issue (1h+ -> 30s) by adding `-shortest` flag to FFmpeg.
  - Fixed infinite effect loop by setting `d=1` in Ken Burns effect.
  - Verified output organization (`outputs/{job_id}/`).
  - **Start**: Retroactively created `tickets/done/TICKET-001-fix-video-effects.md`.
  - **Fixed**: Video freeze after 3s (TICKET-002).
    - **Cause**: Mismatched SAR/Pixel Format between static and effect segments.
    - **Fix**: Enforced `setsar=1` and `format=yuv420p` for _all_ segments in `FFmpegBuilder`.
    - **Verification**: Verified command structure ensures consistent properties.
  - **Fixed**: Broken/Corrupt Video File (TICKET-003).
    - **Cause**: Potential timestamp/timebase mismatch in `concat` due to missing `fps` filter in standardization chain.
    - **Fix**: Added `fps={self.fps}` to standardization chain and fixed label collision bug in `_apply_effects`.
    - **Verification**: `tests/repro_broken_video.py` passes with valid output file.
  - **Fixed**: Audio-Visual Sync Lag (TICKET-005).
    - **Cause**: Accumulated rounding errors in video duration (float) vs audio duration caused video to drift ahead of audio.
    - **Fix**: Implemented Frame-Accurate Duration Calculation (DDA) in `VideoAssembler` to lock video segments to cumulative audio timestamps.
    - **Verification**: Logs confirm drift is capped at ±0.5 frames (<16ms).
  - **Refined**: Visual Generation Prompts (TICKET-006).
    - **Change**: Updated default image style to "Korean Webtoon" aesthetic.
    - **Fix**: Forced single-character isolation for character sheets using negative prompts and strict instructions.
    - **Verification**: Validated prompts via `tests/verify_visual_prompts.py` dry-run.
  - **New Feature**: Extreme Dramatic Hook (TICKET-007).
    - **Change**: Enforced "Cold Open" / "Flash Forward" logic in ScriptWriter system prompt.
    - **Fix**: Relaxed validation to allow 0.5s-3.0s Hook scenes and longer Climax scenes (up to 15s).
    - **Verification**: Validated `Script` model acceptance of 1.5s hook using `tests/verify_hook_validation.py`.
  - **New Feature**: Rapid Word Subtitles (TICKET-008).
    - **Change**: Added `SubtitleGenerator` to create Word-Level ASS subtitles with random pastel colors.
    - **Change**: Updated `VideoAssembler` and `FFmpegBuilder` to overlay the generated ASS file.
    - **Verification**: Verified subtitle file content and successful video render via `scripts/manual_reassemble.py`.
  - **Bug Fix**: AV Sync Drift (TICKET-009).
    - **Issue**: Progressive visual delay (scenes appearing ~1 step behind audio).
    - **Root Cause**: `zoompan` and other filters were generating slightly more frames than calculated, causing segment over-run.
    - **Fix**: Added `trim=duration=...` filter to enforce exact segment durations before concatenation.
    - **Verification**: Re-ran `manual_reassemble.py` on `project_20251231_165437` - successful render without drift.
  - **Feature**: Hybrid Subtitle Logic (TICKET-010).
    - **Change**: Implemented emotion-based subtitle mode switching in `SubtitleGenerator`.
    - **Modes**: Rapid (word-by-word, pastel, 70% position) for intense emotions; Sentence (full text, yellow, bottom) for calm narration.
    - **Detection**: Uses `EmotionTone` metadata (anger, excitement, etc.) and text heuristics (exclamation marks, short sentences).
    - **Verification**: Generated ASS file with dual styles, successfully rendered with mode transitions.
