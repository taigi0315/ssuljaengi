# ⚡️ TICKET-026: Optimize Image Duration for Fast Pacing

## Summary

Optimizes the video pacing for YouTube Shorts/TikTok by reducing scene duration from **6-15s** to **2-4s** (Fast Mode) and updating visual generation logic to focus on "Key Moment" snapshots rather than complex actions.

## Problem

Current videos felt too slow for short-form content standards. Viewers lose interest if a single static image remains on screen for 10 seconds. Complex visual descriptions also took too long to process visually.

### Metrics Before

- **Total Video**: 50-60s (Too long for some Shorts)
- **Scene Duration**: 6-15s (Avg ~10s)
- **Visuals**: Complex multi-action scenes

### Metrics After

- **Total Video**: 30-45s (Optimized)
- **Scene Duration**: 2-4s (Avg 3s)
- **Visuals**: Instant readability ("One Key Moment")

## Changes

### 1. Pacing Overhaul (FAST MODE)

**Files**: `src/gossiptoon/agents/script_writer.py`, `src/gossiptoon/agents/script_evaluator.py`

- **Updated Constraints**:
  - **Hook**: 0.5-2s (Instant grab)
  - **Crisis/Climax**: 3-4s (Punchy drama)
  - **Resolution**: 2-3s (Quick wrap-up)
- **Strict Enforcement**: Evaluator rejects/fixes scenes > 4s
- **Example Scene**: Updated to 3.5s duration

### 2. Visual Logic Optimization ("Key Moment" Strategy)

**Files**: `src/gossiptoon/agents/script_writer.py`

- **Problem**: "She walks into the room, sits down, and starts crying" -> Too complex for 3s.
- **Solution**: "Extreme Close-up (ECU) of tear rolling down cheek" -> **Instant Readability**.
- **Refactoring**:
  - Enforce **"ONE KEY MOMENT"** in prompts.
  - Prioritize **Extreme Close-ups (ECU)** for mobile screens.
  - Reject complex multi-action descriptions.

### 3. Configuration Updates

**Files**: `src/gossiptoon/core/config.py`

Added new fields to `ScriptConfig` for pacing control:

- `min_scene_duration`: 2.0s
- `max_scene_duration`: 4.0s
- `target_scene_duration`: 3.0s

### 4. Tests

**Files**: `tests/unit/test_pacing_optimization.py`

- ✅ Verified fast mode keywords in prompts
- ✅ Verified duration validation logic
- ✅ Verified config defaults

## How It Works

1. **ScriptWriter** now aims for ~3s per scene by keeping text short (max 30 words).
2. **Visual Logic** generates "snapshot" moments tailored for 3s viewing.
3. **ScriptEvaluator** strictly enforces the 4s limit, triggering regeneration if exceeded.

## Acceptance Criteria

- [x] ScriptWriter targets 3-4s duration
- [x] Evaluator rejects scenes > 4s
- [x] Configuration settings added
- [x] Visual logic optimized for instant readability
- [x] Tests added
- [x] Documentation updated

## Breaking Changes

**None**. Backward compatible via configuration (though defaults are now set to Fast Mode).

## Next Steps

- Monitor viewer retention analytics on next upload.
- Proceed to TICKET-027 (Visual Effects refinement).
