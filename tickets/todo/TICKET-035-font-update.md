# Ticket: Update Font to NanumMyeongjo

## Context

The user reported broken text in the output video and requested a font change. They provided new font assets (`NanumMyeongjo` family) which have been added to the repository.

## Requirements

- [ ] Update `VideoAssembler` / `FFmpegBuilder` to use the new `NanumMyeongjo` fonts.
- [ ] Support both "Bold" (for emphasis) and "Regular" (for normal text) weights.
  - Current logic likely uses a single font file.
  - Need to map "High Impact" text to `NanumMyeongjoExtraBold.ttf` (or Bold) and normal text to `NanumMyeongjo.ttf`.
- [ ] Verify that Korean text renders correctly without "tofu" boxes.

## Implementation Details

1.  **Assets**:
    - `assets/fonts/nanum-myeongjo/NanumMyeongjo.ttf`
    - `assets/fonts/nanum-myeongjo/NanumMyeongjoExtraBold.ttf`
2.  **Code**:
    - Modify `src/gossiptoon/video/assembler.py` to point to the new font paths.
    - Modify `src/gossiptoon/video/subtitles.py` to use the correct font family name in ASS styles.
    - Ensure `FFmpegBuilder` correctly mounts the font directory.

## DoD

- Video generation completes.
- Subtitles use NanumMyeongjo.
- No broken characters in Korean text.
