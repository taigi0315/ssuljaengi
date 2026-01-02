# Ticket: Enhance Narrative Tone (Gossip Style)

## Context

The user feels the current scripts are "too clean" and "well-organized". They want the dialogue to sound more "imperfect", "communicational", and "powerful" – specifically referencing a "20-year-old woman talking to her friends" vibe (Gossip style).

## Requirements

- [ ] Update `ScriptWriterAgent` system prompt to shift tone from "professional webtoon" to "casual gossip/conversation".
- [ ] Instructions should encourage:
  - Slang, fillers, and natural speech patterns.
  - Emotional, reactive dialogue over expository narration.
  - "Imperfect" grammar where appropriate for character voice.
  - A "Us vs Them" or "Can you believe this?" framing.

## Implementation Details

1.  **Code**:
    - Modify `src/gossiptoon/agents/script_writer.py`: `SYSTEM_PROMPT`.
    - Adjust tone instructions to emphasize "Raw", "Unfiltered", "Juicy" content.

## DoD

- Generated scripts show a marked difference in tone (more casual, dramatic).
- User feedback confirms the "gossip" vibe is achieved.
