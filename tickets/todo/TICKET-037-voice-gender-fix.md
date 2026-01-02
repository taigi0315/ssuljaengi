# Ticket: Fix Voice Gender Mismatch

## Context

The user reported that the main character (Male) was assigned a female voice. We need to ensure that the voice selection logic correctly respects the character's gender defined in the script.

## Requirements

- [ ] Investigate `ScriptWriterAgent` to ensure `speaker_gender` in `audio_chunks` correctly matches the defined `CharacterProfile`.
- [ ] Investigate `AudioGenerator` (or `GoogleTTSClient`) to ensure it correctly maps the requested "male"/"female" gender to the appropriate voice ID.
- [ ] Add validation or logging to alert if a mismatch is detected (e.g., character is Male but chunk says Female).

## Implementation Details

1.  **Code**:
    - `src/gossiptoon/agents/script_writer.py`: Check prompt instructions for gender consistency.
    - `src/gossiptoon/audio/generator.py`: Verify `get_recommended_voice_for_gender` usage.
    - `src/gossiptoon/audio/google_tts_client.py`: Verify voice banking/gender mapping.

## DoD

- Generated audio matches the character's gender.
- Male characters always get Male voices detailed in `google_tts_client.py`.
