
import pytest
from gossiptoon.video.text_analyzer import TextAnalyzer, TextStyle

def test_analyze_word_high_impact():
    """Test high impact word detection."""
    assert TextAnalyzer.analyze_word("WTF") == TextStyle.HIGH_IMPACT
    assert TextAnalyzer.analyze_word("SCREAMED") == TextStyle.HIGH_IMPACT
    assert TextAnalyzer.analyze_word("OMG") == TextStyle.HIGH_IMPACT
    
    # Trigger words case insensitive
    assert TextAnalyzer.analyze_word("wtf") == TextStyle.HIGH_IMPACT

def test_analyze_word_emphasis():
    """Test emphasis detection."""
    assert TextAnalyzer.analyze_word("Really?!") == TextStyle.EMPHASIS
    # "NO!!" is all caps and in trigger list ("no"), so it will be HIGH_IMPACT
    # We test explicit punctuation on a non-trigger word
    assert TextAnalyzer.analyze_word("Please!!") == TextStyle.EMPHASIS

def test_analyze_word_normal():
    """Test normal word classification."""
    assert TextAnalyzer.analyze_word("The") == TextStyle.NORMAL
    assert TextAnalyzer.analyze_word("grocery") == TextStyle.NORMAL
    assert TextAnalyzer.analyze_word("store") == TextStyle.NORMAL
    # Single letter uppercase should be normal usually, unless specific
    # But current logic: len(clean_word) > 1 for ALLCAPS
    assert TextAnalyzer.analyze_word("I") == TextStyle.NORMAL 
    assert TextAnalyzer.analyze_word("A") == TextStyle.NORMAL

def test_get_ass_tags():
    """Test ASS tag generation."""
    assert r"{\b1\fs150%}" == TextAnalyzer.get_ass_tags(TextStyle.HIGH_IMPACT)
    assert r"{\b1\fs120%}" == TextAnalyzer.get_ass_tags(TextStyle.EMPHASIS)
    assert r"{\b0}" == TextAnalyzer.get_ass_tags(TextStyle.NORMAL)

def test_get_high_impact_color():
    """Test color generation."""
    color = TextAnalyzer.get_high_impact_color()
    assert color.startswith("&H")
    assert len(color) >= 4
