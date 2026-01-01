# TICKET-011: Visual Onomatopoeia (SFX)

**User Request**:
Add comic-style textual sound effects (e.g., "DOOM", "BAM", "SQUEEZE") to the generated images.

**Logic Design**:

1. **Script Level**:
   - `ScriptWriter` agent needs to explicitly suggest an SFX keyword for dramatic scenes.
   - Add `visual_sfx` (Optional[str]) to `Scene` model.
2. **Prompt Engineering**:
   - Update `Director` (ImagePrompter) to recognize `visual_sfx`.
   - If present, append specific instruction to image prompt: "Comic book style text sound effect 'BAM' in bold typography integrated into the background."

**User's Suggested Library**:

1. **Tension**: DOOM, DUN-DUN, LOOM, RUMBLE
2. **Action/Grip**: SQUEEZE, GRAB, GRIP, CLENCH, CRUSH
3. **Impact**: BAM!, WHAM!, THUD, TA-DA!

## Tasks

- [x] Update `Scene` model to include `visual_sfx` field. <!-- id: 1 -->
- [x] Update `ScriptWriter` system prompt with SFX guidelines. <!-- id: 2 -->
- [x] Update `Director` to inject SFX into image generation prompts. <!-- id: 3 -->
- [x] Verify generated prompts using `preview_prompts.py`. <!-- id: 4 -->

## Acceptance Criteria

- [x] ScriptAgent generates SFX keywords for dramatic moments.
- [x] Image prompts include instructions for these text elements.
- [x] Generated images (if model supports text) contain the SFX.
