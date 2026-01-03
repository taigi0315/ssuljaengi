# PR: Narrative Tone Adjustment (Gossip Style)

**Ticket**: [TICKET-036](TICKET-036-narrative-tone.md)
**Branch**: `feature/ticket-036-narrative-tone`

## Summary

Updated the `ScriptWriterAgent` to shift the narrative tone from "professional webtoon" to **"Gossip Style"**. Generated characters will now sound more like real people gossiping, using imperfect speech, slang, and emotional reactions.

## Changes

- **`src/gossiptoon/agents/script_writer.py`**:
  - Updated `SYSTEM_PROMPT` to enforce "raw, unfiltered" tone.
  - Added explicit instructions for fillers (`um`, `like`), slang, and rhetorical questions.
  - Updated `_create_scaffold_system_prompt` to ensure tone consistency during scaffold filling.

## Verification

### Automated Tests

- Ran `tests/unit/test_script_writer_webtoon.py`: **Passed**.
- Confirmed JSON structure remains valid despite tone changes.

### Manual Verification

- Tone check (preview generation) confirms characters use new speech patterns.

## Checklist

- [x] System prompts updated
- [x] Scaffold filling prompt updated
- [x] Unit tests passed
- [x] Ticket moved to `tickets/done/`
