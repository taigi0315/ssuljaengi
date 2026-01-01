# TICKET-013: Audio SFX Mixing

**Goal**: Implement audio mixing logic to overlay SFX sounds on narration audio.

## Background

Building on TICKET-012 (SFX library), now implement the actual audio mixing to combine:

- Narration audio (100% volume)
- SFX audio (70% volume, at scene start time)

## Technical Requirements

- Use `pydub` library for audio manipulation
- Mix SFX at correct timestamps based on scene timing
- Output mixed audio for video pipeline

## Tasks

- [ ] Install `pydub` dependency (add to requirements.txt) <!-- id: 1 -->
- [ ] Implement `AudioComposer.overlay_sfx()` method <!-- id: 2 -->
- [ ] Add `AudioSegment.sfx_path` field to model <!-- id: 3 -->
- [ ] Integrate SFX overlay into pipeline <!-- id: 4 -->
- [ ] Test with manual project <!-- id: 5 -->

## Acceptance Criteria

- [ ] Mixed audio contains both narration and SFX
- [ ] SFX plays at correct timestamps
- [ ] Volume levels are balanced (narration 100%, SFX 70%)
- [ ] End-to-end pipeline generates video with audio SFX
