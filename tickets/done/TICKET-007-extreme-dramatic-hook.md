# Ticket: TICKET-007-extreme-dramatic-hook

## Context

The user wants to maximize viewer retention by modifying the video start (0-3s).
Currently, videos might start chronologically or slowly.
The goal is to enforce an **"Extreme Dramatic Hook"**:

- Start with the most shocking/dramatic moment (Panic, Scream, Shocking Question).
- Can be a flash-forward to the Climax.
- Or a shocking out-of-context statement (e.g., "Did you shrink it?!").
- Duration: Strictly 0-3 seconds.

## Design / Architecture

- **ScriptWriter Agent**: Update the system prompt to enforce the "Cold Open" structure.
  - Act 1 (Hook) MUST be high-energy/shocking.
  - If the story is chronological, the Agent should pick the climax and pull a snippet to the front, or manufacture a "teaser" line.
- **Structure**:
  - Act 1: The Hook (0-3s) - Shocking/Confusing/High Stakes.
  - Act 2: Rewind/Context ("Let me explain", or just jump to chronological start).

## Tasks

- [x] Analyze `ScriptWriter` prompts in `src/gossiptoon/agents/script_writer.py` <!-- id: 1 -->
- [x] Modify System Prompt to enforce "Shocking First 3 Seconds" <!-- id: 2 -->
- [x] Update `Script` model or `Scene` validation if needed (ensure Hook is short) <!-- id: 3 -->
- [x] Verify with a test script generation (using `outputs/` or a new test) <!-- id: 4 -->

## Acceptance Criteria

- [x] Generated scripts always start with a high-intensity scene (Emotion: Shock/Anger/Panic).
- [x] The first scene duration is short (<5s).
- [x] The narrative structure supports the "In Media Res" or "Teaser" format.
