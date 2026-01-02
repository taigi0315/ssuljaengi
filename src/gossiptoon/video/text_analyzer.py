"""Text analyzer for detecting high-impact words and applying styles."""

import re
from enum import Enum
from typing import NamedTuple

class TextStyle(str, Enum):
    """Text style categories."""
    NORMAL = "normal"
    HIGH_IMPACT = "high_impact"
    EMPHASIS = "emphasis"

class StyledSegment(NamedTuple):
    """Segment of text with applied style."""
    text: str
    style: TextStyle
    is_trigger: bool

class TextAnalyzer:
    """Analyzes text to detect dramatic moments and apply styling."""

    # Trigger words configuration
    TRIGGER_WORDS = {
        # Profanity / Intensity (keep list appropriate but functional)
        "wtf", "damn", "hell", "shit", "fuck", "bitch", "crap",
        
        # Exclamations
        "omg", "what", "no", "yes", "stop", "why", "whoa", "wow",
        "seriously", "absolutely", "never", "always",
        
        # Dramatic Verbs
        "screamed", "yelled", "shouted", "exploded", "cried", "died",
        "killed", "slapped", "punched", "grabbed", "choked",
        
        # Shock Words
        "insane", "crazy", "shocking", "unbelievable", "impossible",
        "liar", "cheater", "betrayed", "betrayal", "secret"
    }

    @classmethod
    def analyze_word(cls, word: str) -> TextStyle:
        """Determine style for a single word.
        
        Args:
            word: Word to analyze (can include punctuation)

        Returns:
            TextStyle enum
        """
        clean_word = re.sub(r'[^\w\s]', '', word).lower()
        
        # 1. Check ALL CAPS (Intensity)
        # Needs to be at least 2 chars to avoid "A", "I"
        if word.isupper() and len(clean_word) > 1:
            return TextStyle.HIGH_IMPACT

        # 2. Check Trigger Words
        if clean_word in cls.TRIGGER_WORDS:
            return TextStyle.HIGH_IMPACT

        # 3. Check Emphatic Punctuation (e.g., "What?!")
        if "?!" in word or "!!" in word:
            return TextStyle.EMPHASIS

        return TextStyle.NORMAL

    @staticmethod
    def get_ass_tags(style: TextStyle) -> str:
        """Get ASS formatting tags for a style.
        
        Args:
            style: TextStyle to get tags for

        Returns:
            ASS tag string
        """
        if style == TextStyle.HIGH_IMPACT:
            # Bold, Larger, Yellow/Red/Magenta (Randomized handled by caller or fixed)
            # For now returning base formatting, caller adds color
            return r"{\b1\fs150%}" # Bold, 1.5x size
        
        elif style == TextStyle.EMPHASIS:
            # Bold, slightly larger
            return r"{\b1\fs120%}"
            
        return r"{\b0}" # Normal weight

    @staticmethod
    def get_high_impact_color() -> str:
        """Get a random high-impact color in ASS BGR format.
        
        Returns:
            Review-approved colors: Yellow, Red, Magenta
        """
        import random
        # ASS Color format: &HBBGGRR
        colors = [
            "&H0000FFFF",  # Yellow (BGR: 00 FFFF)
            "&H000000FF",  # Red (BGR: 00 00FF)
            "&H00FF00FF",  # Magenta (BGR: FF 00FF)
            "&H000080FF",  # Orange-ish (BGR: 00 80FF)
        ]
        return random.choice(colors)
