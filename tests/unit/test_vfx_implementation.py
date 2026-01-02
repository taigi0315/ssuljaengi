"""Unit tests for TICKET-027: Refine & Diversify Visual Effects."""
import pytest
from unittest.mock import Mock

from gossiptoon.video.effects.camera import CameraEffect, CameraEffectConfig, ShakeEffect
from gossiptoon.core.constants import CameraEffectType
from gossiptoon.agents.script_writer import ScriptWriterAgent
from gossiptoon.agents.script_evaluator import ScriptEvaluator

class TestCameraEffects:
    """Test camera effect factory logic."""

    def test_shake_variants_creation(self):
        """CameraEffect creates correct ShakeEffect for variants."""
        # Test SLOW shake
        config_slow = CameraEffectConfig(
            effect_type=CameraEffectType.SHAKE_SLOW,
            intensity=1.0
        )
        effect_slow = CameraEffect(config_slow)
        assert isinstance(effect_slow._delegate, ShakeEffect)
        assert effect_slow._delegate.speed == "slow"
        assert effect_slow._delegate.intensity == 0.15 # Defined in factory

        # Test FAST shake
        config_fast = CameraEffectConfig(
            effect_type=CameraEffectType.SHAKE_FAST,
            intensity=1.0
        )
        effect_fast = CameraEffect(config_fast)
        assert isinstance(effect_fast._delegate, ShakeEffect)
        assert effect_fast._delegate.speed == "fast"
        assert effect_fast._delegate.intensity == 0.5

    def test_shake_effect_filters(self):
        """ShakeEffect generates correct FFmpeg filters."""
        # Slow shake
        shake_slow = ShakeEffect(intensity=0.1, speed="slow")
        filter_str = shake_slow.get_filter_string("in", "out")
        assert "sin(t*" in filter_str  # Should use sine wave
        
        # Fast shake
        shake_fast = ShakeEffect(intensity=0.1, speed="fast")
        filter_str_fast = shake_fast.get_filter_string("in", "out")
        assert "random(1)" in filter_str_fast # Should use random jitter


class TestVFXPrompts:
    """Test LLM prompts for VFX."""

    def test_script_writer_vfx_options(self):
        """ScriptWriter prompt lists new VFX options."""
        config = Mock()
        config.api.google_api_key = "test_key"
        config.script.webtoon_mode = True
        
        writer = ScriptWriterAgent(config)
        system_prompt = writer._get_system_prompt()
        
        assert "shake_slow" in system_prompt
        assert "shake_fast" in system_prompt
        assert "zoom_in" in system_prompt
        assert "pan_left" in system_prompt

    def test_evaluator_vfx_validation(self):
        """Evaluator prompt includes VFX validation."""
        config = Mock()
        config.api.google_api_key = "test_key"
        config.scripts_dir.parent = "outputs/test"
        
        evaluator = ScriptEvaluator(config)
        system_prompt = evaluator._get_system_prompt("", "")
        
        assert "Camera Effect Validation" in system_prompt
        assert "shake_slow" in system_prompt
        assert "duration MUST be <=" in system_prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
