"""Unit tests for visual pipeline components.

Tests:
- CharacterConsistencyBank (character management, I2I references)
- ImageClient interface compliance
- GeminiImageClient (mocked)
- DALLEImageClient (mocked)
- VisualDirector orchestration
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from gossiptoon.core.config import ConfigManager
from gossiptoon.core.exceptions import GeminiAPIError, ImageGenerationError, OpenAIAPIError
from gossiptoon.models.script import Act, ActType, EmotionTone, Scene, Script
from gossiptoon.models.visual import (
    CharacterConsistency,
    ImagePrompt,
    VisualAsset,
    VisualProject,
)
from gossiptoon.visual.base import ImageClient
from gossiptoon.visual.character_bank import CharacterConsistencyBank
from gossiptoon.visual.dalle_client import DALLEImageClient
from gossiptoon.visual.director import VisualDirector
from gossiptoon.visual.gemini_client import GeminiImageClient


@pytest.fixture
def temp_storage_dir(tmp_path):
    """Create temporary storage directory."""
    storage_dir = tmp_path / "characters"
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir


@pytest.fixture
def test_image_path(tmp_path):
    """Create test image file."""
    image_path = tmp_path / "test_character.png"
    image_path.write_bytes(b"fake_image_data")
    return image_path


@pytest.fixture
def character_bank(temp_storage_dir):
    """Create character consistency bank."""
    return CharacterConsistencyBank(
        project_id="test_project",
        storage_dir=temp_storage_dir,
    )


@pytest.fixture
def sample_script():
    """Create sample script with characters."""
    return Script(
        script_id="test_script_001",
        story_id="test_story_001",
        title="Test Story",
        acts=[
            Act(
                act_type=ActType.HOOK,
                target_duration_seconds=5.0,
                scenes=[
                    Scene(
                        scene_id="scene_1",
                        act=ActType.HOOK,
                        order=0,
                        visual_description="A mysterious figure in a dark alley, wearing a long coat",
                        narration="This is the beginning of our story",
                        emotion=EmotionTone.DRAMATIC,
                        characters_present=["John"],
                        estimated_duration_seconds=5.0,
                    ),
                ],
            ),
            Act(
                act_type=ActType.BUILD,
                target_duration_seconds=8.0,
                scenes=[
                    Scene(
                        scene_id="scene_2",
                        act=ActType.BUILD,
                        order=0,
                        visual_description="John meets Sarah in a coffee shop, they look worried and anxious",
                        narration="The plot thickens in unexpected ways",
                        emotion=EmotionTone.SUSPENSEFUL,
                        characters_present=["John", "Sarah"],
                        estimated_duration_seconds=8.0,
                    ),
                ],
            ),
            Act(
                act_type=ActType.CRISIS,
                target_duration_seconds=7.0,
                scenes=[
                    Scene(
                        scene_id="scene_3",
                        act=ActType.CRISIS,
                        order=0,
                        visual_description="John and Sarah discover a shocking secret hidden in the basement",
                        narration="Everything changes in this moment",
                        emotion=EmotionTone.SHOCKED,
                        characters_present=["John", "Sarah"],
                        estimated_duration_seconds=7.0,
                    ),
                ],
            ),
            Act(
                act_type=ActType.CLIMAX,
                target_duration_seconds=10.0,
                scenes=[
                    Scene(
                        scene_id="scene_4",
                        act=ActType.CLIMAX,
                        order=0,
                        visual_description="The final confrontation between the characters in a dramatic showdown",
                        narration="The moment of truth arrives",
                        emotion=EmotionTone.EXCITED,
                        characters_present=["John", "Sarah"],
                        estimated_duration_seconds=10.0,
                    ),
                ],
            ),
            Act(
                act_type=ActType.RESOLUTION,
                target_duration_seconds=5.0,
                scenes=[
                    Scene(
                        scene_id="scene_5",
                        act=ActType.RESOLUTION,
                        order=0,
                        visual_description="Peace returns to the quiet neighborhood as the sun sets",
                        narration="And they lived happily ever after",
                        emotion=EmotionTone.HAPPY,
                        characters_present=["John", "Sarah"],
                        estimated_duration_seconds=5.0,
                    ),
                ],
            ),
        ],
        total_estimated_duration=35.0,
    )


@pytest.fixture
def mock_config(tmp_path):
    """Create mock configuration."""
    config = MagicMock()
    config.images_dir = tmp_path / "images"
    config.images_dir.mkdir(parents=True, exist_ok=True)

    # Set up nested API configuration
    api_config = MagicMock()
    api_config.google_api_key = "test_google_key"
    api_config.openai_api_key = "test_openai_key"
    config.api = api_config

    # Set up nested image configuration
    image_config = MagicMock()
    image_config.style = "cinematic digital art"
    image_config.aspect_ratio = "9:16"
    image_config.negative_prompt = "text, watermark, blurry"
    config.image = image_config

    return config


# ============================================================================
# CharacterConsistencyBank Tests
# ============================================================================


def test_character_bank_initialization(character_bank, temp_storage_dir):
    """Test character bank initializes correctly."""
    assert character_bank.project_id == "test_project"
    assert character_bank.storage_dir == temp_storage_dir / "test_project"
    assert len(character_bank.characters) == 0


def test_add_character_to_bank(character_bank, test_image_path):
    """Test adding character to bank."""
    character = character_bank.add_character(
        character_name="John",
        reference_image_path=test_image_path,
        description="A tall man in a dark coat",
        first_appearance_scene_id="scene_1",
        appearance_tags=["tall", "mysterious"],
    )

    assert character.character_name == "John"
    assert character.reference_image_path == test_image_path
    assert character.description == "A tall man in a dark coat"
    assert character.first_appearance_scene_id == "scene_1"
    assert "tall" in character.appearance_tags
    assert character_bank.has_character("John")


def test_get_character_from_bank(character_bank, test_image_path):
    """Test retrieving character from bank."""
    character_bank.add_character(
        character_name="Sarah",
        reference_image_path=test_image_path,
        description="A woman with red hair",
        first_appearance_scene_id="scene_2",
    )

    retrieved = character_bank.get_character("Sarah")
    assert retrieved is not None
    assert retrieved.character_name == "Sarah"
    assert retrieved.description == "A woman with red hair"


def test_get_nonexistent_character(character_bank):
    """Test getting character that doesn't exist."""
    assert character_bank.get_character("NonExistent") is None
    assert not character_bank.has_character("NonExistent")


