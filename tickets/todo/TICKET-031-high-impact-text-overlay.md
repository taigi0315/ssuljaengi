# TICKET-031: High-Impact Text Overlay System

**Priority**: Medium (P2)
**Status**: Todo
**Assignee**: AI Agent
**Created**: 2026-01-01
**Depends On**: None

## Problem

Current subtitle overlays are uniform and don't emphasize dramatic moments. Need bold, eye-catching text styling for high-impact words (screaming, shocking moments, "WTF" moments).

## Goal

Implement dynamic subtitle styling system that automatically identifies and emphasizes high-impact words with:
- Bold fonts
- Larger sizing
- Strong/irritating colors (bright reds, yellows, etc.)
- Optional effects (shake, pulse)

## Requirements

### Text Styling Variants

1. **Normal Subtitles**
   - Standard size and weight
   - White text with black outline (readable)
   - Used for regular dialogue

2. **High-Impact Subtitles**
   - Bold/extra-bold font weight
   - 1.5-2x larger size
   - Bright colors (red, yellow, orange, magenta)
   - Optional shake/pulse animation
   - Used for: screaming, shocking words, profanity, dramatic moments

3. **Trigger Words/Phrases**
   - Profanity (WTF, damn, hell, etc.)
   - Emotional exclamations (OMG, NO WAY, WHAT, etc.)
   - Screaming indicators (all caps in original text)
   - Dramatic verbs (screamed, yelled, exploded, etc.)
   - Shock words (unbelievable, insane, crazy, etc.)

### Technical Requirements

1. **Text Analysis**
   - Detect high-impact words in narration
   - Support custom trigger word list
   - Identify all-caps segments
   - Detect emotional intensity from script

2. **Styling Engine**
   - Apply different styles to text segments
   - Support color gradients
   - Support font weight variations
   - Support size variations within single subtitle

3. **Color Palette**
   - Bright red (#FF0000, #FF1744)
   - Electric yellow (#FFFF00, #FFD600)
   - Orange (#FF6D00)
   - Hot pink/magenta (#FF00FF, #E91E63)
   - Configurable color randomization

4. **Animation (Optional)**
   - Shake animation for intense words
   - Pulse/scale animation
   - Flash effect
   - Duration limits (not too annoying)

## Implementation Plan

### Phase A: Text Analysis

- [ ] Create trigger word dictionary
- [ ] Implement word classification (normal vs. high-impact)
- [ ] Add all-caps detection
- [ ] Test with various scripts

### Phase B: Styling Engine

- [ ] Implement multi-style text rendering
- [ ] Add bold font support
- [ ] Add size variation support
- [ ] Implement color application

### Phase C: Color & Animation

- [ ] Define high-impact color palette
- [ ] Implement color selection logic
- [ ] Add shake animation (optional)
- [ ] Add pulse animation (optional)

### Phase D: Integration

- [ ] Update subtitle generator to use new system
- [ ] Add configuration options
- [ ] Test with generated videos
- [ ] Adjust colors/intensities based on readability

## File Locations (Estimated)

- Subtitle renderer: `src/gossiptoon/video/subtitles.py`
- Text analyzer: `src/gossiptoon/video/text_analyzer.py` (new)
- Style config: `config/subtitle_styles.yaml`

## Data Structures

### Text Segment

```python
class TextSegment(BaseModel):
    text: str
    style: TextStyle
    start_time: float
    duration: float

class TextStyle(str, Enum):
    NORMAL = "normal"
    HIGH_IMPACT = "high_impact"
    EMPHASIS = "emphasis"

class SubtitleStyle(BaseModel):
    font_size: int
    font_weight: str  # normal, bold, extra-bold
    color: str  # hex color
    outline_color: str = "#000000"
    outline_width: int = 2
    animation: str | None = None  # shake, pulse, none
```

### Trigger Words Configuration

```yaml
trigger_words:
  profanity:
    - "wtf"
    - "damn"
    - "hell"
    - "shit"
  exclamations:
    - "omg"
    - "oh my god"
    - "no way"
    - "what"
    - "seriously"
  dramatic_verbs:
    - "screamed"
    - "yelled"
    - "exploded"
    - "shouted"
  shock_words:
    - "unbelievable"
    - "insane"
    - "crazy"
    - "shocking"
```

## Styling Logic

```python
def classify_text_segment(word: str) -> TextStyle:
    """Determine text style based on word content."""
    word_lower = word.lower()

    # Check trigger words
    if word_lower in TRIGGER_WORDS:
        return TextStyle.HIGH_IMPACT

    # Check all caps (intensity)
    if word.isupper() and len(word) > 2:
        return TextStyle.HIGH_IMPACT

    # Check surrounding punctuation (!, ?, ...)
    if has_emphatic_punctuation(word):
        return TextStyle.EMPHASIS

    return TextStyle.NORMAL
```

## Acceptance Criteria

- [ ] High-impact words automatically detected
- [ ] Bold/large styling applied to trigger words
- [ ] Bright colors (red/yellow/orange) used for emphasis
- [ ] Text remains readable over images
- [ ] No excessive animation (motion sickness)
- [ ] Configuration options for style intensity
- [ ] Works with existing subtitle pipeline

## Visual Examples

```
Normal: "I was at the grocery store"
High-Impact: "and she SCREAMED at me" (SCREAMED in bold red, 2x size)
High-Impact: "I couldn't believe what she said" (believe in yellow, bold)
High-Impact: "WTF was she thinking?" (WTF in magenta, extra-bold, shake)
```

## Configuration Options

```yaml
subtitles:
  high_impact:
    enabled: true
    size_multiplier: 1.8
    font_weight: "extra-bold"
    colors: ["#FF0000", "#FFFF00", "#FF6D00", "#FF00FF"]
    color_selection: random  # random, sequential, word-based
    animation:
      shake:
        enabled: false
        intensity: 0.3
        duration: 0.5
```

## Related Tickets

- TICKET-030: Enhance Narrative Dramatization (visual emphasis supports narrative)
- TICKET-029: Webtoon-Style Panel Layouts (text overlay integration)

## Notes

- **Readability First**: Ensure text is always readable (outline, contrast)
- **Not Too Annoying**: Limit animation frequency/intensity
- **Color Psychology**: Red = anger/shock, Yellow = attention, etc.
- **Accessibility**: Consider colorblind-friendly alternatives
