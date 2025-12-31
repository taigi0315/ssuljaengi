"""Visual Director orchestrates image generation with character consistency."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from gossiptoon.core.config import ConfigManager
from gossiptoon.core.exceptions import ImageGenerationError
from gossiptoon.models.script import Script
from gossiptoon.models.visual import ImagePrompt, VisualAsset, VisualProject
from gossiptoon.visual.base import ImageClient
from gossiptoon.visual.character_bank import CharacterConsistencyBank
from gossiptoon.visual.gemini_client import GeminiImageClient

logger = logging.getLogger(__name__)


class VisualDirector:
    """Visual Director orchestrates image generation for all scenes.

    Manages:
    - Image generation per scene
    - Character consistency via I2I
    - Prompt building with character descriptions
    - Visual project assembly
    """

    def __init__(
        self,
        config: ConfigManager,
        image_client: Optional[ImageClient] = None,
    ) -> None:
        """Initialize Visual Director.

        Args:
            config: Configuration manager
            image_client: Optional image client (defaults to Gemini)
        """
        self.config = config

        # Use provided image client or default to Gemini
        self.image_client = image_client or GeminiImageClient(
            api_key=config.api.google_api_key,
            model="imagen-3.0-generate-001",
        )

        logger.info(f"Visual Director initialized with {self.image_client.get_model_name()}")

    async def create_visual_project(
        self,
        script: Script,
    ) -> VisualProject:
        """Create complete visual project for script.

        Args:
            script: Script with all scenes

        Returns:
            VisualProject with all visual assets

        Raises:
            ImageGenerationError: If generation fails
        """
        logger.info(f"Creating visual project for script: {script.script_id}")

        # Initialize character bank
        character_bank = CharacterConsistencyBank(
            project_id=script.script_id,
            storage_dir=self.config.images_dir / "characters",
        )

        # Get all characters from script
        characters = script.get_characters()
        logger.info(f"Script has {len(characters)} characters: {', '.join(characters)}")

        # STEP 1: Pre-generate character portraits FIRST for consistency
        if characters:
            await self._generate_character_portraits(
                script=script,
                characters=characters,
                character_bank=character_bank,
            )

        # STEP 2: Generate images for all scenes (using character refs)
        assets = []
        for scene in script.get_all_scenes():
            asset = await self._generate_scene_image(
                scene=scene,
                character_bank=character_bank,
            )
            assets.append(asset)

        # Create visual project
        visual_project = VisualProject(
            script_id=script.script_id,
            assets=assets,
            character_bank=character_bank.get_all_characters(),
            generation_config={
                "model": self.image_client.get_model_name(),
                "style": self.config.image.style,
                "aspect_ratio": self.config.image.aspect_ratio,
            },
        )

        # Save visual project
        self._save_visual_project(visual_project)

        # Save character bank
        character_bank.save_bank()

        logger.info(
            f"Visual project complete: {len(assets)} assets, "
            f"{len(character_bank.get_all_characters())} characters"
        )

        return visual_project

    async def _generate_character_portraits(
        self,
        script: Script,
        characters: list[str],
        character_bank: CharacterConsistencyBank,
    ) -> None:
        """Generate standalone character portraits BEFORE scene generation.

        This ensures consistent character appearance across all scenes.

        Args:
            script: Script with character info
            characters: List of character names
            character_bank: Character consistency bank
        """
        logger.info(f"Pre-generating {len(characters)} character portraits...")

        for char_name in characters:
            if character_bank.has_character(char_name):
                logger.info(f"Character {char_name} already in bank, skipping")
                continue

            # Get character description from first scene they appear in
            char_description = self._get_character_description_from_script(
                script, char_name
            )

            # Create portrait-specific prompt with strict isolation
            # TICKET-006: Forced single character generation
            portrait_base_prompt = f"""Character design sheet for {char_name}:
{char_description}

