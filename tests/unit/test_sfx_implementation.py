"""Unit tests for SFX generation in ScriptWriter and ScriptEvaluator.

Tests TICKET-025: Fix Missing SFX Implementation
"""
import pytest
from unittest.mock import Mock, patch

from gossiptoon.agents.script_writer import ScriptWriterAgent
from gossiptoon.agents.script_evaluator import ScriptEvaluator
from gossiptoon.audio.sfx_mapper import SFXMapper
from gossiptoon.models.story import Story, RedditPostMetadata


class TestSFXMapper:
    """Test SFX library and mapping functionality."""
    
    def test_sfx_library_structure(self):
        """SFX library has all required categories."""
        mapper = SFXMapper()
        available = mapper.list_available_sfx()
        
        # Should have exactly 13 SFX keywords
        assert len(available) == 13
        
        # Check categories
        tension_sfx = [s for s in available if mapper.get_sfx_category(s) == "tension"]
        action_sfx = [s for s in available if mapper.get_sfx_category(s) == "action"]
        impact_sfx = [s for s in available if mapper.get_sfx_category(s) == "impact"]
        
        assert len(tension_sfx) == 4  # DOOM, DUN-DUN, LOOM, RUMBLE
        assert len(action_sfx) == 5   # SQUEEZE, GRAB, GRIP, CLENCH, CRUSH
        assert len(impact_sfx) == 4   # BAM!, WHAM!, THUD, TA-DA!
    
    def test_sfx_keyword_mapping(self):
        """SFX keywords map to valid file paths."""
        mapper = SFXMapper()
        
        # Test each category
        test_keywords = {
            "DOOM": "tension",
            "BAM!": "impact",
            "GRAB": "action"
        }
        
        for keyword, expected_category in test_keywords.items():
            category = mapper.get_sfx_category(keyword)
            assert category == expected_category
            
            description = mapper.get_sfx_description(keyword)
            assert description is not None
            assert len(description) > 20  # Should have meaningful description
    
    def test_sfx_case_insensitive(self):
        """SFX keywords are case-insensitive."""
        mapper = SFXMapper()
        
        # Different cases should work
        assert mapper.get_sfx_category("BAM!") == "impact"
        assert mapper.get_sfx_category("bam!") == "impact"
        assert mapper.get_sfx_category("BaM!") == "impact"
    
    def test_invalid_sfx_keyword(self):
        """Invalid SFX keywords return None."""
        mapper = SFXMapper()
        
        assert mapper.get_sfx_path("INVALID_SFX") is None
        assert mapper.get_sfx_category("NOT_EXIST") is None
        assert mapper.get_sfx_description("FAKE") is None


class TestScriptWriterSFXPrompt:
    """Test that ScriptWriter prompt includes SFX instructions."""
    
    @pytest.fixture
    def config_mock(self):
        """Mock config for ScriptWriter."""
        config = Mock()
        config.api.google_api_key = "test_key"
        config.script.webtoon_mode = True
        return config
    
    def test_system_prompt_includes_sfx_field(self, config_mock):
        """ScriptWriter system prompt documents visual_sfx field."""
        writer = ScriptWriterAgent(config_mock)
        system_prompt = writer._get_system_prompt()
        
        # Should mention visual_sfx
        assert "visual_sfx" in system_prompt.lower()
        
        # Should list SFX categories
        assert "TENSION" in system_prompt or "DOOM" in system_prompt
        assert "ACTION" in system_prompt or "GRAB" in system_prompt
        assert "IMPACT" in system_prompt or "BAM!" in system_prompt
        
        # Should have usage guidelines
        assert "sparingly" in system_prompt.lower() or "1-2" in system_prompt
    
    def test_example_scene_has_sfx(self, config_mock):
        """Example scene in prompt includes visual_sfx."""
        writer = ScriptWriterAgent(config_mock)
        system_prompt = writer._get_system_prompt()
        
        # Example should show visual_sfx field
        assert '"visual_sfx"' in system_prompt or "'visual_sfx'" in system_prompt


class TestScriptEvaluatorSFXValidation:
    """Test that ScriptEvaluator validates SFX keywords."""
    
    @pytest.fixture
    def config_mock(self):
        """Mock config for ScriptEvaluator."""
        config = Mock()
        config.api.google_api_key = "test_key"
        return config
    
    def test_system_prompt_includes_sfx_validation(self, config_mock):
        """ScriptEvaluator prompt includes SFX validation rules."""
        evaluator = ScriptEvaluator(config_mock)
        system_prompt = evaluator._get_system_prompt("", "")
        
        # Should mention SFX validation
        assert "visual_sfx" in system_prompt.lower() or "sfx" in system_prompt.lower()
        
        # Should list valid SFX keywords
        valid_keywords = ["DOOM", "DUN-DUN", "BAM!", "GRAB", "SQUEEZE"]
        found_keywords = sum(1 for kw in valid_keywords if kw in system_prompt)
        assert found_keywords >= 3  # At least 3 keywords mentioned


class TestSFXIntegration:
    """Integration tests for SFX in pipeline."""
    
    def test_sfx_field_optional(self):
        """visual_sfx field is optional in Scene model."""
        from gossiptoon.models.script import Scene
        
        # Should work without visual_sfx
        scene_without_sfx = Scene(
            scene_id="test_01",
            audio_chunks=[],
            panel_layout="Test layout",
            emotion="neutral",
            visual_description="Test scene",
            characters_present=[],
            estimated_duration_seconds=5.0
        )
        
        assert not hasattr(scene_without_sfx, 'visual_sfx') or scene_without_sfx.visual_sfx is None
    
    def test_sfx_categories_match_assets(self):
        """SFX library categories match asset directory structure."""
        from pathlib import Path
        
        sfx_dir = Path(__file__).parent.parent.parent / "assets" / "sfx"
        
        if sfx_dir.exists():
            # Check expected directories exist
            assert (sfx_dir / "tension").exists()
            assert (sfx_dir / "action").exists()
            assert (sfx_dir / "impact").exists()


class TestSFXUsageGuidelines:
    """Test SFX usage guidelines enforcement."""
    
    def test_max_sfx_per_video_guideline(self):
        """Prompt guidelines recommend max 2 SFX per video."""
        config = Mock()
        config.api.google_api_key = "test_key"
        config.script.webtoon_mode = True
        
        writer = ScriptWriterAgent(config)
        system_prompt = writer._get_system_prompt()
        
        # Should mention limiting SFX usage
        assert "1-2" in system_prompt or "sparingly" in system_prompt.lower()
    
    def test_high_impact_scenes_only(self):
        """Prompt guidelines recommend SFX for high-impact scenes only."""
        config = Mock()
        config.api.google_api_key = "test_key"
        config.script.webtoon_mode = True
        
        writer = ScriptWriterAgent(config)
        system_prompt = writer._get_system_prompt()
        
        # Should mention high-impact/dramatic scenes
        high_impact_terms = ["high-impact", "climax", "shock", "revelation", "dramatic"]
        found = sum(1 for term in high_impact_terms if term.lower() in system_prompt.lower())
        assert found >= 2  # At least 2 high-impact terms mentioned


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
