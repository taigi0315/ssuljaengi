# TICKET-012: Audio SFX Library Setup

**Goal**: Set up audio sound effects library and create SFXMapper to map visual SFX keywords to audio files.

## Background

Building on TICKET-011 (visual SFX text), we now add **actual audio playback** of sound effects synchronized with dramatic moments.

## SFX Library (12 Sounds)

1. **Tension** (4): DOOM, DUN-DUN, LOOM, RUMBLE
2. **Action** (5): SQUEEZE, GRAB, GRIP, CLENCH, CRUSH
3. **Impact** (4): BAM!, WHAM!, THUD, TA-DA!

## Tasks

- [ ] Create `assets/sfx/` directory structure <!-- id: 1 -->
- [ ] Download/acquire 12 SFX audio files (CC0/CC-BY license) <!-- id: 2 -->
- [ ] Create `SFXMapper` class in `src/gossiptoon/audio/sfx_mapper.py` <!-- id: 3 -->
- [ ] Add `.gitattributes` for LFS (if needed) or document in README <!-- id: 4 -->
- [ ] Create unit tests for SFXMapper <!-- id: 5 -->

## Acceptance Criteria

- [ ] All 12 SFX audio files are organized in `assets/sfx/`
- [ ] `SFXMapper.get_sfx_path("BAM!")` returns correct file path
- [ ] Files are properly licensed (CC0/CC-BY) with attribution in CREDITS.md
