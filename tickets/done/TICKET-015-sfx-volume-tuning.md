# TICKET-015: SFX Volume Tuning

**Goal**: Reduce SFX volume to act as background enhancement rather than covering voice narration.

## Problem

User feedback: SFX goes over the voice, should be in background.

## Solution

Reduce default SFX volume from 70% to 30%.

**Current**: 70% volume (-6dB adjustment)  
**Target**: 30% volume (-10.5dB adjustment)

## Tasks

- [ ] Update `AudioSFXMixer` default volume <!-- id: 1 -->
- [ ] Update `orchestrator.py` SFX mixer instantiation <!-- id: 2 -->
- [ ] Test with existing project <!-- id: 3 -->
- [ ] Update documentation <!-- id: 4 -->

## Acceptance Criteria

- [ ] SFX audible but does not cover narration
- [ ] Mixed audio has balanced levels
- [ ] Configuration is easily adjustable for future tuning
