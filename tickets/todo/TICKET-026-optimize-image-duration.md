# TICKET-026: Optimize Image Duration for Better Pacing

**Priority**: High (P1)
**Status**: Todo
**Assignee**: AI Agent
**Created**: 2026-01-01
**Depends On**: None

## Problem

Current image duration (6-10 seconds per image) is too slow and harms viewer retention. YouTube Shorts and TikTok audiences expect faster-paced content for engagement.

## Goal

Reduce maximum image duration to 3-4 seconds to create dynamic visual flow and improve audience retention metrics.

## Requirements

### Functional Requirements

1. **Duration Limits**
   - Maximum duration: 4 seconds per image
   - Minimum duration: 2 seconds per image
   - Target average: 3 seconds per image

2. **Script Validation**
   - Update `Scriptwriter` to generate scripts with shorter image durations
   - Update `Evaluator` to enforce duration constraints
   - Reject or fix scripts that exceed limits

3. **Backward Compatibility**
   - Add configuration flag for duration mode (slow/fast)
   - Allow override for specific content types

### Technical Requirements

1. **Scriptwriter Module**
   - Update script generation prompts
   - Add duration calculation logic
   - Balance narration length with visual pacing

2. **Evaluator Module**
   - Add duration validation rules
   - Calculate total video length
   - Flag scenes exceeding max duration

3. **Configuration**
   - Add `max_image_duration` setting
   - Add `min_image_duration` setting
   - Add `target_pacing` mode (slow/medium/fast)

## Implementation Plan

### Phase A: Analysis

- [ ] Analyze current duration distribution
- [ ] Review scriptwriter duration logic
- [ ] Review evaluator validation rules
- [ ] Identify all duration-related code

### Phase B: Scriptwriter Updates

- [ ] Update LLM prompts to target 3-4s duration
- [ ] Add explicit duration constraints
- [ ] Test script generation with new constraints
- [ ] Validate narration fits within duration

### Phase C: Evaluator Updates

- [ ] Add duration validation to evaluator
- [ ] Implement max duration enforcement
- [ ] Add repair strategies for violations
- [ ] Add duration metrics to evaluation report

### Phase D: Configuration & Testing

- [ ] Add duration settings to config
- [ ] Update default configuration
- [ ] Test with various story lengths
- [ ] Measure retention impact (manual QA)

## File Locations (Estimated)

- Scriptwriter: `src/gossiptoon/agents/scriptwriter.py`
- Evaluator: `src/gossiptoon/agents/evaluator.py`
- Config: `config/video_config.yaml`
- Prompts: `src/gossiptoon/prompts/scriptwriter_prompts.py`

## API Changes

### Configuration Schema

```yaml
video:
  pacing:
    mode: fast  # slow, medium, fast
    min_image_duration: 2.0
    max_image_duration: 4.0
    target_image_duration: 3.0
```

### Script Schema Validation

```python
class SceneValidation:
    def validate_duration(self, scene: Scene) -> ValidationResult:
        """Ensure scene duration is within limits."""
        if scene.duration > config.max_image_duration:
            return ValidationResult(
                valid=False,
                error=f"Duration {scene.duration}s exceeds max {config.max_image_duration}s"
            )
```

## Acceptance Criteria

- [ ] Scriptwriter generates scripts with 3-4s avg duration
- [ ] Evaluator rejects scenes exceeding 4s duration
- [ ] Configuration settings work correctly
- [ ] Existing scripts can be regenerated with new pacing
- [ ] No narration cutoff issues
- [ ] Overall video feels more dynamic

## Metrics to Track

- Average scene duration (before/after)
- Video completion rate (if YouTube analytics available)
- Total video length changes

## Related Tickets

- TICKET-030: Enhance Narrative Dramatization (both affect pacing)

## Notes

- **Impact**: HIGH - Directly affects viewer retention
- **Risk**: Narration might feel rushed; test thoroughly
- **Consideration**: May need faster TTS speaking rate to fit narration
