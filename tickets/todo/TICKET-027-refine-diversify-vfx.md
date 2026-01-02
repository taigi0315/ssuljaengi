# TICKET-027: Refine and Diversify Visual Effects (VFX)

**Priority**: Medium (P2)
**Status**: Todo
**Assignee**: AI Agent
**Created**: 2026-01-01
**Depends On**: None

## Problem

Current "Shake" effect is too aggressive and lasts too long, causing viewer discomfort and potential motion sickness. Limited VFX variety reduces visual interest and creative expression.

## Goal

1. Fix shake effect intensity and duration
2. Implement diverse movement types (Zoom In/Out, Pan Left/Right, Slow/Fast Shake)
3. Expose VFX options to LLM for intelligent scene-based selection

## Requirements

### VFX Types to Implement

1. **Shake Variants**
   - Slow shake (subtle tension)
   - Fast shake (intense action)
   - Limited duration (max 1.5 seconds)

2. **Zoom Effects**
   - Zoom in (focus, revelation)
   - Zoom out (context, surprise)
   - Speed variants (slow/fast)

3. **Pan Effects**
   - Pan left
   - Pan right
   - Pan up/down (optional)

4. **Static**
   - No movement (dialogue, calm scenes)

### Technical Requirements

1. **VFX Parameters**
   - Effect type enum (shake_slow, shake_fast, zoom_in, zoom_out, pan_left, pan_right, static)
   - Intensity (0.0 - 1.0)
   - Duration (max enforced by Evaluator)
   - Easing function (linear, ease_in, ease_out)

2. **Evaluator Constraints**
   - Max shake duration: 1.5 seconds
   - Max zoom duration: 3.0 seconds
   - Prevent consecutive intense effects
   - Validate effect appropriateness

3. **LLM Integration**
   - Add VFX options to scriptwriter prompt
   - Provide effect descriptions and use cases
   - Allow LLM to select effect per scene

## Implementation Plan

### Phase A: VFX Library Expansion

- [ ] Audit existing VFX implementation
- [ ] Implement zoom_in and zoom_out effects
- [ ] Implement pan_left and pan_right effects
- [ ] Add shake intensity variants (slow/fast)
- [ ] Test each effect independently

### Phase B: Duration & Intensity Constraints

- [ ] Add max duration enforcement to Evaluator
- [ ] Implement intensity scaling
- [ ] Add easing functions
- [ ] Test shake duration limits

### Phase C: LLM Integration

- [ ] Update scriptwriter prompts with VFX options
- [ ] Add effect selection to script schema
- [ ] Provide LLM with effect guidelines
- [ ] Test LLM effect selection quality

### Phase D: Validation & Testing

- [ ] Add VFX validation to Evaluator
- [ ] Test effect transitions
- [ ] QA for motion sickness triggers
- [ ] End-to-end testing with various stories

## File Locations (Estimated)

- VFX module: `src/gossiptoon/video/effects.py`
- Evaluator: `src/gossiptoon/agents/evaluator.py`
- Scriptwriter: `src/gossiptoon/agents/scriptwriter.py`
- Prompts: `src/gossiptoon/prompts/scriptwriter_prompts.py`

## API Design

### VFX Schema

```python
class VFXEffect(str, Enum):
    STATIC = "static"
    SHAKE_SLOW = "shake_slow"
    SHAKE_FAST = "shake_fast"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"

class VFXConfig(BaseModel):
    effect: VFXEffect
    intensity: float = Field(ge=0.0, le=1.0, default=0.5)
    duration: float = Field(gt=0.0, le=3.0)
    easing: str = "ease_out"
```

### Evaluator Validation

```python
class VFXValidator:
    MAX_SHAKE_DURATION = 1.5
    MAX_ZOOM_DURATION = 3.0

    def validate_vfx(self, scene: Scene) -> ValidationResult:
        """Validate VFX parameters."""
        if scene.vfx.effect.startswith("shake"):
            if scene.vfx.duration > self.MAX_SHAKE_DURATION:
                return ValidationResult(
                    valid=False,
                    error=f"Shake duration {scene.vfx.duration}s exceeds max {self.MAX_SHAKE_DURATION}s"
                )
```

## LLM Prompt Addition

```
Available Visual Effects:
- static: No movement (for dialogue, calm moments)
- shake_slow: Subtle shake (tension, unease)
- shake_fast: Intense shake (action, shock) [MAX 1.5s]
- zoom_in: Zoom into image (focus, revelation)
- zoom_out: Zoom out from image (surprise, context)
- pan_left: Pan camera left (exploration)
- pan_right: Pan camera right (exploration)

Select appropriate effect based on scene emotion and pacing.
```

## Acceptance Criteria

- [ ] All 7 VFX types implemented and working
- [ ] Shake effects respect 1.5s max duration
- [ ] LLM can select effects in scriptwriter
- [ ] Evaluator validates VFX parameters
- [ ] No motion sickness triggers in testing
- [ ] Effect transitions are smooth
- [ ] Documentation for each effect type

## QA Checklist

- [ ] Test each effect with 3+ different scenes
- [ ] Verify shake doesn't cause discomfort
- [ ] Check zoom doesn't lose image quality
- [ ] Validate pan stays within image bounds
- [ ] Test effect combinations/transitions

## Related Tickets

- TICKET-025: Fix Missing SFX (SFX should complement VFX)
- TICKET-030: Enhance Narrative Dramatization (effects support storytelling)

## Notes

- **User Feedback**: Current shake is "too aggressive and lasts too long"
- **Accessibility**: Consider adding motion reduction mode
- **Future**: Add rotation, blur, color grading effects
