# Design: 3-Agent Structure-First Workflow

## Problem Statement

The current 2-agent workflow (ScriptWriter → ScriptEvaluator) is failing with schema validation errors:
- ScriptWriter generates 16k-19k character unstructured drafts
- ScriptEvaluator is overwhelmed with too many responsibilities
- Missing fields like `order`, `total_estimated_duration` not being populated
- Validation errors causing script generation failures

## Root Cause Analysis

**ScriptWriter** (Temperature 0.9):
- Responsible for creative content AND structure
- Generates large 19k char outputs
- Often misses required schema fields

**ScriptEvaluator** (Temperature 0.2):
- Has 9 different responsibilities
- Expected to "fix missing fields" but failing to do so
- Cognitive overload from complex prompt

## Proposed Solution: Structure-First 3-Agent Workflow

### Architecture

```
Story → SceneStructurer → ScriptWriter → ScriptEvaluator → Script
        (Structure)       (Creative)     (QA)
```

### Agent 1: SceneStructurer (NEW)

**Purpose**: Generate the structural scaffold for the script

**Temperature**: 0.1 (deterministic)

**Input**:
- Story object

**Output**:
- Script object with STRUCTURE ONLY:
  - `script_id`, `story_id`, `title`
  - `character_profiles` (inferred from story)
  - `acts` array (5 acts with correct `act_type`, `target_duration_seconds`)
  - `scenes` array per act with:
    - `scene_id` (generated)
    - `order` (0, 1, 2...)
    - `estimated_duration_seconds` (calculated)
    - `characters_present` (assigned)
    - `emotion` (placeholder)
  - `total_estimated_duration` (calculated sum)
  - ALL creative fields empty (`audio_chunks: []`, `visual_description: ""`, etc.)

**Responsibilities**:
1. Analyze story to identify 2-5 characters
2. Create character profiles with visual descriptions
3. Generate 5-act structure with correct timing
4. Pre-allocate scenes across acts with durations
5. Calculate all numeric fields (`order`, durations)
6. Ensure schema completeness (all required fields present)

**Benefits**:
- Small, focused task
- Deterministic output
- Guaranteed structural correctness
- No creative pressure

### Agent 2: ScriptWriter (MODIFIED)

**Purpose**: Fill the scaffold with creative content

**Temperature**: 0.9 (creative)

**Input**:
- Story object
- Script scaffold (from SceneStructurer)

**Output**:
- Complete Script with CREATIVE CONTENT filled in:
  - `audio_chunks` populated with dialogue/narration
  - `visual_description` written
  - `panel_layout` described
  - `bubble_metadata` created
  - `camera_effect`, `visual_sfx` assigned

**Responsibilities** (REDUCED):
1. Generate dialogue and narration for each scene
2. Write visual descriptions for image generation
3. Create webtoon panel layouts
4. Assign bubble metadata for dialogue
5. Select appropriate camera effects and SFX

**Benefits**:
- Receives structure as input (knows exactly what to fill)
- Smaller output (~10k chars instead of 19k)
- Focuses purely on creativity
- No structural thinking required

### Agent 3: ScriptEvaluator (SIMPLIFIED)

**Purpose**: Quality assurance and final validation

**Temperature**: 0.2 (validation)

**Input**:
- Complete Script (from ScriptWriter)
- Story (for context)

**Output**:
- Validated Script with minor fixes

**Responsibilities** (REDUCED):
1. Validate enum values (emotion, camera_effect)
2. Check audio chunk lengths
3. Verify character consistency
4. Normalize text for TTS (remove parentheticals)
5. Validate SFX usage (max 2 per video)
6. Warning-only validation (no hard fails)

**Benefits**:
- Simpler prompt
- Fewer responsibilities
- Less likely to fail
- Can trust structure is already correct

## Implementation Plan

### Phase 1: Create SceneStructurer Agent
1. Create `src/gossiptoon/agents/scene_structurer.py`
2. Define system prompt focused on structure generation
3. Use `with_structured_output(Script)` for schema compliance
4. Test independently with sample stories

### Phase 2: Modify ScriptWriter
1. Update system prompt to expect scaffold input
2. Change input parameters to accept scaffold
3. Focus prompt on creative content only
4. Remove structural responsibilities from prompt

### Phase 3: Simplify ScriptEvaluator
1. Remove field-patching logic from prompt
2. Focus on validation and enum fixing only
3. Reduce cognitive load

### Phase 4: Update Orchestrator
1. Modify `write_script` workflow in orchestrator
2. Add SceneStructurer call before ScriptWriter
3. Pass scaffold to ScriptWriter
4. Keep ScriptEvaluator as final step

### Phase 5: Testing
1. Test each agent independently
2. Test full pipeline with sample stories
3. Compare output quality with old 2-agent workflow
4. Measure success rate improvements

## Expected Outcomes

### Quantitative Improvements
- Script generation success rate: 60% → 95%+
- Average ScriptWriter output: 19k → 10k chars
- Validation errors: Common → Rare
- Missing field errors: Eliminated

### Qualitative Improvements
- Clearer separation of concerns
- Easier debugging (can inspect scaffold)
- Better maintainability
- More predictable outputs
- Reduced prompt complexity per agent

## Rollout Strategy

1. Implement on `agent` branch
2. Test extensively with various story types
3. Compare success rates with main branch
4. If successful, merge to main
5. If issues arise, iterate on agent prompts

## Risk Mitigation

**Risk**: SceneStructurer generates poor structure
- Mitigation: Low temp (0.1) for deterministic output
- Mitigation: Validate scaffold before passing to ScriptWriter

**Risk**: ScriptWriter ignores scaffold
- Mitigation: Clear prompt instructions to "fill the provided structure"
- Mitigation: Include scaffold validation in evaluator

**Risk**: Extra agent increases latency
- Mitigation: SceneStructurer is fast (small output)
- Mitigation: Can run in parallel with other operations if needed

## Success Metrics

1. Zero missing field errors - Structure guaranteed complete
2. Reduced validation errors - From ~12 per run to 0-2
3. Improved script quality - Better pacing, timing, structure
4. Higher success rate - 95%+ script generation success

---

Status: Design approved, ready for implementation
Branch: `agent`
Created: 2026-01-02
