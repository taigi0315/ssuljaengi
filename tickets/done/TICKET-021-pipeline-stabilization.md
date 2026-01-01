# TICKET-021: Pipeline Stabilization & Polish

## Objective

Fix critical bugs in the video generation pipeline preventing successful end-to-end execution, specifically addressing `VideoAssembler` failures, CLI resume logic, and API quota limits.

## Changes

1.  **Repo Cleanup**: Organized test scripts and artifacts.
2.  **Fix: Video Assembly**:
    - Renamed `CameraEffect` Enum to `CameraEffectType` to resolve name collision.
    - Chained subtitle filters within `filter_complex` to fix FFmpeg conflict.
    - Fixed `TypeError` in duration calculation (string vs int).
    - Explicitly passed `Script` object to `VideoAssembler`.
3.  **Fix: Resume CLI**:
    - Updated `main.py` to set job context before initialization, fixing "No checkpoint found" error.
4.  **Fix: API Quota Resilience**:
    - Implemented fallback in `EngagementWriter` to handle Gemini `429 Resource Exhausted` errors.
    - Returns valid default hooks to allow pipeline completion.
5.  **Quality Assurance**:
    - Added emoji sanitization to `EngagementOverlayGenerator` to prevent font rendering errors ("□").

## Verification

- **Debug Script**: `debug_assembly.py` confirmed FFmpeg command fixes.
- **End-to-End Test**: Successfully resumed `project_20260101_092458` and generated 63s video.

## Status

- [x] Implemented
- [x] Verified
- [x] Merged