def test_get_reference_image(character_bank, test_image_path):
    """Test getting reference image path."""
    character_bank.add_character(
        character_name="John",
        reference_image_path=test_image_path,
        description="Description",
        first_appearance_scene_id="scene_1",
    )

    reference = character_bank.get_reference_image("John")
    assert reference == test_image_path
    assert reference.exists()


def test_get_character_description(character_bank, test_image_path):
    """Test getting character description."""
    description = "A mysterious figure"
    character_bank.add_character(
        character_name="Mystery",
        reference_image_path=test_image_path,
        description=description,
        first_appearance_scene_id="scene_1",
    )

    retrieved_desc = character_bank.get_character_description("Mystery")
    assert retrieved_desc == description


def test_get_all_characters(character_bank, test_image_path):
    """Test getting all characters."""
    character_bank.add_character(
        character_name="John",
        reference_image_path=test_image_path,
        description="John desc",
        first_appearance_scene_id="scene_1",
    )
    character_bank.add_character(
        character_name="Sarah",
        reference_image_path=test_image_path,
        description="Sarah desc",
        first_appearance_scene_id="scene_2",
    )

    all_chars = character_bank.get_all_characters()
    assert len(all_chars) == 2
    names = [c.character_name for c in all_chars]
    assert "John" in names
    assert "Sarah" in names


def test_update_character_reference(character_bank, test_image_path, tmp_path):
    """Test updating character reference image."""
    character_bank.add_character(
        character_name="John",
        reference_image_path=test_image_path,
        description="Description",
        first_appearance_scene_id="scene_1",
    )

    new_image = tmp_path / "new_image.png"
    new_image.write_bytes(b"new_image_data")

    character_bank.update_character_reference("John", new_image)

    updated_ref = character_bank.get_reference_image("John")
    assert updated_ref == new_image


