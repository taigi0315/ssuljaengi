"""Unit tests for TICKET-028: Standardized Character Sheets."""
import pytest
from unittest.mock import Mock, AsyncMock
from pathlib import Path

from gossiptoon.models.script import Script, CharacterProfile, Act
from gossiptoon.agents.script_writer import ScriptWriterAgent
from gossiptoon.agents.script_evaluator import ScriptEvaluator
from gossiptoon.visual.director import VisualDirector, CHARACTER_SHEET_TEMPLATE

class TestCharacterProfileModel:
    """Test CharacterProfile model validation."""
    
    def test_character_profile_creation(self):
        """Valid profile creates successfully."""
        profile = CharacterProfile(
            name="John",
            age="25",
            gender="Male",
            role="Protagonist",
            personality_vibe="Cheerful",
            body_type="Slim",
            hair_style_color="Short blonde",
            face_details_expression="Blue eyes, smiling",
            outfit="Blue shirt"
        )
        assert profile.name == "John"
        assert profile.age == "25"

class TestScriptModelUpdate:
    """Test Script model includes character profiles."""
    
    def test_script_initialization_with_profiles(self):
        """Script accepts character_profiles field."""
        profile = CharacterProfile(
            name="John",
            age="25",
            gender="Male",
            role="Protagonist",
            personality_vibe="Cheerful",
            body_type="Slim",
            hair_style_color="Short blonde",
            face_details_expression="Blue eyes, smiling",
            outfit="Blue shirt"
        )
        
        # Helper to create valid Acts
        act_data = []
        for act_type in ["hook", "build", "crisis", "climax", "resolution"]:
            act_data.append(Act(
                act_type=act_type,
                target_duration_seconds=10.0,
                scenes=[{
                    "scene_id": f"{act_type}_01",
                    "order": 1,
                    "visual_description": "A tall man standing in a brightly lit room with blue walls, looking very happy",
                    "emotion": "neutral",
                    "estimated_duration_seconds": 3.0,
                    "characters_present": ["John"],
                    "audio_chunks": [{
                        "chunk_id": "chunk_1",
                        "chunk_type": "narration",
                        "speaker_id": "Narrator",
                        "text": "Hello world",
                        "director_notes": "Calm voice",
                        "estimated_duration": 3.0
                    }]
                }]
            ))

        script_data = {
            "script_id": "test_script",
            "story_id": "test_story",
            "title": "Test Title with sufficient length for validation",
            "total_estimated_duration": 50.0,
            "character_profiles": [profile.model_dump()],
            "acts": act_data
        }
        
        script = Script(**script_data)
        assert len(script.character_profiles) == 1
        assert script.character_profiles[0].name == "John"


class TestScriptWriterPrompt:
    """Test Agent Prompts."""
    
    def _create_mock_config(self):
        config = Mock()
        config.api.google_api_key = "test"
        config.script.webtoon_mode = True
        
        # Fix: Mock pathlib.Path behavior for / operator
        mock_path = Mock()
        mock_path.mkdir = Mock()
        
        # Mock directory structure for path / "file"
        mock_child = Mock(mkdir=Mock())
        mock_path.__truediv__ = Mock(return_value=mock_child)
        
        # Mock parent directory for LLMDebugger (important!)
        mock_parent = Mock()
        mock_parent.__truediv__ = Mock(return_value=Mock(mkdir=Mock()))
        mock_path.parent = mock_parent
        
        config.scripts_dir = mock_path
        return config
    
    def test_writer_system_prompt_includes_standards(self):
        """ScriptWriter prompt includes character design standards."""
        config = self._create_mock_config()
        
        # We don't need to instantiate Agent fully if we just check class attribute, 
        # but to test __init__ logic we do.
        # But wait, SYSTEM_PROMPT is a class attribute.
        assert "Character Design Standards" in ScriptWriterAgent.SYSTEM_PROMPT
        assert "character_profiles" in ScriptWriterAgent.SYSTEM_PROMPT
        assert "Personality Vibe" in ScriptWriterAgent.SYSTEM_PROMPT

    def test_example_output_includes_profiles(self):
        """Example output JSON includes character_profiles."""
        # Check SYSTEM_PROMPT directly as it contains the Example
        assert '"character_profiles": [' in ScriptWriterAgent.SYSTEM_PROMPT
        assert '"name": "Mother"' in ScriptWriterAgent.SYSTEM_PROMPT
        assert '"outfit": "Floral apron over house clothes"' in ScriptWriterAgent.SYSTEM_PROMPT


class TestVisualDirectorPrompting:
    """Test VisualDirector prompt generation logic."""
    
    @pytest.mark.asyncio
    async def test_generate_portraits_uses_profile_template(self):
        """VisualDirector should use CHARACTER_SHEET_TEMPLATE when profile exists."""
        # Setup Mocks
        config = Mock()
        config.images_dir = Path("/tmp/images")
        config.api.google_api_key = "test"
        config.image.style = "webtoon"
        config.image.aspect_ratio = "9:16"
        config.image.negative_prompt = "bad quality"
        
        mock_image_client = AsyncMock()
        mock_image_client.generate_image.return_value = Path("dummy_path.png")
        # Fix: setup model name to avoid error in non-mocked log call
        mock_image_client.get_model_name.return_value = "test_model"
        
        # Fix: Mock supports_i2i for later calls if needed, though not for portrait
        mock_image_client.supports_i2i.return_value = False
        
        director = VisualDirector(config, image_client=mock_image_client)
        
        # Setup Mock Script with Profile
        profile = CharacterProfile(
            name="Hero",
            age="20",
            gender="Male",
            role="Protagonist",
            personality_vibe="Brave",
            body_type="Athletic",
            hair_style_color="Red spikes",
            face_details_expression="Scar on lip",
            outfit="Armor"
        )
        script = Mock(spec=Script)
        script.script_id = "test_script"
        script.character_profiles = [profile]
        
        # Mock character bank
        mock_bank = Mock()
        mock_bank.has_character.return_value = False
        
        # Run
        await director._generate_character_portraits(script, ["Hero"], mock_bank)
        
        # Verify call to generate_image
        assert mock_image_client.generate_image.called
        
        # Get arguments safely
        call_args = mock_image_client.generate_image.call_args
        
        kwargs = call_args.kwargs
        image_prompt = kwargs.get('prompt')
        
        assert image_prompt is not None, "Prompt argument missing"
        
        # Check that the prompt was formatted using the template
        # Template: "{age} year old {gender}" -> "20 year old Male"
        # Prompt code: age.replace("year old", "") -> "20"
        expected_part = "full body view of a 20 year old Male. Brave vibe. Athletic build"
        assert expected_part in image_prompt.base_prompt
        assert "Having Red spikes hair" in image_prompt.base_prompt
        assert "Wearing Armor" in image_prompt.base_prompt
        assert "plain solid white background" in image_prompt.base_prompt

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
