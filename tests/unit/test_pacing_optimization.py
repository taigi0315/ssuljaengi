"""Unit tests for TICKET-026: Optimize Image Duration."""
import pytest
from unittest.mock import Mock, patch

from gossiptoon.agents.script_writer import ScriptWriterAgent
from gossiptoon.agents.script_evaluator import ScriptEvaluator
from gossiptoon.core.config import ScriptConfig


class TestPacingConstraints:
    """Test that pacing constraints are enforced."""
    
    def test_script_writer_pacing_prompt(self):
        """ScriptWriter prompt includes FAST MODE guidelines."""
        config = Mock()
        config.api.google_api_key = "test_key"
        config.script.webtoon_mode = True
        
        writer = ScriptWriterAgent(config)
        system_prompt = writer._get_system_prompt()
        
        # Check fast mode keywords
        assert "FAST MODE" in system_prompt
        assert "30-45s" in system_prompt
        assert "2-4s" in system_prompt
        assert "Hook: 0.5-2s" in system_prompt
    
    def test_example_scene_duration(self):
        """Example scene has correct duration for fast pacing."""
        config = Mock()
        config.api.google_api_key = "test_key"
        config.script.webtoon_mode = True
        
        writer = ScriptWriterAgent(config)
        system_prompt = writer._get_system_prompt()
        
        # Example duration should be 3.5s
        assert '"estimated_duration_seconds": 3.5' in system_prompt

    def test_evaluator_duration_validation(self):
        """Evaluator prompt includes strict duration validation."""
        config = Mock()
        config.api.google_api_key = "test_key"
        # Mock ScriptsDir for evaluator
        config.scripts_dir.parent = "outputs/test_project"
        
        evaluator = ScriptEvaluator(config)
        system_prompt = evaluator._get_system_prompt("", "")
        
        # Check validation rules
        assert "MIN: 2.0s" in system_prompt
        assert "MAX: 4.0s" in system_prompt
        assert "TARGET: 3.0s" in system_prompt


class TestVisualLogicOptimization:
    """Test that visual logic is optimized for fast pacing."""

    def test_panel_layout_instant_readability(self):
        """Prompt enforces instant readability."""
        config = Mock()
        config.api.google_api_key = "test_key"
        config.script.webtoon_mode = True
        
        writer = ScriptWriterAgent(config)
        system_prompt = writer._get_system_prompt()
        
        # Check visual keywords
        assert "INSTANT READABILITY" in system_prompt
        assert "ONE KEY MOMENT" in system_prompt
        assert "Extreme Close-up" in system_prompt

    def test_evaluator_visual_validation(self):
        """Evaluator validates visual simplicity."""
        config = Mock()
        config.api.google_api_key = "test_key"
        config.scripts_dir.parent = "outputs/test_project"
        
        evaluator = ScriptEvaluator(config)
        system_prompt = evaluator._get_system_prompt("", "")
        
        # Check visual validation rules
        assert "ONE KEY MOMENT" in system_prompt
        assert "REJECT complex multi-action" in system_prompt
        assert "SNAPSHOT moments" in system_prompt.lower() or "snapshot moments" in system_prompt.lower()


class TestConfiguration:
    """Test configuration updates."""
    
    def test_default_pacing_config(self):
        """Default config uses fast pacing values."""
        config = ScriptConfig()
        
        assert config.min_scene_duration == 2.0
        assert config.max_scene_duration == 4.0
        assert config.target_scene_duration == 3.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
