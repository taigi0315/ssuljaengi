# 🎥 TICKET-027: Refine & Diversify Visual Effects (VFX)

## Summary

Significantly expands the Visual Effects library with new camera movements (Zoom, Pan, Variable Shake) and integrates them into the ScriptWriter/Evaluator workflow, resolving the issue of "aggressive and monotonous" shake effects.

## Problem

- **Monotonous**: Only had one generic "Shake" effect.
- **Aggressive**: Shake was too intense and had no duration limit, causing motion sickness.
- **Static**: Lack of subtle camera movements (Zoom/Pan) made non-action scenes feel dead.

## Changes

### 1. Expanded VFX Library (`src/gossiptoon/video/effects/camera.py`)

- **Variable Shake**:
  - `SHAKE_SLOW`: 2Hz, Wide amplitude (Tension/Unease)
  - `SHAKE_FAST`: 15Hz, Tight amplitude (Shock/Impact)
  - `SHAKE`: Standard drama shake
- **KenBurns Integration**:
  - `ZOOM_IN` / `ZOOM_OUT`
  - `PAN_LEFT` / `PAN_RIGHT`
  - All exposed as explicit `CameraEffect` types

### 2. Intelligent Selection (`src/gossiptoon/agents/script_writer.py`)

- Updated **ScriptWriter System Prompt**:
  - Added full list of `camera_effect` options
  - Provided usage guidelines (e.g., "shake_fast" for max 1.5s)
  - Added `camera_effect` to Example Scene

### 3. Safety Constraints (`src/gossiptoon/agents/script_evaluator.py`)

- **Duration Limit**: Shake effects strictly capped at **2.0s**.
- **Validation**: Evaluator rejects invalid effect names or excessive shake durations.

### 4. Tests (`tests/unit/test_vfx_implementation.py`)

- Verified factory logic for creating specific Shake variants
- Verified FFmpeg filter generation for different intensity/speed settings

## How It Works

1. **Writer** chooses `camera_effect: "zoom_in"` for a revelation scene.
2. **Evaluator** checks if duration is safe (Zoom allowed up to 4s, Shake up to 2s).
3. **CameraEffect** factory creates a `KenBurnsEffect` with pre-configured parameters.
4. **FFmpegBuilder** applies the filter.

## Acceptance Criteria

- [x] Zoom/Pan/Shake variants implemented
- [x] Shake duration limited to 2s
- [x] LLM prompt updated with options
- [x] Validator enforces constraints
- [x] Unit tests passed

## Breaking Changes

**None**. Backward compatible (defaults to "static" if field missing).

## Next Steps

- Verify visual impact in next E2E run.
- Proceed to **TICKET-028** (TTS Voice Selection).
