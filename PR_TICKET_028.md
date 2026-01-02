# TICKET-028: Standardized Character Sheets

## Problem

Currently, character designs are generated from the `visual_description` of the first scene where they appear. This often leads to:

1.  **Low Quality**: "Two people fighting in a kitchen" is used as the character reference prompt.
2.  **Inconsistency**: Lack of explicit age, build, and outfit details across scenes.
3.  **Hallucinations**: Reference images contain background elements or other characters, confusing subsequent generations.

## Solution

Implement a **Standardized Character Creating** pipeline:

1.  **Strict Prompt Template**: Use a professional animation character design sheet template.
2.  **Explicit Profiles**: Force the LLM (`ScriptWriterAgent`) to generate detailed profiles (Age, Gender, Vibe, Body, Hair, Face, Outfit) for all main characters.
3.  **Schema Enforcement**: Add `CharacterProfile` model to the Script schema.

## Changes

### 1. Schema (`src/gossiptoon/models/script.py`)

- Added `CharacterProfile` class using Pydantic.
- Added `character_profiles` list to `Script` model.

### 2. Agents (`src/gossiptoon/agents/script_writer.py`, `script_evaluator.py`)

- Updated System Prompt to demand character profiles.
- Updated Output Example Schema.
- Added validation rules to ensure profiles exist for all speakers.

### 3. Visual Director (`src/gossiptoon/visual/director.py`)

- Added `CHARACTER_SHEET_TEMPLATE` constant.
- Updated `_generate_character_portraits` to prioritize `character_profiles` over legacy scene descriptions.

## Testing

- Added `tests/unit/test_character_standardization.py`.
- Verified `Script` model validation.
- Verified prompt injection and template formatting.

## Next Steps

- Verify E2E generation with new `gossiptoon run` command.
- Move to **TICKET-029: Webtoon-Style Panel Layouts** to utilize these high-quality characters in dynamic compositions.
