# Google TTS Multi-Speaker Support

## Overview

Google TTS 클라이언트가 이제 **multi-speaker** 지원을 위해 확장되었습니다. 30개의 모든 Google TTS prebuilt voice가 gender 및 style 메타데이터와 함께 포함되어 있어, script writer가 character의 gender에 따라 적절한 voice를 자동으로 선택할 수 있습니다.

## Voice Selection API

### 1. Get All Voices with Metadata

```python
from gossiptoon.audio.google_tts_client import GoogleTTSClient

client = GoogleTTSClient(api_key="YOUR_API_KEY")

# Get all 30 voices with full metadata
voices = client.get_available_voices()

# Each voice includes:
# - id: Voice name
# - name: Voice name
# - gender: "male" or "female"
# - style: Voice characteristic (e.g., "breezy", "firm", "informative")
# - description: Detailed description
# - category: "prebuilt"
```

### 2. Filter Voices by Gender

```python
# Get all female voices (14 total)
female_voices = client.get_voices_by_gender("female")
# Returns: ['Achernar', 'Aoede', 'Autonoe', ...]

# Get all male voices (16 total)
male_voices = client.get_voices_by_gender("male")
# Returns: ['Achird', 'Algenib', 'Algieba', ...]
```

### 3. Get Recommended Voice for Character

```python
# Get recommended voice for a female character
voice = client.get_recommended_voice_for_gender("female", index=0)
# Returns: "Aoede" (first recommended female voice)

# Get second female voice for variety
voice = client.get_recommended_voice_for_gender("female", index=1)
# Returns: "Kore" (second recommended female voice)

# Get recommended voice for a male character
voice = client.get_recommended_voice_for_gender("male", index=0)
# Returns: "Puck" (first recommended male voice)
```

**Recommended Voices:**

- **Female**: Aoede, Kore, Laomedeia, Sulafat, Despina
- **Male**: Puck, Charon, Fenrir, Orus, Umbriel

## Complete Voice List

### Female Voices (14)

| Voice Name   | Style      | Description                                        |
| ------------ | ---------- | -------------------------------------------------- |
| Achernar     | soft       | Clear, mid-range tone; friendly and engaging       |
| Aoede        | breezy     | Clear, conversational, intelligent, and articulate |
| Autonoe      | bright     | Mature and resonant with a calm, measured pace     |
| Callirrhoe   | easy-going | Confident and professional; projects energy        |
| Despina      | smooth     | Warm, inviting, and trustworthy                    |
| Erinome      | clear      | Professional, articulate, and sophisticated        |
| Gacrux       | mature     | Smooth, confident, and authoritative               |
| Kore         | firm       | Energetic, youthful, and perky                     |
| Laomedeia    | upbeat     | Clear and inquisitive with energy                  |
| Leda         | youthful   | Composed, articulate, and professional             |
| Pulcherrima  | forward    | Bright, energetic, and highly upbeat               |
| Sulafat      | warm       | Warm, confident, and persuasive                    |
| Vindemiatrix | gentle     | Calm, mature, and composed                         |
| Zephyr       | bright     | Energetic and perky; youthful and positive         |

### Male Voices (16)

| Voice Name    | Style         | Description                                   |
| ------------- | ------------- | --------------------------------------------- |
| Achird        | friendly      | Youthful and clear with inquisitive quality   |
| Algenib       | gravelly      | Warm and confident with friendly authority    |
| Algieba       | smooth        | Smooth delivery                               |
| Alnilam       | firm          | Energetic with mid-to-low pitch               |
| Charon        | informative   | Smooth and conversational; trustworthy        |
| Enceladus     | breathy       | Energetic and enthusiastic                    |
| Fenrir        | excitable     | Friendly and conversational                   |
| Iapetus       | clear         | Friendly with casual, everyman quality        |
| Orus          | firm          | Mature, deeper, and resonant; wise elder      |
| Puck          | upbeat        | Clear, direct, and approachable               |
| Rasalgethi    | informative   | Conversational with inquisitive quality       |
| Sadachbia     | lively        | Deeper voice with slight rasp; cool authority |
| Sadaltager    | knowledgeable | Friendly and enthusiastic; professional       |
| Schedar       | even          | Friendly and informal; down-to-earth          |
| Umbriel       | easy-going    | Smooth and knowledgeable                      |
| Zubenelgenubi | casual        | Deep and resonant; strong authority           |

## Usage Example: Multi-Character Story

```python
from gossiptoon.audio.google_tts_client import GoogleTTSClient
from gossiptoon.core.constants import EmotionTone

client = GoogleTTSClient(api_key="YOUR_API_KEY")

# Character 1: Female protagonist
female_voice = client.get_recommended_voice_for_gender("female", index=0)
await client.generate_speech(
    text="I can't believe this is happening!",
    voice_id=female_voice,  # "Aoede"
    emotion=EmotionTone.SHOCKED,
    output_path=Path("character1_line1.mp3")
)

# Character 2: Male antagonist
male_voice = client.get_recommended_voice_for_gender("male", index=0)
await client.generate_speech(
    text="You should have seen this coming.",
    voice_id=male_voice,  # "Puck"
    emotion=EmotionTone.SARCASTIC,
    output_path=Path("character2_line1.mp3")
)

# Character 3: Second female character (different voice for variety)
female_voice_2 = client.get_recommended_voice_for_gender("female", index=1)
await client.generate_speech(
    text="Let me explain what really happened.",
    voice_id=female_voice_2,  # "Kore"
    emotion=EmotionTone.SYMPATHETIC,
    output_path=Path("character3_line1.mp3")
)
```

## Integration with Script Writer

The script writer agent can now:

1. **Identify character genders** from the story
2. **Assign voices** using `get_recommended_voice_for_gender(gender, character_index)`
3. **Generate audio** for each character with their assigned voice
4. **Maintain consistency** by using the same voice for the same character throughout the story

### Example Script Writer Logic

```python
# In script writer agent
characters = [
    {"name": "Sarah", "gender": "female"},
    {"name": "John", "gender": "male"},
    {"name": "Emma", "gender": "female"},
]

# Assign voices
character_voices = {}
for i, character in enumerate(characters):
    voice = client.get_recommended_voice_for_gender(
        character["gender"],
        index=i  # Use index to get different voices for same gender
    )
    character_voices[character["name"]] = voice

# Result:
# Sarah -> Aoede (female, index 0)
# John -> Puck (male, index 0)
# Emma -> Kore (female, index 1)
```

## Key Features

✅ **30 Voices**: Complete catalog of all Google TTS prebuilt voices  
✅ **Gender Metadata**: Each voice tagged with gender for automatic selection  
✅ **Style Information**: Voice characteristics for better matching  
✅ **Automatic Cycling**: `index` parameter cycles through recommended voices  
✅ **Backward Compatible**: Existing code continues to work with default voice

## Notes

- Google TTS supports **up to 2 speakers** in a single API request
- For stories with more than 2 characters, generate audio separately for each character
- Voice selection is deterministic - same gender + index always returns same voice
- Recommended voices are curated for storytelling quality
