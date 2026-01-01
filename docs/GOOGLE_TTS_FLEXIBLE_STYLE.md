# Google TTS Flexible Style Instructions

## Overview

Google TTS 클라이언트가 이제 **flexible style instructions**를 지원합니다. 기존 `EmotionTone` enum 외에도, 자유로운 string 형식의 style instruction을 전달할 수 있어 "audio emotion script writer agent"가 더 상세하고 context-aware한 style을 작성할 수 있습니다.

## Key Changes

### 1. WAV Format Output

- **Before**: PCM → WAV → MP3 변환
- **After**: PCM → WAV (변환 없음)
- **Reason**: 불필요한 변환 제거, 품질 손실 방지

### 2. Flexible Style Parameter

```python
async def generate_speech(
    text: str,
    voice_id: str,
    emotion: Optional[EmotionTone] = None,           # Backward compatibility
    style_instruction: Optional[str] = None,         # NEW: Flexible style
    output_path: Optional[Path] = None,
) -> Path:
```

**Priority**: `style_instruction` > `emotion` > plain text

## Usage Examples

### Example 1: Using EmotionTone (Backward Compatible)

```python
from gossiptoon.audio.google_tts_client import GoogleTTSClient
from gossiptoon.core.constants import EmotionTone

client = GoogleTTSClient(api_key="...")

# Old way still works
audio = await client.generate_speech(
    text="I can't believe this is happening!",
    voice_id="Aoede",
    emotion=EmotionTone.SHOCKED
)
# Prompt: "Say in a sudden gasp with wide-eyed surprise, sharp intake of breath, and disbelief: I can't believe this is happening!"
```

### Example 2: Custom Style Instruction (NEW)

```python
# Detailed, context-aware style
audio = await client.generate_speech(
    text="Shields at 20 percent, Captain!",
    voice_id="Puck",
    style_instruction="a dramatic dialogue from a Sci-Fi video game set inside a spaceship cockpit during a chaotic battle"
)
# Prompt: "Say in a dramatic dialogue from a Sci-Fi video game set inside a spaceship cockpit during a chaotic battle: Shields at 20 percent, Captain!"
```

### Example 3: Complex Scene-Specific Style

```python
# Audio emotion script writer agent can generate this
style = """
a tense whisper from a detective in a noir film,
speaking into a phone in a dimly lit alley at midnight,
with distant sirens in the background
"""

audio = await client.generate_speech(
    text="I found the evidence. Meet me at the usual place.",
    voice_id="Charon",
    style_instruction=style
)
```

### Example 4: Priority Demonstration

```python
# Both emotion and style_instruction provided
# style_instruction takes precedence
audio = await client.generate_speech(
    text="This is amazing!",
    voice_id="Kore",
    emotion=EmotionTone.HAPPY,  # Ignored
    style_instruction="an excited child seeing snow for the first time"  # Used
)
```

## Integration with Audio Emotion Script Writer Agent

### Workflow

```mermaid
graph LR
    A[Script Writer] --> B[Story Script]
    B --> C[Audio Emotion Agent]
    C --> D[Analyze Context]
    D --> E[Generate Style Instructions]
    E --> F[Google TTS Client]
    F --> G[WAV Audio Files]
```

### Audio Emotion Agent Output Example

```python
# Audio emotion agent analyzes the story and generates style instructions
audio_styles = [
    {
        "character": "Sarah",
        "line": "I can't believe you did this to me.",
        "style_instruction": "a betrayed friend confronting someone in a quiet coffee shop, voice trembling with hurt and anger",
        "voice": "Aoede"
    },
    {
        "character": "John",
        "line": "I had no choice.",
        "style_instruction": "a guilty confession with defensive undertones, spoken while avoiding eye contact",
        "voice": "Puck"
    }
]

# Generate audio for each line
for item in audio_styles:
    audio = await client.generate_speech(
        text=item["line"],
        voice_id=item["voice"],
        style_instruction=item["style_instruction"]
    )
```

## Style Instruction Best Practices

### Good Style Instructions

✅ **Specific and Descriptive**

```python
"a panicked scientist warning colleagues about an imminent explosion in a research lab"
```

✅ **Include Context**

```python
"a tired mother reading a bedtime story to her children, voice soft and soothing"
```

✅ **Describe Emotion + Setting**

```python
"an excited sports commentator announcing a last-second winning goal in a packed stadium"
```

### Less Effective

❌ **Too Vague**

```python
"happy"  # Use EmotionTone.HAPPY instead
```

❌ **Too Long/Complex**

```python
"a character who is feeling a mix of 15 different emotions while simultaneously..."  # Keep it focused
```

## Technical Details

### Prompt Building Logic

```python
# Priority order:
if style_instruction:
    prompt = f"Say in {style_instruction}: {text}"
elif emotion:
    prompt = f"Say in a {EMOTION_STYLE_DIRECTIVES[emotion]}: {text}"
else:
    prompt = text
```

### Output Format

- **Format**: WAV (PCM, 24kHz, mono, 16-bit)
- **Extension**: Automatically enforced to `.wav`
- **No Conversion**: Direct PCM to WAV, no MP3 step

## Migration Guide

### For Existing Code

No changes required! Existing code using `emotion` parameter continues to work:

```python
# This still works exactly as before
audio = await client.generate_speech(
    text="Hello",
    voice_id="Kore",
    emotion=EmotionTone.HAPPY
)
```

### For New Features

Add `style_instruction` for more control:

```python
# Enhanced version
audio = await client.generate_speech(
    text="Hello",
    voice_id="Kore",
    style_instruction="a cheerful greeting from a friendly shopkeeper welcoming a regular customer"
)
```

## Future Enhancements

- [ ] Audio emotion script writer agent implementation
- [ ] Style instruction templates library
- [ ] Context-aware style generation based on story genre
- [ ] Multi-turn conversation style consistency