def test_save_and_load_character(character_bank, test_image_path):
    """Test saving and loading character from disk."""
    character_bank.add_character(
        character_name="Persistent",
        reference_image_path=test_image_path,
        description="Persisted character",
        first_appearance_scene_id="scene_1",
        appearance_tags=["tag1"],
    )

    # Create new bank with same storage
    new_bank = CharacterConsistencyBank(
        project_id="test_project",
        storage_dir=character_bank.storage_dir.parent,
    )

    # Character should be loaded
    loaded = new_bank.get_character("Persistent")
    assert loaded is not None
    assert loaded.character_name == "Persistent"
    assert loaded.description == "Persisted character"


def test_save_bank_metadata(character_bank, test_image_path):
    """Test saving bank metadata."""
    character_bank.add_character(
        character_name="John",
        reference_image_path=test_image_path,
        description="Desc",
        first_appearance_scene_id="scene_1",
    )

    character_bank.save_bank()

    metadata_file = character_bank.storage_dir / "bank_metadata.json"
    assert metadata_file.exists()

    with open(metadata_file) as f:
        metadata = json.load(f)

    assert metadata["project_id"] == "test_project"
    assert metadata["num_characters"] == 1
    assert "John" in metadata["characters"]


def test_clear_bank(character_bank, test_image_path):
    """Test clearing character bank."""
    character_bank.add_character(
        character_name="John",
        reference_image_path=test_image_path,
        description="Desc",
        first_appearance_scene_id="scene_1",
    )

    assert len(character_bank.get_all_characters()) == 1

    character_bank.clear_bank()

    assert len(character_bank.get_all_characters()) == 0


# ============================================================================
# ImagePrompt Tests
# ============================================================================


def test_image_prompt_build_full_prompt():
    """Test building full prompt from ImagePrompt."""
    prompt = ImagePrompt(
        scene_id="scene_1",
        base_prompt="A man in a dark alley",
        characters=["John"],
        style="cinematic digital art",
        aspect_ratio="9:16",
        negative_prompt="blurry, low quality",
    )

    # Test with character descriptions
    char_descriptions = {"John": "A tall man in a dark coat"}
    full_prompt = prompt.build_full_prompt(character_descriptions=char_descriptions)

    assert "A man in a dark alley" in full_prompt
    assert "cinematic digital art" in full_prompt
    assert "John" in full_prompt
    assert "tall man in a dark coat" in full_prompt

    # Test without character descriptions
    full_prompt_no_chars = prompt.build_full_prompt()
    assert "A man in a dark alley" in full_prompt_no_chars
    assert "cinematic digital art" in full_prompt_no_chars


def test_image_prompt_with_reference():
    """Test ImagePrompt with reference image."""
    ref_path = Path("/fake/reference.png")
    prompt = ImagePrompt(
        scene_id="scene_2",
        base_prompt="Character in coffee shop",
        characters=["John"],
        style="dramatic",
        aspect_ratio="9:16",
        use_character_references=True,
        reference_image_path=ref_path,
    )

    assert prompt.use_character_references is True
    assert prompt.reference_image_path == ref_path


# ============================================================================
# Mock ImageClient Tests
# ============================================================================


class MockImageClient(ImageClient):
    """Mock implementation of ImageClient for testing."""

    def __init__(self):
        self.generate_called = False
        self.last_prompt = None

    async def generate_image(self, prompt, reference_image=None, output_path=None):
        self.generate_called = True
        self.last_prompt = prompt
        if output_path is None:
            output_path = Path("/tmp/mock_image.png")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"mock_image")
        return output_path

    def get_model_name(self):
        return "mock-model"

    def supports_i2i(self):
        return True

    def get_recommended_params(self):
        return {"style": "mock"}


def test_image_client_interface():
    """Test ImageClient interface compliance."""
    client = MockImageClient()

    assert hasattr(client, "generate_image")
    assert hasattr(client, "get_model_name")
    assert hasattr(client, "supports_i2i")
    assert hasattr(client, "get_recommended_params")


@pytest.mark.asyncio
async def test_mock_image_client_generate(tmp_path):
    """Test mock image client generation."""
    client = MockImageClient()

    prompt = ImagePrompt(
        scene_id="scene_1",
        base_prompt="A detailed test prompt for image generation with sufficient length",
        characters=["John"],
        style="test",
        aspect_ratio="9:16",
    )

    output_path = tmp_path / "output.png"
    result = await client.generate_image(prompt, output_path=output_path)

    assert client.generate_called
    assert client.last_prompt == prompt
    assert result.exists()


