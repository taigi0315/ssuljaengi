# Google TTS 2.5 Flash Integration - Documentation

## Overview

Google TTS 2.5 Flash를 ElevenLabs의 대체 TTS provider로 성공적으로 구현했습니다. "Director" 방식을 사용하여 emotion에 따른 dramatic한 narration을 생성합니다.

## Usage

### 1. Environment Configuration

`.env` 파일에서 TTS provider를 선택:

```bash
# Google TTS 사용
TTS_PROVIDER=google
GOOGLE_TTS_VOICE=Kore
GOOGLE_TTS_MODEL=gemini-2.5-flash-preview-tts

# 또는 ElevenLabs 사용 (기본값)
TTS_PROVIDER=elevenlabs
DEFAULT_VOICE_ID=21m00Tcm4TlvDq8ikWAM
```

### 2. Available Voices

Google TTS는 30개의 prebuilt voice를 제공합니다 (female 14개, male 16개).

**Recommended Voices:**

- **Female**: Aoede, Kore, Laomedeia, Sulafat, Despina
- **Male**: Puck, Charon, Fenrir, Orus, Umbriel

전체 voice 목록과 gender 정보는 [Multi-Speaker Documentation](GOOGLE_TTS_MULTI_SPEAKER.md)을 참조하세요.

### 3. Multi-Speaker Support

Character별로 gender에 맞는 voice를 자동 선택:

```python
# Get recommended voice for character
female_voice = client.get_recommended_voice_for_gender("female", index=0)  # "Aoede"
male_voice = client.get_recommended_voice_for_gender("male", index=0)      # "Puck"

# Get all voices by gender
female_voices = client.get_voices_by_gender("female")  # 14 voices
male_voices = client.get_voices_by_gender("male")      # 16 voices
```

자세한 내용은 [GOOGLE_TTS_MULTI_SPEAKER.md](GOOGLE_TTS_MULTI_SPEAKER.md)를 참조하세요.

### 4. Emotion-to-Style Mapping

각 `EmotionTone`은 Google TTS의 "Director" 방식 프롬프트로 자동 변환됩니다:

| Emotion     | Style Directive                                                              |
| ----------- | ---------------------------------------------------------------------------- |
| EXCITED     | "infectious, cheerful vocal smile with rising energy and enthusiasm"         |
| SHOCKED     | "sudden gasp with wide-eyed surprise, sharp intake of breath, and disbelief" |
| DRAMATIC    | "theatrical, sweeping delivery with dramatic pauses and intensity"           |
| SUSPENSEFUL | "hushed, tense whisper with building anticipation and mystery"               |
| SARCASTIC   | "dry, ironic tone with subtle eye-roll energy and wit"                       |

전체 매핑은 `src/gossiptoon/core/constants.py`의 `GOOGLE_TTS_STYLE_DIRECTIVES`를 참조하세요.

### 4. Code Example

```python
from gossiptoon.audio.google_tts_client import GoogleTTSClient
from gossiptoon.core.constants import EmotionTone
from pathlib import Path

# Initialize client
client = GoogleTTSClient(
    api_key="YOUR_GOOGLE_API_KEY",
    model="gemini-2.5-flash-preview-tts",
    default_voice="Kore"
)

# Generate speech with emotion
audio_path = await client.generate_speech(
    text="This is absolutely shocking!",
    voice_id="Puck",
    emotion=EmotionTone.SHOCKED,
    output_path=Path("output/shocked.mp3")
)
```

### 5. Automatic Provider Selection

`AudioGenerator`는 설정에 따라 자동으로 TTS provider를 선택합니다:

```python
from gossiptoon.audio.generator import AudioGenerator
from gossiptoon.core.config import ConfigManager

config = ConfigManager()  # .env에서 TTS_PROVIDER 읽음
generator = AudioGenerator(config)  # 자동으로 Google TTS 또는 ElevenLabs 선택
```

## Technical Details

### Architecture

- **Base Interface**: `TTSClient` abstract class를 구현
- **Swappable Design**: ElevenLabs 코드를 전혀 수정하지 않음
- **Format Conversion**: Google TTS의 PCM → WAV → MP3 자동 변환
- **Error Handling**: `AudioGenerationError`로 통일된 에러 처리
- **Retry Logic**: `@retry_with_backoff` decorator 사용

### File Structure

```
src/gossiptoon/
├── audio/
│   ├── base.py                    # TTSClient interface
│   ├── elevenlabs_client.py       # ElevenLabs implementation (unchanged)
│   ├── google_tts_client.py       # Google TTS implementation (NEW)
│   └── generator.py               # Auto-selects TTS provider
├── core/
│   ├── config.py                  # Added TTS provider config
│   ├── constants.py               # Added Google TTS style directives
│   └── exceptions.py              # Added GoogleTTSError
```

### Configuration Flow

```
.env (TTS_PROVIDER=google)
  ↓
ConfigManager.audio.tts_provider
  ↓
AudioGenerator.__init__()
  ↓
GoogleTTSClient (if provider=google)
  ↓
generate_speech() with emotion → style directive
```

## Testing

### Basic Test

```bash
# Test import
python -c "from gossiptoon.audio.google_tts_client import GoogleTTSClient; print('OK')"

# Test config
python -c "from gossiptoon.core.config import ConfigManager; c = ConfigManager(); print(c.audio.tts_provider)"
```

### Integration Test

```bash
# Run with Google TTS
TTS_PROVIDER=google gossiptoon run <reddit_url>

# Run with ElevenLabs (verify backward compatibility)
TTS_PROVIDER=elevenlabs gossiptoon run <reddit_url>
```

## Notes

- Google TTS returns 24kHz PCM audio, converted to MP3 for pipeline compatibility
- Style directives are optimized for dramatic storytelling
- Voice selection is flexible - any Google prebuilt voice name works
- ElevenLabs code remains completely untouched for backward compatibility
