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
MIN_SCRIPT_DURATION = 40.0  # seconds (was 30.0)
MAX_SCRIPT_DURATION = 60.0  # seconds (matches YouTube Shorts max)
TARGET_SCRIPT_DURATION = 55.0  # seconds (target sweet spot)
MAX_SCENE_NARRATION_WORDS = 35  # slightly relaxed but still concise
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
    STATIC = "static"
    LOOM = "loom"  # NEW - dramatic forward movement


# Act duration guidelines (in seconds) - Revised for 40s target
ACT_DURATION_RANGES = {
    ActType.HOOK: (0.5, 3.0),  # Ultra-short hook (Extreme Dramatic)
    ActType.BUILD: (3.0, 10.0),  # Fast context
    ActType.CRISIS: (5.0, 12.0),  # Quick escalation
    ActType.CLIMAX: (10.0, 15.0),  # Main engagement
    ActType.RESOLUTION: (5.0, 10.0),  # Quick wrap-up
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

# Google TTS style directives (for Gemini 2.5 Flash TTS)
# Using the "Director" method for expressive narration
GOOGLE_TTS_STYLE_DIRECTIVES = {
    EmotionTone.EXCITED: "infectious, cheerful vocal smile with rising energy and enthusiasm",
    EmotionTone.SHOCKED: "sudden gasp with wide-eyed surprise, sharp intake of breath, and disbelief",
    EmotionTone.SYMPATHETIC: "warm, gentle tone with soft empathy and understanding",
    EmotionTone.DRAMATIC: "theatrical, sweeping delivery with dramatic pauses and intensity",
    EmotionTone.ANGRY: "sharp, forceful tone with rising volume and controlled fury",
    EmotionTone.HAPPY: "bright, uplifting tone with a natural smile in the voice",
    EmotionTone.SAD: "slow, melancholic delivery with a heavy, sorrowful tone",
    EmotionTone.NEUTRAL: "clear, balanced delivery with professional composure",
    EmotionTone.SUSPENSEFUL: "hushed, tense whisper with building anticipation and mystery",
    EmotionTone.SARCASTIC: "dry, ironic tone with subtle eye-roll energy and wit",
    EmotionTone.FRUSTRATED: "exasperated tone with barely contained irritation",
    EmotionTone.DETERMINED: "firm, resolute delivery with unwavering confidence",
    EmotionTone.RELIEVED: "exhaling tension with a warm, grateful release",
    EmotionTone.EXASPERATED: "fed-up, exhausted patience with a deep sigh",
}

# Google TTS voice metadata - All 30 prebuilt voices with gender and characteristics
GOOGLE_TTS_VOICE_METADATA = {
    # Female Voices
    "Achernar": {"gender": "female", "style": "soft"},
    "Aoede": {"gender": "female", "style": "breezy"},
    "Autonoe": {"gender": "female", "style": "bright"},
    "Callirrhoe": {"gender": "female", "style": "easy-going"},
    "Despina": {"gender": "female", "style": "smooth"},
    "Erinome": {"gender": "female", "style": "clear"},
    "Gacrux": {"gender": "female", "style": "mature"},
    "Kore": {"gender": "female", "style": "firm"},
    "Laomedeia": {"gender": "female", "style": "upbeat"},
    "Leda": {"gender": "female", "style": "youthful"},
    "Pulcherrima": {"gender": "female", "style": "forward"},
    "Sulafat": {"gender": "female", "style": "warm"},
    "Vindemiatrix": {"gender": "female", "style": "gentle"},
    "Zephyr": {"gender": "female", "style": "bright"},
    # Male Voices
    "Achird": {"gender": "male", "style": "friendly"},
    "Algenib": {"gender": "male", "style": "gravelly"},
    "Algieba": {"gender": "male", "style": "smooth"},
    "Alnilam": {"gender": "male", "style": "firm"},
    "Charon": {"gender": "male", "style": "informative"},
    "Enceladus": {"gender": "male", "style": "breathy"},
    "Fenrir": {"gender": "male", "style": "excitable"},
    "Iapetus": {"gender": "male", "style": "clear"},
    "Orus": {"gender": "male", "style": "firm"},
    "Puck": {"gender": "male", "style": "upbeat"},
    "Rasalgethi": {"gender": "male", "style": "informative"},
    "Sadachbia": {"gender": "male", "style": "lively"},
    "Sadaltager": {"gender": "male", "style": "knowledgeable"},
    "Schedar": {"gender": "male", "style": "even"},
    "Umbriel": {"gender": "male", "style": "easy-going"},
    "Zubenelgenubi": {"gender": "male", "style": "casual"},
}

# Recommended voices by gender for character assignment
GOOGLE_TTS_RECOMMENDED_FEMALE_VOICES = ["Aoede", "Kore", "Laomedeia", "Sulafat", "Despina"]
GOOGLE_TTS_RECOMMENDED_MALE_VOICES = ["Puck", "Charon", "Fenrir", "Orus", "Umbriel"]
