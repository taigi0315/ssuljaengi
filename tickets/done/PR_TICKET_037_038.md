# Voice Gender Fix & Visual Enhancements (TICKET-037, TICKET-038)

## Summary

This PR implements two key improvements:

1. **TICKET-037**: Fixes voice gender mismatch by ensuring male characters receive male voices
2. **TICKET-038**: Enhances visual quality with a new `VisualDetailerAgent` and dynamic style injection

## Changes

### TICKET-037: Voice Gender Fix

- **Updated `ScriptWriterAgent`**: Added `speaker_gender` requirement in scaffold prompt
- **Enhanced `AudioGenerator`**:
  - Passes `character_profiles` gender map through audio generation pipeline
  - Falls back to gender map if `speaker_gender` is missing from LLM output
  - Defaults to "female" if character not found
- **Added Tests**: `tests/unit/test_audio_gender_logic.py` (2 tests)

### TICKET-038: Visual Enhancements

- **Created `VisualDetailerAgent`**: New agent enriches scene descriptions with:
  - Specific lighting details
  - Camera angles
  - Facial micro-expressions
- **Integrated into Pipeline**: Runs as Step 4 after script validation
- **Dynamic Style Template**: `VisualDirector` now uses configurable style parameter
- **Added Tests**: `tests/unit/test_visual_detailer.py` (1 test)

## Files Modified

- `src/gossiptoon/agents/script_writer.py`
- `src/gossiptoon/audio/generator.py`
- `src/gossiptoon/pipeline/orchestrator.py`
- `src/gossiptoon/visual/director.py`

## Files Created

- `src/gossiptoon/agents/visual_detailer.py`
- `tests/unit/test_audio_gender_logic.py`
- `tests/unit/test_visual_detailer.py`

## Testing

All tests pass:

```
======== 3 passed, 20 warnings in 5.50s =========
```

## Checklist

- [x] Code follows project style guidelines
- [x] Unit tests added and passing
- [x] No breaking changes
- [x] Documentation updated (walkthrough.md)
