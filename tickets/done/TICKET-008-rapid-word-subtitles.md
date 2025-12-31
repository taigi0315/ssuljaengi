# Ticket: TICKET-008-rapid-word-subtitles

## Context

The user wants to increase viewer engagement with rapid, word-by-word subtitles (Alex Hormozi style / TikTok style).

- **Source**: Use Whisper timestamps (already available).
- **Format**: Word-by-word (or small chunks).
- **Position**: 70% from top (y=0.7\*H).
- **Style**: Random pastel colors for each word event.
- **Current State**: No subtitles are being overlaid.

## Design / Architecture

- **Audio Processing**: Ensure `WhisperTranscriber` returns word-level timestamps (`word_timestamps=True`).
- **Subtitle Generation**:
  - Instead of burning full sentence subtitles, we will generate an ASS/SRT file (or drawtext commands) where each "dialogue" line is just one word (or 2-3 words) with its specific start/end time.
- **Visual styling in `FFmpegBuilder`**:
  - Implement a `generate_dynamic_subtitles` method.
  - Generates ASS (Advanced Substation Alpha) file for easier styling (colors, positioning) than complex filter_complex chains.
  - Or, use multiple `drawtext` filters (might be slow/complex). **Decision**: ASS file is standard for this.
  - **Random Colors**: Generate a palette of pastel colors and pick one randomly for each word event in the ASS file.

## Tasks

- [x] Verify `WhisperTranscriber` configuration for word timestamps <!-- id: 1 -->
- [x] Create `SubtitleGenerator` helper to convert Whisper JSON to "Word-Level ASS" <!-- id: 2 -->
- [x] Implement random pastel color logic <!-- id: 3 -->
- [x] Update `VideoAssembler` to integrate the subtitle overlay step <!-- id: 4 -->
- [x] Verify with `manual_reassemble.py` <!-- id: 5 -->

## Acceptance Criteria

- [x] Video has open captions overlaid.
- [x] Captions appear word-by-word (rapid fire).
- [x] Colors change randomly (pastel palette) per word.
- [x] Position is ~70% down the screen.
