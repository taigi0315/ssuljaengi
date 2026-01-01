# TICKET-021: Implement Strict Schema Validation

**Priority**: Medium (P2)  
**Status**: Blocked  
**Assignee**: AI Agent  
**Created**: 2025-12-31  
**Blocked By**: Gemini API schema compatibility issues

## Problem

Gemini LLM generates invalid enum values (e.g., `exasperated`, `bewildered`) that don't match our Pydantic model, causing validation errors and pipeline failures during script generation.

## Attempted Solutions

### Attempt 1: Native Gemini API `response_schema`

- **Method**: Use `genai.GenerationConfig(response_schema=Script)`
- **Result**: ❌ Failed - Pydantic `Field(example=...)` not compatible with Gemini schema
- **Error**: `Unknown field for Schema: example`

### Attempt 2: LangChain `with_structured_output()`

- **Method**: Use `ChatGoogleGenerativeAI.with_structured_output(Script)`
- **Result**: ❌ Failed - Schema not fully enforced
- **Error**: Gemini omitted required fields like `Scene.act`
- **Commits**: Reverted in commit `[revert commit hash]`

## Root Cause Analysis

1. **LangChain → Gemini conversion incomplete**: LangChain doesn't properly translate all Pydantic constraints to Gemini's schema format
2. **Pydantic metadata incompatibility**: Fields like `example`, `description` with complex values break Gemini schema parser
3. **Enum constraints not enforced**: Even with schema, Gemini generates out-of-enum values

## Proposed Solutions (Future Work)

### Option A: Custom JSON Schema Generation ⭐ Recommended

Generate Gemini-compatible JSON schema manually from Pydantic model:

```python
def pydantic_to_gemini_schema(model: Type[BaseModel]) -> dict:
    # Custom converter that removes incompatible fields
    # Ensures all enums are properly constrained
    pass
```

### Option B: Post-Processing Validation Layer

Accept any LLM output, then normalize/fix in post-processing:

```python
def normalize_script(raw_script: dict) -> Script:
    # Fill missing fields with defaults
    # Map invalid enum values to closest valid ones
    # Validate and retry specific fields if needed
    pass
```

### Option C: Prompt Engineering Enhancement

Strengthen system prompt to explicitly list allowed values:

- List all emotions in prompt
- Provide examples for each field
- Use few-shot examples

## Temporary Workaround

**Current approach**: Add new emotions to `EmotionTone` enum as Gemini generates them.

**Added so far**:

- `FRUSTRATED`
- `DETERMINED`
- `RELIEVED`
- `EXASPERATED`

This is **reactive** but keeps pipeline working.

## Implementation Plan (When Unblocked)

1. Research Gemini 2.5 Flash schema capabilities
2. Implement custom Pydantic → Gemini schema converter
3. Add unit tests for schema generation
4. Test with E2E pipeline
5. Monitor for new validation errors

## Acceptance Criteria

- [ ] No Pydantic validation errors during script generation
- [ ] All enum fields strictly validated at generation time
- [ ] No required fields missing from LLM output
- [ ] E2E test passes without retries

## Related Tickets

- TICKET-020: Subtitle Fix (unrelated)
- TICKET-018: Auto-Crawler (unrelated)

## Notes

- This ticket is **blocked** until we find a compatible schema enforcement method
- Consider upgrading to Gemini Pro or exploring other providers (Claude, GPT-4) for better structured output support
- Track new invalid enum values in this ticket as they appear
