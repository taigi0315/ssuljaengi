# TICKET-028: Standardize Character Design Sheet Generation

**Priority**: Medium (P2)
**Status**: Todo
**Assignee**: AI Agent
**Created**: 2026-01-01
**Depends On**: None

## Problem

Character generations are inconsistent - some blend into backgrounds rather than producing clear reference design sheets. This makes it difficult to maintain character consistency across scenes.

## Goal

Update image generation prompts to strictly produce Character Design Sheets showing:
- Front and back views
- Varying facial expressions
- Clear character features
- White/neutral background (no scene blending)

## Requirements

### Character Sheet Format

1. **Standard Layout**
   - Front view (centered)
   - Back view (optional, if space)
   - 3-5 facial expression variations
   - Full body or head/torso focus (configurable)

2. **Visual Requirements**
   - Clean white or neutral background
   - No scene elements
   - Clear character outlines
   - Consistent art style

3. **Prompt Engineering**
   - User will provide specific prompt logic
   - System must integrate prompt template
   - Support character type variations (human, animal, etc.)

### Technical Requirements

1. **Image Generation Module**
   - Update character sheet prompt template
   - Add background enforcement ("white background", "character sheet")
   - Support expression variations in single sheet

2. **Quality Validation**
   - Detect if background is clean (optional ML validation)
   - Retry generation if scene elements detected
   - Manual review flag for quality issues

3. **Character Consistency**
   - Save character description per character
   - Reuse description for consistency across scenes
   - Support character reference images (future)

## Implementation Plan

### Phase A: Prompt Engineering

- [ ] Research character sheet generation best practices
- [ ] Draft initial character sheet prompt template
- [ ] Test with various character types
- [ ] Get user approval on prompt logic
- [ ] Integrate user-provided prompt template

### Phase B: Integration

- [ ] Update image generation module
- [ ] Add character sheet mode toggle
- [ ] Implement expression variation logic
- [ ] Add background cleaning/validation

### Phase C: Testing & Refinement

- [ ] Generate 20+ character sheets for testing
- [ ] Evaluate consistency and quality
- [ ] Refine prompt based on results
- [ ] Document prompt engineering decisions

## File Locations (Estimated)

- Image generation: `src/gossiptoon/image/generator.py`
- Prompt templates: `src/gossiptoon/prompts/image_prompts.py`
- Character models: `src/gossiptoon/models/character.py`

## Prompt Template Structure (Example)

```python
CHARACTER_SHEET_PROMPT = """
Create a character design sheet on a plain white background.

Character Description: {character_description}

Layout:
- Front view of character (centered)
- {expression_count} facial expressions showing: {expressions}
- Full body visible
- Clear, clean lines

Style: {art_style}
Background: Pure white, no scene elements
Format: Character reference sheet

DO NOT include any background scenery, props, or environmental elements.
ONLY the character on a white background.
"""
```

## Acceptance Criteria

- [ ] Character sheets have clean white backgrounds
- [ ] No scene blending or environmental elements
- [ ] Multiple expressions visible in single sheet
- [ ] Front view always included
- [ ] Consistent character features across generations
- [ ] User-provided prompt template integrated
- [ ] Works with various character types (human, animal, etc.)

## User Collaboration

User will provide specific prompt logic. System must be ready to:
- Accept custom prompt template
- Support template variables (character_description, expressions, etc.)
- Test and validate user prompt effectiveness

## Related Tickets

- TICKET-029: Implement Webtoon-Style Panel Layouts (uses character assets)

## Notes

- **User Input Required**: Waiting for specific prompt logic from user
- **Priority**: MEDIUM - Improves quality but not blocking
- **Future Enhancement**: Support character reference images for consistency
- **Art Style**: Should match overall webtoon aesthetic
