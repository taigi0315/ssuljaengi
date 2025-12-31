# TICKET-010: Hybrid Subtitle Logic

**User Request**:
Mix "Sentence by Sentence" (informative/story-telling) and "Word by Word" (intense/dramatic) subtitles.

**Logic Design**:

1. **Intensity Trigger**:
   - Use `AudioSegment.emotion` (from ElevenLabs metadata) as the primary trigger.
   - High arousal emotions (Anger, Fear, Excitement) -> **Rapid Mode**.
   - Low arousal emotions (Narration, Calm, Sadness) -> **Sentence Mode**.
2. **Text Analysis**:
   - Short, punchy sentences (e.g., "What?!", "No way.") -> **Rapid Mode**.
   - Long, complex sentences -> **Sentence Mode**.

**Implementation**:

- Update `SubtitleGenerator` to switch strategies per phrase/sentence.
- **Rapid Mode**: Existing logic (1 word per event, random colors, center-ish).
- **Sentence Mode**: Group words, standard white/yellow text, bottom position.

## Tasks

- [ ] Define "Intensity" heuristic in `SubtitleGenerator`. <!-- id: 1 -->
- [ ] Implement `generate_sentence_events` (grouping words). <!-- id: 2 -->
- [ ] Implement `generate_rapid_events` (existing). <!-- id: 3 -->
- [ ] Update `generate_ass_file` to switch modes dynamically. <!-- id: 4 -->

## Acceptance Criteria

- [ ] "Calm" scenes show full sentences/phrases.
- [ ] "Intense" scenes show rapid word-by-word captions.
- [ ] Visual transition between modes is smooth (or distinct but not broken).
