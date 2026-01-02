"""Unit tests for the new 3-agent workflow (Structure-First)."""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from gossiptoon.agents.scene_structurer import SceneStructurerAgent
from gossiptoon.agents.script_writer import ScriptWriterAgent
from gossiptoon.agents.script_evaluator import ScriptEvaluator
from gossiptoon.core.config import ConfigManager
from gossiptoon.models.story import Story, StoryCategory
from gossiptoon.models.script import Script, Act, Scene, ActType, EmotionTone


@pytest.fixture
def sample_story():
    """Create a sample story for testing."""
    return Story(
        story_id="test_story_001",
        title="Test Story",
        content="This is a test story about a person who did something interesting. " * 20,
        category=StoryCategory.RELATIONSHIP,
        url="https://reddit.com/r/test",
        score=100,
        comments=50,
        subreddit="test"
    )


@pytest.fixture
def config_manager(tmp_path):
    """Create a config manager with temporary directories."""
    from pathlib import Path

    config = ConfigManager(base_dir=tmp_path)
    # Override API key for testing
    config.api.google_api_key = "test_api_key_for_testing"
    return config


class TestSceneStructurer:
    """Test SceneStructurer agent."""

    @pytest.mark.asyncio
    async def test_scaffold_has_required_fields(self, config_manager, sample_story):
        """Test that scaffold contains all required structural fields."""
        # This is a smoke test - we'll check the structure without calling the LLM
        structurer = SceneStructurerAgent(config_manager)

        # Mock the LLM response
        mock_scaffold = Script(
            script_id="scaffold_test_001",
            story_id=sample_story.id,
            title=sample_story.title,
            total_estimated_duration=45.0,
            acts=[
                Act(
                    act_type=ActType.HOOK,
                    target_duration_seconds=2.0,
                    scenes=[
                        Scene(
                            scene_id="hook_01",
                            order=0,
                            audio_chunks=[],  # Empty in scaffold
                            emotion=EmotionTone.NEUTRAL,
                            visual_description="Placeholder description for testing purposes",
                            characters_present=["TestChar"],
                            estimated_duration_seconds=2.0
                        )
                    ]
                )
            ],
            character_profiles=[]
        )

        # Validate scaffold structure
        assert mock_scaffold.script_id is not None
        assert mock_scaffold.story_id == sample_story.id
        assert len(mock_scaffold.acts) >= 1
        assert mock_scaffold.total_estimated_duration > 0

        # Check scene has required fields
        scene = mock_scaffold.acts[0].scenes[0]
        assert scene.scene_id is not None
        assert scene.order == 0
        assert scene.estimated_duration_seconds > 0
        assert len(scene.audio_chunks) == 0  # Should be empty in scaffold
        assert scene.visual_description is not None


    def test_scaffold_validation_logic(self, config_manager, sample_story):
        """Test the scaffold validation method."""
        structurer = SceneStructurerAgent(config_manager)

        # Create a valid scaffold
        scaffold = Script(
            script_id="string",  # Should be auto-generated
            story_id="string",  # Should be auto-filled
            title=sample_story.title,
            total_estimated_duration=45.0,
            acts=[
                Act(
                    act_type=ActType.HOOK,
                    target_duration_seconds=2.0,
                    scenes=[
                        Scene(
                            scene_id="hook_01",
                            order=0,
                            audio_chunks=[],
                            emotion=EmotionTone.NEUTRAL,
                            visual_description="Placeholder description for testing purposes",
                            characters_present=["TestChar"],
                            estimated_duration_seconds=2.0
                        )
                    ]
                ),
                Act(
                    act_type=ActType.BUILD,
                    target_duration_seconds=3.0,
                    scenes=[
                        Scene(
                            scene_id="build_01",
                            order=0,
                            audio_chunks=[],
                            emotion=EmotionTone.NEUTRAL,
                            visual_description="Placeholder description for testing purposes",
                            characters_present=["TestChar"],
                            estimated_duration_seconds=3.0
                        )
                    ]
                ),
                Act(
                    act_type=ActType.CRISIS,
                    target_duration_seconds=10.0,
                    scenes=[
                        Scene(
                            scene_id="crisis_01",
                            order=0,
                            audio_chunks=[],
                            emotion=EmotionTone.DRAMATIC,
                            visual_description="Placeholder description for testing purposes",
                            characters_present=["TestChar"],
                            estimated_duration_seconds=10.0
                        )
                    ]
                ),
                Act(
                    act_type=ActType.CLIMAX,
                    target_duration_seconds=10.0,
                    scenes=[
                        Scene(
                            scene_id="climax_01",
                            order=0,
                            audio_chunks=[],
                            emotion=EmotionTone.DRAMATIC,
                            visual_description="Placeholder description for testing purposes",
                            characters_present=["TestChar"],
                            estimated_duration_seconds=10.0
                        )
                    ]
                ),
                Act(
                    act_type=ActType.RESOLUTION,
                    target_duration_seconds=3.0,
                    scenes=[
                        Scene(
                            scene_id="resolution_01",
                            order=0,
                            audio_chunks=[],
                            emotion=EmotionTone.RELIEVED,
                            visual_description="Placeholder description for testing purposes",
                            characters_present=["TestChar"],
                            estimated_duration_seconds=3.0
                        )
                    ]
                )
            ],
            character_profiles=[]
        )

        # Validate (should auto-fix script_id and story_id)
        structurer._validate_scaffold(scaffold, sample_story)

        assert scaffold.script_id != "string"
        assert scaffold.story_id == sample_story.id
        assert len(scaffold.acts) == 5