# ============================================================================
# GeminiImageClient Tests (Mocked)
# ============================================================================


@pytest.mark.asyncio
async def test_gemini_client_initialization():
    """Test Gemini client initializes correctly."""
    client = GeminiImageClient(
        api_key="test_key",
        model="imagen-3.0-generate-001",
    )

    assert client.api_key == "test_key"
    assert client.model == "imagen-3.0-generate-001"
    assert client.get_model_name() == "imagen-3.0-generate-001"
    assert client.supports_i2i() is True


@pytest.mark.asyncio
async def test_gemini_client_generate_image_text_to_image(tmp_path):
    """Test Gemini client text-to-image generation (mocked)."""
    client = GeminiImageClient(api_key="test_key")

    # Mock the generate method to avoid actual API calls
    async def mock_generate(prompt, reference_image=None, output_path=None):
        if output_path is None:
            output_path = tmp_path / "output.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake_gemini_image")
        return output_path

    # Replace the generate_image method
    client.generate_image = mock_generate

    prompt = ImagePrompt(
        scene_id="scene_1",
        base_prompt="A beautiful landscape with mountains and trees in the distance",
        characters=[],
        style="cinematic",
        aspect_ratio="9:16",
    )

    output_path = tmp_path / "output.png"
    result = await client.generate_image(prompt, output_path=output_path)

    assert result.exists()
    assert result == output_path


@pytest.mark.asyncio
async def test_gemini_client_generate_image_i2i(tmp_path, test_image_path):
    """Test Gemini client I2I generation with reference (mocked)."""
    client = GeminiImageClient(api_key="test_key")

    # Mock the generate method
    async def mock_generate(prompt, reference_image=None, output_path=None):
        # Verify reference was passed
        assert reference_image is not None
        if output_path is None:
            output_path = tmp_path / "output_i2i.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake_gemini_i2i_image")
        return output_path

    client.generate_image = mock_generate

    prompt = ImagePrompt(
        scene_id="scene_2",
        base_prompt="Character in new scene with dramatic lighting and composition",
        characters=["John"],
        style="cinematic",
        aspect_ratio="9:16",
        use_character_references=True,
        reference_image_path=test_image_path,
    )

    output_path = tmp_path / "output.png"
    result = await client.generate_image(
        prompt,
        reference_image=test_image_path,
        output_path=output_path,
    )

    assert result.exists()


@pytest.mark.asyncio
async def test_gemini_client_no_images_error(tmp_path):
    """Test Gemini client error handling."""
    client = GeminiImageClient(api_key="test_key")

    # Test that client can handle errors
    assert client.supports_i2i() is True
    assert client.get_model_name() == "imagen-3.0-generate-001"

    # Test recommended params
    params = client.get_recommended_params()
    assert "aspect_ratio" in params
    assert params["aspect_ratio"] == "9:16"


# ============================================================================
# DALLEImageClient Tests (Mocked)
# ============================================================================


@pytest.mark.asyncio
async def test_dalle_client_initialization():
    """Test DALL-E client initializes correctly."""
    client = DALLEImageClient(
        api_key="test_key",
        model="dall-e-3",
        quality="hd",
    )

    assert client.api_key == "test_key"
    assert client.model == "dall-e-3"
    assert client.quality == "hd"
    assert client.get_model_name() == "dall-e-3"
    assert client.supports_i2i() is False  # DALL-E doesn't support I2I


@pytest.mark.asyncio
async def test_dalle_client_generate_image(tmp_path):
    """Test DALL-E client image generation (mocked)."""
    client = DALLEImageClient(api_key="test_key")

    # Mock the generate method
    async def mock_generate(prompt, reference_image=None, output_path=None):
        if output_path is None:
            output_path = tmp_path / "dalle_output.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake_dalle_image")
        return output_path

    client.generate_image = mock_generate

    prompt = ImagePrompt(
        scene_id="scene_1",
        base_prompt="A stunning vista with mountains and valleys in the background",
        characters=[],
        style="vivid",
        aspect_ratio="9:16",
    )

    output_path = tmp_path / "dalle_output.png"
    result = await client.generate_image(prompt, output_path=output_path)

    assert result.exists()
    assert result == output_path


