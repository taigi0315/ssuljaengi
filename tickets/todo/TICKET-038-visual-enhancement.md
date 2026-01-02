# Ticket: Visual Enhancements & Detail Agent

## Context

The user feels the character creation is "extremely simple" and lacks consistency with the scene style. They also noted that scene images are too general (e.g., "mass" instead of specific details) and requested that a new agent handle the enrichment of visual descriptions to avoid overloading the ScriptWriter.

## Requirements

- [ ] **Global Style Injection**: Ensure `CHARACTER_SHEET_TEMPLATE` and other prompts explicitly use the project's global image style (e.g., "Korean Webtoon", "Cel-shaded") instead of hardcoded defaults.
- [ ] **Visual Detail Agent**: Create a new agent (or processing step) that runs AFTER script generation but BEFORE image generation.
  - **Input**: The raw `Scene` objects with basic descriptions.
  - **Task**: "Populate/Add more details" about facial expressions, lighting, angles, background clutter, etc.
  - **Output**: Enhanced `visual_description` and `panel_descriptions`.
- [ ] **Goal**: More "fine-tuned" images, better character consistency, and richer visual storytelling.

## Implementation Details

1.  **Code**:
    - `src/gossiptoon/visual/director.py`: Update prompt templates.
    - `src/gossiptoon/agents/visual_detailer.py` (New): Create `VisualDetailerAgent`.
    - `src/gossiptoon/pipeline/orchestrator.py`: Integrate the new agent into the pipeline.

## DoD

- Character portraits match the scene style.
- Scene descriptions are detailed and specific.
- Image quality is improved (less "general/messy").
