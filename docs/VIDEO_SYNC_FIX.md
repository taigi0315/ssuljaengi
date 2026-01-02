# Video/Audio Synchronization Bug Fix

**Date**: 2026-01-01  
**Severity**: CRITICAL  
**Status**: ✅ FIXED (Commit: 73268b7)

---

## Problem Summary

Output videos were **significantly shorter** than their audio tracks, causing mid-speech cutoffs.

### Observed Symptoms

- **Video duration**: 34.2 seconds
- **Audio duration**: 63.5 seconds
- **Missing**: ~29 seconds (46% of content!)
- **Effect**: Last scenes cut off mid-dialogue, incomplete story

### User Impact

- Pipeline unusable for production
- Videos end abruptly during climax/resolution
- Audio continues after video ends (black screen)

---

## Root Cause Analysis

### Architecture Context

The webtoon video pipeline has a **1-to-many relationship** between scenes and audio chunks:

```
Script Structure:
├─ 10 scenes (visual assets)
└─ 19 audio chunks (narration + dialogue)

Example - Scene "act5_resolution_02":
├─ Audio chunk 1: Minjun dialogue (6.33s)
├─ Audio chunk 2: Jieun dialogue (3.22s)
└─ Audio chunk 3: Narrator (2.32s)
   Total duration: 11.87s
```

### The Bug

**Three functions** had the same critical bug - using only the **first audio chunk** instead of summing **all chunks** for a scene:

#### 1. `VideoAssembler._get_scene_duration()` ❌

```python
# BUGGY CODE (before fix)
for segment in audio_project.segments:
    if segment.scene_id == scene_id:
        return segment.duration_seconds  # ❌ Returns first match only!
```

**Impact**: Returns 6.33s instead of 11.87s for the example scene above.

#### 2. `VideoAssembler._build_timeline()` ❌

```python
# BUGGY CODE (before fix)
for asset in visual_project.assets:
    for seg in audio_project.segments:
        if seg.scene_id == asset.scene_id:
            audio_segment = seg  # ❌ Breaks after first match
            break
    duration = audio_segment.duration_seconds  # ❌ Only first chunk
```

**Impact**: Timeline entries use incorrect durations, causing early scene transitions.

#### 3. `PipelineOrchestrator._overlay_audio_sfx()` ❌

```python
# BUGGY CODE (before fix)
for scene, audio_segment in zip(script.get_all_scenes(), audio_project.segments):
    # ❌ WRONG! Pairs 10 scenes with first 10 of 19 segments
    current_offset += audio_segment.duration_seconds  # ❌ Incorrect timing
```

**Impact**: SFX placed at wrong timestamps, doesn't account for multi-chunk scenes.

---

## The Fix

### Changed Approach

**Before**: First-match (early return/break)  
**After**: Group-and-sum (list comprehension + sum())

### Code Changes

#### Fix 1: `_get_scene_duration()` ✅

```python
# FIXED CODE
def _get_scene_duration(self, scene_id, audio_project):
    # Get ALL segments for this scene
    scene_segments = [
        segment for segment in audio_project.segments
        if segment.scene_id == scene_id
    ]

    if not scene_segments:
        return 5.0  # Default fallback

    # Sum ALL chunk durations
    total_duration = sum(seg.duration_seconds for seg in scene_segments)
    return total_duration  # ✅ Correct!
```

#### Fix 2: `_build_timeline()` ✅

```python
# FIXED CODE
for asset in visual_project.assets:
    # Get ALL audio segments for this scene
    scene_segments = [
        seg for seg in audio_project.segments
        if seg.scene_id == asset.scene_id
    ]

    # Sum ALL chunk durations for this scene
    duration = sum(seg.duration_seconds for seg in scene_segments)

    segment = TimelineSegment(
        scene_id=asset.scene_id,
        start_time=current_time,
        end_time=current_time + duration,  # ✅ Correct duration
        ...
    )
    current_time += duration
```

#### Fix 3: `_overlay_audio_sfx()` ✅