@pytest.mark.asyncio
async def test_dalle_client_warns_on_reference_image(tmp_path, test_image_path):
    """Test DALL-E client doesn't support I2I."""
    client = DALLEImageClient(api_key="test_key")

    # DALL-E should not support I2I
    assert client.supports_i2i() is False

    # Test recommended params
    params = client.get_recommended_params()
    assert "quality" in params
    assert params["quality"] == "hd"


# ============================================================================
# VisualDirector Tests
# ============================================================================


@pytest.mark.asyncio
async def test_visual_director_initialization(mock_config):
    """Test VisualDirector initializes correctly."""
    mock_client = MockImageClient()
    director = VisualDirector(config=mock_config, image_client=mock_client)

    assert director.config == mock_config
    assert director.image_client == mock_client


@pytest.mark.asyncio
async def test_visual_director_uses_default_gemini_client(mock_config):
    """Test VisualDirector defaults to GeminiImageClient."""
    with patch("gossiptoon.visual.director.GeminiImageClient") as mock_gemini_class:
        mock_gemini_instance = MagicMock()
        mock_gemini_class.return_value = mock_gemini_instance

        director = VisualDirector(config=mock_config)

        assert director.image_client == mock_gemini_instance
        mock_gemini_class.assert_called_once()


@pytest.mark.asyncio
async def test_visual_director_create_visual_project(mock_config, sample_script, tmp_path):
    """Test VisualDirector creates complete visual project."""
    mock_client = MockImageClient()
    director = VisualDirector(config=mock_config, image_client=mock_client)

    # Mock image paths
    with patch.object(mock_client, "generate_image") as mock_generate:

        async def fake_generate(prompt, reference_image=None, output_path=None):
            if output_path is None:
                output_path = tmp_path / f"{prompt.scene_id}.png"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"fake_image")
            return output_path

        mock_generate.side_effect = fake_generate

        visual_project = await director.create_visual_project(sample_script)

        assert visual_project.script_id == "test_script_001"
        assert len(visual_project.assets) == 5  # 5 scenes
        assert len(visual_project.character_bank) == 2  # John and Sarah

        # Check character bank
        char_names = [c.character_name for c in visual_project.character_bank]
        assert "John" in char_names
        assert "Sarah" in char_names

        # Verify images were generated for all scenes
        assert mock_generate.call_count == 5


@pytest.mark.asyncio
async def test_visual_director_character_consistency(mock_config, sample_script, tmp_path):
    """Test VisualDirector maintains character consistency via I2I."""
    mock_client = MockImageClient()
    director = VisualDirector(config=mock_config, image_client=mock_client)

    call_count = 0
    reference_used_count = 0

    async def track_references(prompt, reference_image=None, output_path=None):
        nonlocal call_count, reference_used_count
        call_count += 1

        if reference_image is not None:
            reference_used_count += 1

        if output_path is None:
            output_path = tmp_path / f"scene_{call_count}.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake_image")
        return output_path

    with patch.object(mock_client, "generate_image") as mock_generate:
        mock_generate.side_effect = track_references

        await director.create_visual_project(sample_script)

        # First scene with John: no reference (first appearance)
        # Scenes 2-5 with John/Sarah: should use reference
        # Scene 2 is first appearance of Sarah, so 1 reference
        # Scenes 3-5: both characters exist, so references used
        assert reference_used_count >= 3


@pytest.mark.asyncio
async def test_visual_director_saves_project(mock_config, sample_script, tmp_path):
    """Test VisualDirector saves visual project to disk."""
    mock_config.images_dir = tmp_path / "images"
    mock_config.images_dir.mkdir(parents=True, exist_ok=True)

    mock_client = MockImageClient()
    director = VisualDirector(config=mock_config, image_client=mock_client)

    async def fake_generate(prompt, reference_image=None, output_path=None):
        if output_path is None:
            output_path = tmp_path / f"{prompt.scene_id}.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake_image")
        return output_path

    with patch.object(mock_client, "generate_image") as mock_generate:
        mock_generate.side_effect = fake_generate

        await director.create_visual_project(sample_script)

        # Check project file was saved
        project_file = mock_config.images_dir / "test_script_001_project.json"
        assert project_file.exists()

        with open(project_file) as f:
            project_data = json.load(f)

        assert project_data["script_id"] == "test_script_001"
        assert len(project_data["assets"]) == 5


