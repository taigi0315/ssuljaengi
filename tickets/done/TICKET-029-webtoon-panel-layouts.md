# TICKET-029: Implement Webtoon-Style Panel Layouts

**Priority**: Medium (P2)
**Status**: Todo
**Assignee**: AI Agent
**Created**: 2026-01-01
**Depends On**: None

## Problem

Currently using single images per scene. Need to move to vertical "Webtoon" style paneling for more dynamic storytelling and better mobile viewing experience.

## Goal

Implement fixed panel layout templates (3-panel, 4-panel vertical splits) that the Scriptwriter can select and the image generator can populate with scene-specific content.

## Requirements

### Panel Layout Templates

1. **Template A: 3-Panel Vertical Split**
   - 3 equal-height panels stacked vertically
   - Aspect ratio: 9:16 (mobile-optimized)
   - Panel borders/gutters configurable

2. **Template B: 4-Panel Vertical Split**
   - 4 equal-height panels stacked vertically
   - Aspect ratio: 9:16 (mobile-optimized)
   - Panel borders/gutters configurable

3. **Future Templates** (out of scope for this ticket)
   - Mixed panel sizes
   - L-shaped layouts
   - Diagonal splits

### Workflow Integration

1. **Scriptwriter Selection**
   - LLM selects appropriate template per scene
   - Template ID in script (e.g., "template_a_3panel")
   - Panel count must match scene complexity

2. **Image Generation**
   - Generate separate image per panel
   - Each panel has specific scene description
   - Speech bubble placement instructions per panel
   - Stitch panels into single vertical image

3. **Speech Bubbles**
   - Position bubbles within panel boundaries
   - Support multi-panel dialogue flow
   - Respect reading order (top to bottom)

### Technical Requirements

1. **Template System**
   - Define panel layout configurations
   - Panel dimensions and positions
   - Border/gutter styling

2. **Image Composition**
   - Generate individual panel images
   - Composite into final vertical layout
   - Maintain image quality during stitching

3. **Prompt Engineering**
   - Panel-specific prompts
   - Bubble placement per panel
   - Maintain visual consistency across panels

## Implementation Plan

### Phase A: Template System

- [ ] Design panel layout data structures
- [ ] Implement Template A (3-panel)
- [ ] Implement Template B (4-panel)
- [ ] Add template configuration to config file
- [ ] Create template visualization/documentation

### Phase B: Image Composition

- [ ] Implement panel image generation
- [ ] Create image stitching module
- [ ] Add border/gutter rendering
- [ ] Test composite quality and dimensions

### Phase C: Scriptwriter Integration

- [ ] Update scriptwriter prompts with template options
- [ ] Add template selection to script schema
- [ ] Update image prompt generator for panels
- [ ] Add panel-specific scene descriptions

### Phase D: Speech Bubble Integration

- [ ] Update bubble placement for panel coordinates
- [ ] Handle multi-panel dialogue flow
- [ ] Test bubble positioning accuracy
- [ ] Validate reading order

### Phase E: Testing

- [ ] Test 3-panel layout with various stories
- [ ] Test 4-panel layout with various stories
- [ ] Validate mobile aspect ratio (9:16)
- [ ] QA visual consistency across panels

## File Locations (Estimated)

- Templates: `src/gossiptoon/video/panel_templates.py`
- Image composer: `src/gossiptoon/image/compositor.py`
- Scriptwriter: `src/gossiptoon/agents/scriptwriter.py`
- Image generator: `src/gossiptoon/image/generator.py`
- Config: `config/panel_templates.yaml`

## Data Structures

### Panel Template

```python
class PanelLayout(BaseModel):
    template_id: str
    panel_count: int
    aspect_ratio: tuple[int, int] = (9, 16)
    panels: list[PanelConfig]

class PanelConfig(BaseModel):
    panel_index: int
    x: int
    y: int
    width: int
    height: int

class PanelTemplate(str, Enum):
    TEMPLATE_A_3PANEL = "template_a_3panel"
    TEMPLATE_B_4PANEL = "template_b_4panel"
```

### Script Schema Update

```python
class Scene(BaseModel):
    # ... existing fields ...
    panel_template: PanelTemplate | None = None
    panel_descriptions: list[str] | None = None
    panel_bubbles: list[SpeechBubbleConfig] | None = None
```

## Scriptwriter Prompt Addition

```
Panel Layout Templates:
- template_a_3panel: 3 vertical panels (use for scenes with 3 key moments)
- template_b_4panel: 4 vertical panels (use for dialogue-heavy scenes)
- single_image: Traditional single image (use for establishing shots)

Select appropriate template based on scene complexity and pacing.
For panel layouts, provide separate image description for each panel.
```

## Acceptance Criteria

- [ ] 3-panel template generates correctly
- [ ] 4-panel template generates correctly
- [ ] Panels stitch seamlessly (no quality loss)
- [ ] Speech bubbles position correctly in panels
- [ ] Scriptwriter can select templates
- [ ] Mobile aspect ratio (9:16) maintained
- [ ] Visual consistency across panels
- [ ] Reading order flows naturally (top to bottom)

## Visual Quality Checklist

- [ ] Panel borders are clean and consistent
- [ ] No artifacts at panel boundaries
- [ ] Image resolution sufficient for mobile
- [ ] Colors consistent across panels
- [ ] Character consistency within panels

## Related Tickets

- TICKET-028: Standardize Character Design Sheets (character consistency)
- TICKET-031: High-Impact Text Overlay System (bubble integration)

## Notes

- **Art Style**: "Webtoon style" refers to Korean vertical webcomics
- **Mobile First**: 9:16 aspect ratio optimized for phone viewing
- **Reading Direction**: Top to bottom (standard webtoon flow)
- **Future**: Could add horizontal panel options for YouTube landscape
