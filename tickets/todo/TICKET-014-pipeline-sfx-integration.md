# TICKET-014: Pipeline SFX Integration

**Goal**: Integrate AudioSFXMixer into the pipeline to automatically overlay SFX on master audio.

## Background

Final phase of audio SFX system - connect all components:

- SFXMapper (TICKET-012) ✅
- AudioSFXMixer (TICKET-013) ✅
- Pipeline integration (this ticket)

## Tasks

- [ ] Locate audio generation in pipeline/orchestrator <!-- id: 1 -->
- [ ] Add SFX mapping logic (match scene.visual_sfx to audio files) <!-- id: 2 -->
- [ ] Calculate scene offsets for SFX timing <!-- id: 3 -->
- [ ] Call AudioSFXMixer after master audio generation <!-- id: 4 -->
- [ ] Update video assembly to use mixed audio <!-- id: 5 -->
- [ ] End-to-end test with Reddit URL <!-- id: 6 -->

## Acceptance Criteria

- [ ] Generated videos include actual SFX audio playback
- [ ] SFX plays at correct timestamps (scene start)
- [ ] Volume levels are balanced
- [ ] No pipeline errors or crashes