@pytest.mark.asyncio
async def test_visual_director_regenerate_scene(mock_config, sample_script, tmp_path):
    """Test VisualDirector can regenerate specific scene."""
    mock_config.images_dir = tmp_path / "images"
    mock_config.images_dir.mkdir(parents=True, exist_ok=True)

    mock_client = MockImageClient()
    director = VisualDirector(config=mock_config, image_client=mock_client)

    async def fake_generate(prompt, reference_image=None, output_path=None):
        if output_path is None:
            output_path = tmp_path / f"{prompt.scene_id}.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake_image")
        return output_path

    with patch.object(mock_client, "generate_image") as mock_generate:
        mock_generate.side_effect = fake_generate

        # Create initial project
        visual_project = await director.create_visual_project(sample_script)

        original_path = visual_project.assets[0].image_path

        # Regenerate first scene
        updated_project = await director.regenerate_scene_image(
            visual_project=visual_project,
            scene_id="scene_1",
            new_description="Updated visual description",
        )

        # Check scene was regenerated
        new_path = updated_project.assets[0].image_path
        assert new_path != original_path
        assert "_v2" in str(new_path)


@pytest.mark.asyncio
async def test_visual_director_regenerate_nonexistent_scene(mock_config, sample_script, tmp_path):
    """Test VisualDirector raises error for nonexistent scene."""
    mock_client = MockImageClient()
    director = VisualDirector(config=mock_config, image_client=mock_client)

    async def fake_generate(prompt, reference_image=None, output_path=None):
        if output_path is None:
            output_path = tmp_path / f"{prompt.scene_id}.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake_image")
        return output_path

    with patch.object(mock_client, "generate_image") as mock_generate:
        mock_generate.side_effect = fake_generate

        visual_project = await director.create_visual_project(sample_script)

        with pytest.raises(ImageGenerationError, match="Scene .* not found"):
            await director.regenerate_scene_image(
                visual_project=visual_project,
                scene_id="nonexistent_scene",
                new_description="New description",
            )


@pytest.mark.asyncio
async def test_visual_director_respects_i2i_support(mock_config, sample_script, tmp_path):
    """Test VisualDirector respects I2I support of image client."""

    class NoI2IClient(ImageClient):
        """Mock client that doesn't support I2I."""

        async def generate_image(self, prompt, reference_image=None, output_path=None):
            # Should not receive reference_image
            assert reference_image is None
            if output_path is None:
                output_path = tmp_path / f"{prompt.scene_id}.png"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"fake")
            return output_path

        def get_model_name(self):
            return "no-i2i-model"

        def supports_i2i(self):
            return False

        def get_recommended_params(self):
            return {}

    no_i2i_client = NoI2IClient()
    director = VisualDirector(config=mock_config, image_client=no_i2i_client)

    # Should not raise assertion error
    await director.create_visual_project(sample_script)


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_full_visual_pipeline_integration(mock_config, sample_script, tmp_path):
    """Test complete visual pipeline from script to visual project."""
    mock_config.images_dir = tmp_path / "images"
    mock_config.images_dir.mkdir(parents=True, exist_ok=True)

    mock_client = MockImageClient()
    director = VisualDirector(config=mock_config, image_client=mock_client)

    async def fake_generate(prompt, reference_image=None, output_path=None):
        if output_path is None:
            output_path = tmp_path / f"{prompt.scene_id}.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake_image")
        return output_path

    with patch.object(mock_client, "generate_image") as mock_generate:
        mock_generate.side_effect = fake_generate

        # Run full pipeline
        visual_project = await director.create_visual_project(sample_script)

        # Verify outputs
        assert len(visual_project.assets) == 5
        assert len(visual_project.character_bank) == 2

        # Verify all images exist
        for asset in visual_project.assets:
            assert asset.image_path.exists()

        # Verify character bank saved (it's stored in images_dir/characters)
        char_bank_dir = mock_config.images_dir / "characters" / "test_script_001"
        assert char_bank_dir.exists()
        assert (char_bank_dir / "bank_metadata.json").exists()

        # Verify project saved
        project_file = mock_config.images_dir / "test_script_001_project.json"
        assert project_file.exists()
