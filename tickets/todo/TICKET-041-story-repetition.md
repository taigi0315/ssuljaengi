# TICKET-041: Fix Story Repetition with Feedback Loop (CRITICAL)

## Priority

**🔴 CRITICAL**

## Problem

Acts repeat similar emotional beats and dialogue, making the story feel repetitive.

### Example

- BUILD: "She wanted to meet my _mom_?"
- CRISIS: "My mom? Seriously?! Like, she thinks she can just waltz in?"
- CLIMAX: "Seriously, how DARE she just waltz in? Thinking she can just meet my mom?"

**Same question repeated 3 times!**

## Root Cause

1. ScriptWriter fills each Act without seeing previous act content
2. ScriptEvaluator only validates structure, not story coherence
3. **No feedback loop** - bad scripts proceed to audio/visual generation (waste!)

## Solution: LLM-Based Evaluation + Feedback Loop

### Key Insight

**ScriptEvaluator is an LLM** - it can understand and evaluate story content!

### Architecture Change

**BEFORE** (One-way pipeline):

```
ScriptWriter → ScriptEvaluator → Audio → Visuals
                     ↓
                  (issues?)
                     ↓
                  ❌ Proceed anyway (WASTE!)
```

**AFTER** (Feedback loop):

```
ScriptWriter → ScriptEvaluator
                     ↓
              Coherence Check
                     ↓
              is_coherent?
                /        \
              YES        NO
               ↓          ↓
            Audio    Retry (max 3x)
                         ↓
                   Regenerate Script
```

## Implementation

### Phase 1: ScriptWriter - Add Previous Act Context

```python
# Track filled acts
filled_acts = []
for act in scaffold.acts:
    # Pass previous acts to LLM
    filled_act = await self._fill_single_act(story, scaffold, act, filled_acts)
    filled_acts.append(filled_act)
```

### Phase 2: ScriptEvaluator - Add Coherence Check

```python
class ValidationResult(BaseModel):
    script: Script
    is_coherent: bool
    issues: list[str] = []

async def validate_script(self, script: Script, story: Story) -> ValidationResult:
    # QA validation
    validated = await self._qa_validation(script, story)

    # NEW: Coherence check (LLM reads story)
    coherence = await self._check_story_coherence(validated, story)

    return ValidationResult(
        script=validated,
        is_coherent=coherence.is_coherent,
        issues=coherence.issues
    )
```

**Coherence Check Prompt**:

```
You are a Story Editor. Read this script and evaluate:

1. Does each act introduce NEW information?
2. Are there repeated questions or reactions?
3. Do acts repeat the same emotional beats?

Output:
- is_coherent: true/false
- issues: ["CRISIS and CLIMAX repeat 'how dare she' reaction"]
```

### Phase 3: Orchestrator - Add Feedback Loop (CRITICAL!)

```python
async def _generate_script(self, story: Story) -> Script:
    max_attempts = 3

    for attempt in range(1, max_attempts + 1):
        # 1. Generate script
        scaffold = await self.scene_structurer.generate_scaffold(story)
        script = await self.script_writer.fill_scaffold(scaffold, story)

        # 2. Validate with coherence check
        result = await self.script_evaluator.validate_script(script, story)

        # 3. Check if coherent
        if result.is_coherent:
            logger.info("✅ Script passed coherence check")
            return result.script

        # 4. Reject - log and retry
        logger.warning(f"❌ Script rejected (attempt {attempt}): {result.issues}")

        if attempt < max_attempts:
            logger.info("🔄 Regenerating script...")
            await asyncio.sleep(2)

    # All attempts failed
    raise ScriptGenerationError(f"Failed after {max_attempts} attempts")
```

**Why This is Critical**:

- ✅ Prevents wasted API calls (no audio/visuals with bad script)
- ✅ Ensures quality before expensive operations
- ✅ Automatic retry with fresh generation
- ✅ Clear failure reporting

## Files to Modify

- `src/gossiptoon/agents/script_writer.py`
- `src/gossiptoon/agents/script_evaluator.py`
- `src/gossiptoon/pipeline/orchestrator.py`
- `src/gossiptoon/models/script.py` (add `ValidationResult`)

## Acceptance Criteria

- [ ] ScriptWriter passes previous act content
- [ ] ScriptEvaluator performs coherence check
- [ ] Orchestrator implements retry loop
- [ ] Bad scripts are rejected and regenerated
- [ ] Test: Generate 3 scripts, verify no repetition

## Estimated Effort

- Phase 1: 2 hours
- Phase 2: 3 hours
- Phase 3: 2 hours
- Testing: 1 hour
- **Total: 8 hours**

## Why LLM-Based is Better

✅ Understands semantics, not just syntax  
✅ Catches subtle repetition  
✅ Provides actionable feedback  
✅ Aligns with existing architecture

## Notes

- This is like LangGraph's conditional edges, but simpler
- Future: Could use actual LangGraph for more complex workflows
- This prevents the biggest waste: generating audio/visuals with bad script
