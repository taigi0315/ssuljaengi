# TICKET-025: Fix Missing SFX Implementation

**Priority**: High (P1)
**Status**: Todo
**Assignee**: AI Agent
**Created**: 2026-01-01
**Depends On**: None

## Problem

Sound effects (SFX) are currently missing from the final video output despite being part of the audio pipeline requirements. Videos lack impact without proper SFX layering.

## Goal

Investigate and fix the SFX application in the audio generation pipeline to ensure sound effects are properly rendered in the final output.

## Requirements

### Investigation Phase

1. **Verify SFX Code Existence**
   - Check if SFX layering module exists in codebase
   - Review audio pipeline architecture
   - Identify where SFX should be applied

2. **Debug Current Pipeline**
   - Trace audio generation flow
   - Identify why SFX is not rendering
   - Check for missing dependencies or configuration

### Implementation Phase

1. **If Code Exists:**
   - Debug and fix rendering issues
   - Verify SFX file paths and assets
   - Test SFX timing and synchronization

2. **If Code Missing:**
   - Implement SFX layering module
   - Support multiple SFX types (whoosh, impact, tension, etc.)
   - Integrate with existing audio pipeline

### Technical Requirements

1. **SFX Library Management**
   - Define SFX asset directory structure
   - Support multiple SFX categories
   - Add SFX selection logic based on scene type

2. **Audio Mixing**
   - Layer SFX over narration and BGM
   - Proper volume balancing
   - Timing synchronization with visual events

3. **Configuration**
   - SFX enable/disable toggle
   - Volume control per SFX type
   - Asset path configuration

## Implementation Plan

### Phase A: Investigation

- [ ] Search codebase for existing SFX implementation
- [ ] Review audio generation modules
- [ ] Trace audio pipeline from script to final output
- [ ] Document current architecture

### Phase B: Fix/Implementation

- [ ] Create or fix SFX layering module
- [ ] Add SFX asset management
- [ ] Implement audio mixing logic
- [ ] Add timing synchronization

### Phase C: Testing

- [ ] Test with various SFX types
- [ ] Verify audio quality and balance
- [ ] Test synchronization with visuals
- [ ] End-to-end pipeline test

## File Locations (Estimated)

- Audio pipeline: `src/gossiptoon/audio/`
- SFX module: `src/gossiptoon/audio/sfx.py` (may need creation)
- Audio mixer: `src/gossiptoon/audio/mixer.py`
- Config: `config/audio_config.yaml`

## Acceptance Criteria

- [ ] SFX renders in final video output
- [ ] SFX timing aligns with visual events
- [ ] Audio mixing maintains clarity (narration audible)
- [ ] Multiple SFX types supported
- [ ] Configuration options available
- [ ] No audio quality degradation

## Related Tickets

- TICKET-027: Refine and Diversify Visual Effects (complementary enhancement)

## Notes

- Priority: HIGH - This is a core feature gap affecting video quality
- Consider using free SFX libraries (freesound.org, zapsplat.com)
- Ensure licensing compliance for any SFX assets used