```python
# FIXED CODE
from collections import defaultdict

# Group segments by scene_id FIRST
segments_by_scene = defaultdict(list)
for segment in audio_project.segments:
    segments_by_scene[segment.scene_id].append(segment)

current_offset = 0.0

for scene in script.get_all_scenes():
    # Get ALL segments for this scene
    scene_segments = segments_by_scene.get(scene.scene_id, [])
    scene_duration = sum(s.duration_seconds for s in scene_segments)

    # Place SFX at correct offset
    if scene.visual_sfx:
        sfx_list.append((sfx_path, current_offset))  # ✅ Correct timing

    # Accumulate TOTAL scene duration
    current_offset += scene_duration  # ✅ All chunks included
```

---

## Bonus Fix: Audio Speed

**Issue**: Audio playback sounded 10% faster than normal.

**Root Cause**:

```python
# config.py (before)
speed_factor: float = Field(default=1.1, ...)  # 10% speedup
```

**Fix**:

```python
# config.py (after)
speed_factor: float = Field(default=1.0, ...)  # Normal speed
```

---

## Verification

### Test Cases

1. **Unit Test**: `test_multiple_chunks_scene()`

   - Scene with 3 chunks (6.33s + 3.22s + 2.32s)
   - Expected: 11.87s ✅
   - Before fix: 6.33s ❌

2. **Integration Test**: `test_timeline_with_multiple_chunks_per_scene()`

   - 2 scenes: (5s+3s) and (4s)
   - Expected timeline: [0-8s], [8-12s] ✅
   - Before fix: [0-5s], [5-9s] ❌

3. **E2E Test**: project_20260101_210420
   - 10 scenes, 19 audio chunks
   - Expected: ~63.5s video
   - Before fix: 34.2s ❌
   - After fix: 63.5s ✅

### Command

```bash
# Run unit tests
pytest tests/unit/test_video_duration_fix.py -v

# Verify with real project
gossiptoon resume project_20260101_210420
ffprobe outputs/project_20260101_210420/videos/*.mp4
```

---

## Impact Assessment

### Before Fix

- ❌ Video duration: 34.2s (missing 46% of content)
- ❌ Audio continues after video ends
- ❌ Story incomplete (climax/resolution cut off)
- ❌ SFX timing incorrect
- ❌ Pipeline unusable for production

### After Fix

- ✅ Video duration: 63.5s (matches audio exactly)
- ✅ All scenes show for complete duration
- ✅ No mid-speech cutoffs
- ✅ SFX plays at correct scene boundaries
- ✅ Audio speed normalized to 1.0x
- ✅ Pipeline production-ready

---

## Prevention Strategy

### Code Review Checklist

- [ ] Any loop over `audio_project.segments` checks for multi-chunk scenes
- [ ] Duration calculations use `sum()` not first-match
- [ ] Scene/segment pairing uses proper grouping (not `zip()`)

### Future Safeguards

1. **Linting**: Add comment warnings near duration calculations
2. **Tests**: Regression test suite (see `test_video_duration_fix.py`)
3. **Documentation**: This document + inline code comments

---

## Files Modified

| File                       | Function                | Change                        |
| -------------------------- | ----------------------- | ----------------------------- |
| `core/config.py`           | AudioConfig             | `speed_factor: 1.1 → 1.0`     |
| `video/assembler.py`       | `_get_scene_duration()` | Sum all scene segments        |
| `video/assembler.py`       | `_build_timeline()`     | Group segments, sum durations |
| `pipeline/orchestrator.py` | `_overlay_audio_sfx()`  | Use defaultdict grouping      |

### Commit

```
73268b7 - fix: Critical video/audio sync bug - sum all audio chunks per scene
```

---

## Related Issues

- ✅ **Issue 1**: Video duration mismatch (FIXED)
- ✅ **Issue 2**: Audio speed too fast (FIXED)
- ⚠️ **Potential Issue 3**: Caption timing (verify after fix)

---

## References

- **Test Suite**: `tests/unit/test_video_duration_fix.py`
- **Architecture Doc**: `.gemini/antigravity/brain/.../pipeline_architecture.md`
- **Commit**: `73268b7`
