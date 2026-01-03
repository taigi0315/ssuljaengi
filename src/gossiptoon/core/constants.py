"""Constants used throughout the GossipToon engine."""

from enum import Enum
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "default.yaml"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs"

# API configuration
DEFAULT_REQUEST_TIMEOUT = 30
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 2

# Video configuration
DEFAULT_VIDEO_RESOLUTION = "1080x1920"  # 9:16 aspect ratio for Shorts
DEFAULT_VIDEO_FPS = 30
DEFAULT_VIDEO_CODEC = "libx264"
DEFAULT_VIDEO_PRESET = "medium"
DEFAULT_VIDEO_BITRATE = "5M"
DEFAULT_ASPECT_RATIO = "9:16"

# Audio configuration
DEFAULT_AUDIO_CODEC = "aac"
DEFAULT_AUDIO_BITRATE = "192k"
WHISPER_MODELS = ["tiny", "base", "small", "medium", "large"]
DEFAULT_WHISPER_MODEL = "base"

# Script configuration
MIN_SCRIPT_DURATION = 60.0  # seconds (1 minute minimum for engaging storytelling)
MAX_SCRIPT_DURATION = 150.0  # seconds (2.5 minutes maximum for detailed narratives)
TARGET_SCRIPT_DURATION = 120.0  # seconds (2 minutes target sweet spot)
MAX_SCENE_NARRATION_WORDS = 50  # increased for more detailed storytelling
MAX_CHARACTERS_PER_VIDEO = 5

# ... (Image config unchanged) ...

class EmotionTone(str, Enum):
    """Emotion tones for TTS narration."""

    EXCITED = "excited"
    SHOCKED = "shocked"
    SYMPATHETIC = "sympathetic"
    DRAMATIC = "dramatic"
    ANGRY = "angry"
    HAPPY = "happy"
    SAD = "sad"
    NEUTRAL = "neutral"
    SUSPENSEFUL = "suspenseful"
    SARCASTIC = "sarcastic"
    FRUSTRATED = "frustrated"
    DETERMINED = "determined"
    RELIEVED = "relieved"
    EXASPERATED = "exasperated"  # NEW - fed up, exhausted patience

class ActType(str, Enum):
    """Five-act structure for video scripts."""

    HOOK = "hook"  # 0-3s: Grab attention
    BUILD = "build"  # 3-8s: Context and setup
    CRISIS = "crisis"  # 8-18s: Problem escalates
    CLIMAX = "climax"  # 18-30s: Peak tension
    RESOLUTION = "resolution"  # 30-40s: Outcome/twist



class StoryCategory(str, Enum):
    """Reddit story categories."""

    AITA = "aita"
    TIFU = "tifu"
    RELATIONSHIP = "relationship"
    REVENGE = "revenge"
    HORROR = "horror"
    CONFESSION = "confession"
    ENTITLED_PEOPLE = "entitled_people"
    WORKPLACE = "workplace"
    FAMILY = "family"
    WEDDING = "wedding"
    OTHER = "other"





class CameraEffectType(str, Enum):
    """Camera effects for video scenes."""

    KEN_BURNS = "ken_burns"
    FADE_TRANSITION = "fade_transition"
    CAPTION = "caption"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    PAN_UP = "pan_up"
    PAN_DOWN = "pan_down"
    SHAKE = "shake"
    SHAKE_SLOW = "shake_slow"  # NEW - subtle tension
    SHAKE_FAST = "shake_fast"  # NEW - intense shock
    STATIC = "static"
    LOOM = "loom"


# Act duration guidelines (in seconds) - Extended for 2-minute storytelling
ACT_DURATION_RANGES = {
    ActType.HOOK: (2.0, 5.0),      # Strong hook with context
    ActType.BUILD: (10.0, 20.0),   # Detailed setup and character development
    ActType.CRISIS: (20.0, 40.0),  # Extended escalation with multiple beats
    ActType.CLIMAX: (30.0, 50.0),  # Peak drama with full emotional impact
    ActType.RESOLUTION: (10.0, 20.0), # Satisfying conclusion
}

# ElevenLabs voice settings
EMOTION_VOICE_SETTINGS = {
    EmotionTone.EXCITED: {"stability": 0.4, "similarity_boost": 0.75, "style": 0.8},
    EmotionTone.SHOCKED: {"stability": 0.3, "similarity_boost": 0.75, "style": 0.9},
    EmotionTone.SYMPATHETIC: {"stability": 0.6, "similarity_boost": 0.85, "style": 0.5},
    EmotionTone.DRAMATIC: {"stability": 0.5, "similarity_boost": 0.75, "style": 0.85},
    EmotionTone.ANGRY: {"stability": 0.3, "similarity_boost": 0.75, "style": 0.9},
    EmotionTone.HAPPY: {"stability": 0.5, "similarity_boost": 0.75, "style": 0.7},
    EmotionTone.SAD: {"stability": 0.7, "similarity_boost": 0.85, "style": 0.4},
    EmotionTone.NEUTRAL: {"stability": 0.5, "similarity_boost": 0.75, "style": 0.5},
    EmotionTone.SUSPENSEFUL: {"stability": 0.6, "similarity_boost": 0.75, "style": 0.8},
    EmotionTone.SARCASTIC: {"stability": 0.4, "similarity_boost": 0.75, "style": 0.75},
}
