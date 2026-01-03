# TICKET-042: Composite Panel Generation (CRITICAL - Cost Savings)

## Priority

**🔴 CRITICAL** (Cost Optimization)

## Problem

Currently generating 3 separate images for 3-panel scenes costs 3x API calls.

### Current Approach

```
Scene with template_a_3panel:
- Panel 1: API call → image1.png ($$$)
- Panel 2: API call → image2.png ($$$)
- Panel 3: API call → image3.png ($$$)
Total: 3 API calls
```

### Cost Impact

- Average script: ~19 scenes
- ~40% use multi-panel templates (3-4 panels)
- Current: ~50 image generation calls per video
- **Potential savings: 66% reduction** (50 → ~20 calls)

## Proposed Solution

### Approach: Single Composite Image

```
Scene with template_a_3panel:
- Generate 1 composite image with prompt:
  "Create a 3-panel Korean webtoon layout in vertical format:

   [Panel 1 - Top]
   {panel_1_description}

   [Panel 2 - Middle]
   {panel_2_description}

   [Panel 3 - Bottom]
   {panel_3_description}

   Style: Cinematic Korean manhwa, clear panel divisions"

Total: 1 API call (66% cost savings!)
```

## Technical Challenges

### Challenge 1: Prompt Engineering

- **Question**: Can Gemini Imagen handle multi-panel layouts?
- **Test Needed**: Generate sample composite images
- **Fallback**: If quality is poor, keep current approach

### Challenge 2: Panel Layout Specification

- Need to specify panel arrangement (vertical stacking)
- Panel borders/divisions
- Consistent character appearance across panels

### Challenge 3: Template Variations

- `template_a_3panel`: 3 panels vertical
- `template_b_4panel`: 4 panels (2x2 grid? or vertical?)
- Need clear layout instructions for each

## Implementation Plan

### Phase 1: Research & Prototyping

1. **Test Gemini Imagen Capabilities**

   ```python
   # Test prompt
   prompt = """Create a 3-panel Korean webtoon comic layout:

   Panel 1 (Top): Close-up of shocked girl with wide eyes
   Panel 2 (Middle): Girl looking at phone with confused expression
   Panel 3 (Bottom): Girl covering face with hands in frustration

   Style: Korean manhwa, clear black borders between panels, vertical layout"""
   ```

2. **Evaluate Quality**

   - Panel separation clarity
   - Character consistency
   - Overall composition

3. **Decision Point**: Proceed or fallback to current approach

### Phase 2: Implementation (if Phase 1 succeeds)

#### Step 1: Modify `VisualDirector.generate_scene_visuals()`

```python
async def generate_scene_visuals(self, scene: Scene, ...) -> SceneVisuals:
    if scene.panel_template == "single_image":
        # Current approach: 1 image
        return await self._generate_single_image(scene)
    else:
        # NEW: Composite multi-panel image
        return await self._generate_composite_panels(scene)
```

#### Step 2: Create `_generate_composite_panels()`

```python
async def _generate_composite_panels(self, scene: Scene) -> SceneVisuals:
    # Build composite prompt
    panel_count = len(scene.panel_descriptions)
    layout = self._get_layout_instruction(scene.panel_template)

    composite_prompt = f"""Create a {panel_count}-panel Korean webtoon layout:

    {layout}

    {self._format_panel_descriptions(scene.panel_descriptions)}

    Style: {scene.visual_description}
    Clear black borders between panels."""

    # Generate single composite image
    image_path = await self.image_client.generate_image(composite_prompt)

    return SceneVisuals(
        scene_id=scene.scene_id,
        images=[image_path],  # Single composite image
        panel_layout=scene.panel_template
    )
```

#### Step 3: Layout Instructions

```python
def _get_layout_instruction(self, template: str) -> str:
    layouts = {
        "template_a_3panel": "Vertical layout with 3 panels stacked top to bottom",
        "template_b_4panel": "2x2 grid layout with 4 panels",
    }
    return layouts.get(template, "")
```

### Phase 3: Testing

1. Generate test videos with composite panels
2. Compare quality vs. current approach
3. Verify cost savings (monitor API calls)
4. User validation

## Acceptance Criteria

- [ ] Composite panel generation working for `template_a_3panel`
- [ ] Composite panel generation working for `template_b_4panel`
- [ ] Panel borders clearly visible
- [ ] Character consistency across panels in same scene
- [ ] **66% reduction in image generation API calls**
- [ ] Visual quality acceptable (user validation)

## Fallback Plan

If composite generation quality is poor:

- Keep current multi-image approach
- Explore alternative: Use cheaper image generation API for panels
- Consider: Generate panels sequentially with character reference

## Files to Modify

- `src/gossiptoon/visual/director.py`
- `src/gossiptoon/models/visual.py` (if needed)

## Testing Strategy

1. **Phase 1 Testing** (Prototyping):

   - Generate 10 test composite images
   - Manual quality review
   - Go/No-go decision

2. **Phase 2 Testing** (Integration):

   - Generate 3 full test videos
   - Compare with current approach
   - Cost analysis

3. **User Validation**:
   - Present samples to user
   - Get feedback on quality

## Estimated Effort

- **Phase 1** (Prototyping): 1-2 hours
- **Phase 2** (Implementation): 3-4 hours
- **Phase 3** (Testing): 2 hours
- **Total**: 6-8 hours

## ROI Analysis

- **Current Cost**: ~50 image calls × $0.XX = $XX per video
- **New Cost**: ~20 image calls × $0.XX = $XX per video
- **Savings**: ~$XX per video (66%)
- **Monthly Savings** (100 videos): ~$XXX

## Notes

- This is a **cost optimization**, not a quality improvement
- Quality must not degrade significantly
- If Gemini Imagen can't handle it, explore alternatives
- Consider this AFTER fixing story repetition (TICKET-041)