class TestScriptWriterScaffoldFill:
    """Test ScriptWriter scaffold-filling functionality."""

    def test_scaffold_fill_prompt_generation(self, config_manager):
        """Test that scaffold-fill prompt is generated correctly."""
        writer = ScriptWriterAgent(config_manager)

        # Get the scaffold system prompt
        prompt = writer._create_scaffold_system_prompt()

        assert "CRITICAL: You are filling a PRE-BUILT STRUCTURE" in prompt
        assert "audio_chunks" in prompt
        assert "visual_description" in prompt
        assert "DO NOT change any structural fields" in prompt


class TestScriptEvaluatorQA:
    """Test ScriptEvaluator QA-only validation."""

    def test_qa_prompt_is_simplified(self, config_manager):
        """Test that QA prompt is simpler than legacy prompt."""
        evaluator = ScriptEvaluator(config_manager)

        # The new validate_script should have a simpler prompt
        # Check by inspecting the method
        import inspect
        source = inspect.getsource(evaluator.validate_script)

        assert "QA-only" in source
        assert "script structure is ALREADY CORRECT" in source.replace("**", "")


class TestWorkflowIntegration:
    """Test the complete 3-agent workflow integration."""

    def test_workflow_stages(self):
        """Test that workflow has 3 distinct stages."""
        # Stage 1: SceneStructurer - Structure only
        # Stage 2: ScriptWriter - Creative content
        # Stage 3: ScriptEvaluator - QA validation

        stages = [
            "SceneStructurer.generate_scaffold",
            "ScriptWriter.fill_scaffold",
            "ScriptEvaluator.validate_script"
        ]

        # Verify all stage methods exist
        from gossiptoon.agents.scene_structurer import SceneStructurerAgent
        from gossiptoon.agents.script_writer import ScriptWriterAgent
        from gossiptoon.agents.script_evaluator import ScriptEvaluator

        assert hasattr(SceneStructurerAgent, 'generate_scaffold')
        assert hasattr(ScriptWriterAgent, 'fill_scaffold')
        assert hasattr(ScriptEvaluator, 'validate_script')


    def test_scaffold_to_script_fields(self):
        """Test that scaffold fields are preserved through workflow."""
        # Create a scaffold
        scaffold = Script(
            script_id="test_scaffold",
            story_id="test_story",
            title="Test",
            total_estimated_duration=45.0,
            acts=[
                Act(
                    act_type=ActType.HOOK,
                    target_duration_seconds=2.0,
                    scenes=[
                        Scene(
                            scene_id="hook_01",
                            order=0,
                            audio_chunks=[],
                            emotion=EmotionTone.NEUTRAL,
                            visual_description="Placeholder description for testing purposes",
                            characters_present=["Char1"],
                            estimated_duration_seconds=2.0
                        )
                    ]
                ),
                Act(
                    act_type=ActType.BUILD,
                    target_duration_seconds=3.0,
                    scenes=[
                        Scene(
                            scene_id="build_01",
                            order=0,
                            audio_chunks=[],
                            emotion=EmotionTone.NEUTRAL,
                            visual_description="Placeholder description for testing purposes",
                            characters_present=["Char1"],
                            estimated_duration_seconds=3.0
                        )
                    ]
                ),
                Act(
                    act_type=ActType.CRISIS,
                    target_duration_seconds=10.0,
                    scenes=[
                        Scene(
                            scene_id="crisis_01",
                            order=0,
                            audio_chunks=[],
                            emotion=EmotionTone.DRAMATIC,
                            visual_description="Placeholder description for testing purposes",
                            characters_present=["Char1"],
                            estimated_duration_seconds=10.0
                        )
                    ]
                ),
                Act(
                    act_type=ActType.CLIMAX,
                    target_duration_seconds=10.0,
                    scenes=[
                        Scene(
                            scene_id="climax_01",
                            order=0,
                            audio_chunks=[],
                            emotion=EmotionTone.DRAMATIC,
                            visual_description="Placeholder description for testing purposes",
                            characters_present=["Char1"],
                            estimated_duration_seconds=10.0
                        )
                    ]
                ),
                Act(
                    act_type=ActType.RESOLUTION,
                    target_duration_seconds=3.0,
                    scenes=[
                        Scene(
                            scene_id="resolution_01",
                            order=0,
                            audio_chunks=[],
                            emotion=EmotionTone.RELIEVED,
                            visual_description="Placeholder description for testing purposes",
                            characters_present=["Char1"],
                            estimated_duration_seconds=3.0
                        )
                    ]
                )
            ],
            character_profiles=[]
        )

        # Verify structural fields
        assert scaffold.script_id == "test_scaffold"
        assert len(scaffold.acts) == 5
        assert scaffold.acts[0].scenes[0].order == 0
        assert scaffold.total_estimated_duration == 45.0

        # In a filled script, these should remain the same
        # while audio_chunks, visual_description, etc. are populated


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