FORMAT: Single character full-body portrait on white background.
VIEW: Front facing, neutral expression.
STRICTLY SINGLE CHARACTER. NO background elements, NO other people."""

            portrait_prompt = ImagePrompt(
                scene_id=f"portrait_{char_name.lower().replace(' ', '_')}",
                base_prompt=portrait_base_prompt,
                characters=[char_name],
                style=self.config.image.style,
                aspect_ratio=self.config.image.aspect_ratio,
                negative_prompt=self.config.image.negative_prompt + ", group, couple, multiple people, crowd, background, scenery, text, overlay",
            )

            # Generate portrait image
            output_path = self.config.images_dir / "characters" / script.script_id / f"{char_name.lower().replace(' ', '_')}_portrait.png"
            output_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                portrait_path = await self.image_client.generate_image(
                    prompt=portrait_prompt,
                    output_path=output_path,
                )

                # Add to character bank with portrait as reference
                character_bank.add_character(
                    character_name=char_name,
                    reference_image_path=portrait_path,
                    description=char_description,
                    first_appearance_scene_id="portrait",
                    appearance_tags=[],
                )

                logger.info(f"Generated portrait for {char_name}: {portrait_path}")

            except Exception as e:
                logger.warning(f"Failed to generate portrait for {char_name}: {e}")
                # Continue without portrait - will use scene-based approach as fallback

    def _get_character_description_from_script(
        self,
        script: Script,
        character_name: str,
    ) -> str:
        """Extract character description from script scenes.

        Args:
            script: Script object
            character_name: Character to find

        Returns:
            Character description string
        """
        # Find first scene where character appears
        for scene in script.get_all_scenes():
            if character_name in scene.characters_present:
                # Return the visual description from that scene
                return scene.visual_description

        return f"Character named {character_name}"

    async def _generate_scene_image(
        self,
        scene: any,  # Scene from script
        character_bank: CharacterConsistencyBank,
    ) -> VisualAsset:
        """Generate image for a single scene.

        Args:
            scene: Scene object from script
            character_bank: Character consistency bank

        Returns:
            VisualAsset with generated image
        """
        logger.info(f"Generating image for scene: {scene.scene_id}")

        # Build enhanced prompt with character descriptions for consistency
        base_prompt = scene.visual_description
        
        # Add character descriptions to prompt for Gemini consistency
        # (Since Gemini doesn't support true I2I, we embed descriptions in text)
        character_info_parts = []
        for char_name in scene.characters_present:
            if character_bank.has_character(char_name):
                description = character_bank.get_character_description(char_name)
                if description:
                    # Add SAME character description to maintain consistency
                    character_info_parts.append(
                        f"IMPORTANT - {char_name} must appear exactly as described: {description[:200]}"
                    )

        if character_info_parts:
            enhanced_prompt = f"""{base_prompt}

CHARACTER CONSISTENCY REQUIREMENTS:
{chr(10).join(character_info_parts)}"""
        else:
            enhanced_prompt = base_prompt

        prompt = ImagePrompt(
            scene_id=scene.scene_id,
            base_prompt=enhanced_prompt,
            characters=scene.characters_present,
            style=self.config.image.style,
            aspect_ratio=self.config.image.aspect_ratio,
            negative_prompt=self.config.image.negative_prompt,
        )

        reference_image = None

        # Generate image
        output_path = self.config.images_dir / f"{scene.scene_id}.png"

        image_path = await self.image_client.generate_image(
            prompt=prompt,
            reference_image=reference_image if self.image_client.supports_i2i() else None,
            output_path=output_path,
        )

        # Add new characters to bank (first appearance)
        for char_name in scene.characters_present:
            if not character_bank.has_character(char_name):
                # Extract character description from scene
                char_description = self._extract_character_description(
                    scene.visual_description,
                    char_name,
                )

                character_bank.add_character(
                    character_name=char_name,
                    reference_image_path=image_path,
                    description=char_description,
                    first_appearance_scene_id=scene.scene_id,
                    appearance_tags=[],
                )

                logger.info(f"Added {char_name} to character bank (first appearance)")

        # Create visual asset
        asset = VisualAsset(
            scene_id=scene.scene_id,
            image_path=image_path,
            prompt_used=prompt,
            characters_rendered=scene.characters_present,
            width=1080,
            height=1920,
            camera_effect=scene.camera_effect,  # Propagate AI director's choice
            generation_metadata={
                "model": self.image_client.get_model_name(),
                "used_reference": reference_image is not None,
            },
        )

        logger.info(f"Scene image generated: {image_path}")

        return asset

    def _extract_character_description(
        self,
        visual_description: str,
        character_name: str,
    ) -> str:
        """Extract character description from scene's visual description.

        Args:
            visual_description: Scene's visual description
            character_name: Character name

        Returns:
            Character description (defaults to visual description if not found)
        """
        # TODO: Could use LLM to extract specific character description
        # For now, use the full visual description
        return visual_description

    def _save_visual_project(self, visual_project: VisualProject) -> None:
        """Save visual project to disk.

        Args:
            visual_project: Visual project to save
        """
        output_path = self.config.images_dir / f"{visual_project.script_id}_project.json"

        with open(output_path, "w") as f:
            json.dump(
                visual_project.model_dump(mode="json"),
                f,
                indent=2,
                default=str,
            )

        logger.info(f"Visual project saved to {output_path}")

    async def regenerate_scene_image(
        self,
        visual_project: VisualProject,
        scene_id: str,
        new_description: str,
    ) -> VisualProject:
        """Regenerate image for a specific scene (useful for revisions).

        Args:
            visual_project: Existing visual project
            scene_id: Scene to regenerate
            new_description: New visual description

        Returns:
            Updated visual project
        """
        logger.info(f"Regenerating image for scene: {scene_id}")

        # Find and replace the asset
        for i, asset in enumerate(visual_project.assets):
            if asset.scene_id == scene_id:
                # Update prompt
                prompt = asset.prompt_used
                prompt.base_prompt = new_description

                # Generate new image
                output_path = self.config.images_dir / f"{scene_id}_v2.png"

                image_path = await self.image_client.generate_image(
                    prompt=prompt,
                    reference_image=prompt.reference_image_path,
                    output_path=output_path,
                )

                # Update asset
                visual_project.assets[i].image_path = image_path
                visual_project.assets[i].prompt_used = prompt

                # Save updated project
                self._save_visual_project(visual_project)

                logger.info(f"Scene {scene_id} regenerated successfully")
                return visual_project

        raise ImageGenerationError(f"Scene {scene_id} not found in visual project")
