"""Visual data models for image generation and character consistency."""

from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

from gossiptoon.core.constants import CameraEffect


class CharacterConsistency(BaseModel):
    """Character reference for I2I (image-to-image) consistency."""

    character_name: str = Field(..., description="Character name")
    reference_image_path: Path = Field(..., description="Path to reference image")
    description: str = Field(..., description="Detailed appearance description")
    first_appearance_scene_id: str = Field(
        ..., description="Scene ID where character first appears"
    )
    gemini_reference_id: Optional[str] = Field(
        None, description="Gemini's internal reference for I2I"
    )
    appearance_tags: list[str] = Field(
        default_factory=list, description="Tags for appearance (e.g., 'blonde', 'tall')"
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "character_name": "Sarah",
                "reference_image_path": "/outputs/images/sarah_ref.png",
                "description": "Young woman, mid-20s, blonde shoulder-length hair, "
                "green eyes, casual modern clothing",
                "first_appearance_scene_id": "scene_hook_01",
                "appearance_tags": ["blonde", "green-eyes", "casual"],
            }
        }


class ImagePrompt(BaseModel):
    """Structured prompt for image generation."""

    scene_id: str = Field(..., description="Reference to scene")
    base_prompt: str = Field(..., min_length=20, description="Base prompt from scene description")
    characters: list[str] = Field(default_factory=list, description="Character names in scene")
    style: str = Field(
        default="cinematic digital art, dramatic lighting, 8k quality",
        description="Style modifiers",
    )
    aspect_ratio: str = Field(default="9:16", description="Aspect ratio for vertical video")
    negative_prompt: str = Field(
        default="text, watermark, blurry, low quality, distorted, deformed",
        description="What to avoid in generation",
    )
    use_character_references: bool = Field(
        default=False, description="Whether to use character I2I references"
    )
    reference_image_path: Optional[Path] = Field(
        None, description="Path to reference image for I2I"
    )

    def build_full_prompt(self, character_descriptions: Optional[dict[str, str]] = None) -> str:
        """Construct complete Gemini prompt with character details.

        Args:
            character_descriptions: Dict mapping character names to descriptions

        Returns:
            Complete prompt string
        """
        parts = [self.base_prompt]

        # Add character descriptions if available
        if character_descriptions and self.characters:
            char_details = []
            for char_name in self.characters:
                if char_name in character_descriptions:
                    char_details.append(
                        f"{char_name}: {character_descriptions[char_name]}"
                    )
            if char_details:
                parts.append("Characters: " + ", ".join(char_details))

        # Add style
        parts.append(self.style)

        return ". ".join(parts)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "scene_id": "scene_hook_01",
                "base_prompt": "A shocked young woman standing in a modern living room",
                "characters": ["Sarah"],
                "style": "cinematic digital art, dramatic lighting",
                "aspect_ratio": "9:16",
            }
        }


class VisualAsset(BaseModel):
    """Generated visual asset for a scene."""

    scene_id: str = Field(..., description="Reference to scene")
    image_path: Path = Field(..., description="Path to generated image")
    prompt_used: ImagePrompt = Field(..., description="Prompt used for generation")
    generation_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional generation metadata"
    )
    characters_rendered: list[str] = Field(
        default_factory=list, description="Characters that appear in this image"
    )
    camera_effect: Optional[CameraEffect] = Field(
        default=None, description="Camera effect to apply (pan/zoom/etc)"
    )
    width: int = Field(default=1080, description="Image width in pixels")
    height: int = Field(default=1920, description="Image height in pixels")
    file_size_bytes: Optional[int] = Field(None, description="File size in bytes")

    def get_aspect_ratio(self) -> float:
        """Calculate aspect ratio.

        Returns:
            Aspect ratio (width/height)
        """
        return self.width / self.height if self.height > 0 else 0.0

    def is_vertical(self) -> bool:
        """Check if image is vertical (portrait).

        Returns:
            True if height > width
        """
        return self.height > self.width

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "scene_id": "scene_hook_01",
                "image_path": "/outputs/images/scene_hook_01.png",
                "characters_rendered": ["Sarah"],
                "width": 1080,
                "height": 1920,
            }
        }


class VisualProject(BaseModel):
    """Complete visual project for a script."""

    script_id: str = Field(..., description="Reference to script")
    assets: list[VisualAsset] = Field(..., description="Visual assets for each scene")
    character_bank: list[CharacterConsistency] = Field(
        default_factory=list, description="Character references for consistency"
    )
    generation_config: dict[str, Any] = Field(
        default_factory=dict, description="Configuration used for generation"
    )

    def get_asset_by_scene(self, scene_id: str) -> Optional[VisualAsset]:
        """Get visual asset for scene.

        Args:
            scene_id: Scene identifier

        Returns:
            VisualAsset if found, None otherwise
        """
        return next((a for a in self.assets if a.scene_id == scene_id), None)

    def get_character_reference(self, character_name: str) -> Optional[CharacterConsistency]:
        """Get character reference by name.

        Args:
            character_name: Character name

        Returns:
            CharacterConsistency if found, None otherwise
        """
        return next(
            (c for c in self.character_bank if c.character_name == character_name),
            None,
        )

    def add_character_reference(self, reference: CharacterConsistency) -> None:
        """Add or update character reference.

        Args:
            reference: Character consistency reference
        """
        # Remove existing reference for this character if exists
        self.character_bank = [
            c for c in self.character_bank if c.character_name != reference.character_name
        ]
        # Add new reference
        self.character_bank.append(reference)

    def get_all_characters(self) -> list[str]:
        """Get list of all characters in the project.

        Returns:
            Sorted list of character names
        """
        characters = set()
        for asset in self.assets:
            characters.update(asset.characters_rendered)
        return sorted(list(characters))

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "script_id": "script_20250101_abc123",
                "generation_config": {
                    "model": "gemini-flash-2.5",
                    "style": "cinematic",
                },
            }
        }
