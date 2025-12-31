# Ticket: TICKET-006-refine-visual-prompts

## Context

User feedback indicates issues with image generation quality and consistency:

1. **Style**: Need a consistent global style applied to every image.
2. **Character Sheets**: Currently generating "family portraits" or group shots instead of individual character references.
3. **Character Prompts**: Currently using narrative descriptions (e.g., "wife staring at husband") which confuses the image generator. Prompts should focus strictly on physical appearance.

## Design / Architecture

- **Global Style**: Inject the user-provided style prompt into every image generation call.
- **Character Generation**:
  - Modify `VisualDirector._generate_character_sheet` to strictly enforce "solo portrait" prompts.
  - Ensure prompts describe physical traits (hair, eyes, clothes) rather than actions/relationships.
- **Prompt Engineering**:
  - Update `director.py` to strip narrative context from character generation prompts.
  - Ensure consistent style prefix/suffix.

## Tasks

- [x] Update `VisualDirector` to apply global style prompt (User provided: "A panel from a Korean webtoon...") <!-- id: 1 -->
- [x] Modify character sheet generation to force single-character portraits <!-- id: 2 -->
- [x] Refine character description prompts to focus on visual traits <!-- id: 3 -->
- [x] Verify with a dry-run of visual generation (using `outputs/project_.../script.json`) <!-- id: 4 -->

## Acceptance Criteria

- [x] All generated character sheets show ONLY the specific character.
- [x] All images adhere to the "Korean webtoon" style.
- [x] Character prompts are descriptive (visual) not narrative (action).
