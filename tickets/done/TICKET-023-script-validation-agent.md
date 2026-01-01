# TICKET-023: Script Validation Agent Refactor

## Objective

Decouple creative scriptwriting from strict formatting/validation to improve script quality and schema compliance.

## Changes Implemented

1.  **Refactored `ScriptWriterAgent`**:

    - Simplified system prompt to focus on creativity (pacing, viral hooks, emotion) rather than JSON syntax.
    - Removed structured output constraints from the initial generation step.
    - Updated to delegate validation to the new `ScriptEvaluator`.

2.  **Created `ScriptEvaluator` Agent**:

    - New agent in `src/gossiptoon/agents/script_evaluator.py`.
    - Responsible for taking the creative draft and enforcing the strict `Script` Pydantic schema.
    - Handles Enum mapping (e.g., "mad" -> `EmotionTone.ANGRY`, "zoom" -> `CameraEffectType.ZOOM_IN`).
    - Enforces 5-act structure and timing/duration constraints.

3.  **Codebase Clean-up**:
    - Renamed `CameraEffect` to `CameraEffectType` in `src/gossiptoon/core/constants.py` to resolve name collisions.
    - Updated `models/script.py`, `models/visual.py`, `models/video.py`, and `video/effects/camera.py` to use consistent Enum naming.

## Verification

- Created `tests/manual/test_script_writer_refactor.py` to verify the new pipeline.
- Verified imports and dependency injection (`ConfigManager` passing).
- **Status**: Code is structurally correct. Execution hit `429 ResourceExhausted` (Gemini Free Tier limit), confirming the agent communicates with the API, though full end-to-end generation was limited by quota.

## Next Steps

- Run `tests/manual/test_script_writer_refactor.py` when API quota resets to verify full generation.
- Proceed with pipeline execution.
