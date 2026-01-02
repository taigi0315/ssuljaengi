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

# TICKET-028: Standardized Character Sheet Prompt Template
CHARACTER_SHEET_TEMPLATE = """A professional animation character design reference sheet, concept art, full body view of a {age} year old {gender}. {vibe} vibe. {body_type} build. Having {hair} hair, and {face}. Wearing {outfit}. Isolated against a plain solid white background. Focus solely on the character, clean lines, cel-shaded, webtoon style, flat colors, high quality,"""


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
            model="image-generation-002",  # Fallback to stable Imagen 2 (Imagen 3 requires whitelist/preview)
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

            # Check for detailed character profile first (TICKET-028)
            # Use getattr to safely access character_profiles as it might not exist in old scripts
            profiles = getattr(script, "character_profiles", [])
            profile = next((p for p in profiles if p.name == char_name), None)

            if profile:
                logger.info(f"Using detailed profile for character: {char_name}")
                portrait_base_prompt = CHARACTER_SHEET_TEMPLATE.format(
                    age=profile.age.replace(
                        "year old", ""
                    ).strip(),  # Clean up if LLM adds "year old"
                    gender=profile.gender,
                    vibe=profile.personality_vibe,
                    body_type=profile.body_type,
                    hair=profile.hair_style_color,
                    face=profile.face_details_expression,
                    outfit=profile.outfit,
                )
                # Store structural description for bank reference
                char_description = f"{char_name}: {profile.age} {profile.gender}, {profile.hair_style_color}, {profile.outfit}"
            else:
                # Fallback to legacy extraction
                char_description = self._get_character_description_from_script(script, char_name)

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
                negative_prompt=self.config.image.negative_prompt
                + ", group, couple, multiple people, crowd, background, scenery, text, overlay",
            )

            # Generate portrait image
            output_path = (
                self.config.images_dir
                / "characters"
                / script.script_id
                / f"{char_name.lower().replace(' ', '_')}_portrait.png"
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)

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

        Supports both single images and multi-panel layouts (Ticket-029).

        Args:
            scene: Scene object from script
            character_bank: Character consistency bank

        Returns:
            VisualAsset with generated image
        """
        logger.info(f"Generating image for scene: {scene.scene_id}")

        # TICKET-029: Check for multi-panel layout
        from gossiptoon.models.panel import PanelTemplateType

        image_path = None
        prompt_used = None  # Will store primary prompt

        # Condition: Structured Panel System is active and not SINGLE
        if (
            hasattr(scene, "panel_template")
            and scene.panel_template
            and scene.panel_template != PanelTemplateType.SINGLE
            and scene.panel_descriptions
        ):
            logger.info(f"Generating multi-panel layout: {scene.panel_template}")
            panel_images = []

            # Generate each panel
            for idx, desc in enumerate(scene.panel_descriptions):
                logger.info(f"Generating panel {idx+1}/{len(scene.panel_descriptions)}")

                panel_prompt = self._build_prompt(
                    base_description=desc,
                    scene=scene,
                    character_bank=character_bank,
                    is_panel=True,
                    panel_index=idx,
                )

                if idx == 0:
                    prompt_used = panel_prompt  # Store first prompt for metadata

                output_path = self.config.images_dir / f"{scene.scene_id}_panel_{idx}.png"

                p_path = await self.image_client.generate_image(
                    prompt=panel_prompt,
                    output_path=output_path,
                )
                panel_images.append(p_path)

            # Stitch panels
            logger.info("Stitching panels...")
            image_path = self._stitch_panels(
                panel_images, scene.panel_template, self.config.images_dir / f"{scene.scene_id}.png"
            )

        else:
            # Standard Single Image Generation (Legacy + Single Template)
            logger.info("Generating standard single image")

            # Use panel_layout (legacy string) if available and no structured template
            primary_description = scene.visual_description
            if hasattr(scene, "panel_layout") and scene.panel_layout and not scene.panel_template:
                primary_description = scene.panel_layout

            prompt = self._build_prompt(
                base_description=primary_description, scene=scene, character_bank=character_bank
            )
            prompt_used = prompt

            output_path = self.config.images_dir / f"{scene.scene_id}.png"
            image_path = await self.image_client.generate_image(
                prompt=prompt,
                reference_image=None,  # Gemini doesn't fully support I2I yet
                output_path=output_path,
            )

        # Add new characters to bank (first appearance)
        # Scan all prompts/descriptions or just base scene chars
        for char_name in scene.characters_present:
            if not character_bank.has_character(char_name):
                # Use scene's base visual description for extraction if new
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
            prompt_used=prompt_used,
            characters_rendered=scene.characters_present,
            width=1080,
            height=1920,
            camera_effect=scene.camera_effect,
            generation_metadata={
                "model": self.image_client.get_model_name(),
                "template": str(scene.panel_template)
                if hasattr(scene, "panel_template")
                else "single",
                "panel_count": len(scene.panel_descriptions)
                if hasattr(scene, "panel_descriptions") and scene.panel_descriptions
                else 1,
            },
        )

        logger.info(f"Scene image generated: {image_path}")

        return asset

    def _build_prompt(
        self,
        base_description: str,
        scene: any,
        character_bank: CharacterConsistencyBank,
        is_panel: bool = False,
        panel_index: int = 0,
    ) -> ImagePrompt:
        """Helper to build consistent ImagePrompt."""

        character_info_parts = []
        for char_name in scene.characters_present:
            if character_bank.has_character(char_name):
                description = character_bank.get_character_description(char_name)
                if description:
                    character_info_parts.append(
                        f"IMPORTANT - {char_name} must appear exactly as described: {description[:200]}"
                    )

        enhanced_prompt = base_description
        if character_info_parts:
            enhanced_prompt = f"""{base_description}

CHARACTER CONSISTENCY REQUIREMENTS:
{chr(10).join(character_info_parts)}"""

        # Append style instructions
        if hasattr(scene, "panel_layout") and scene.panel_layout and not is_panel:
            enhanced_prompt += (
                "\n\nSTYLE: Vertical Webtoon Panel Layout. Split image into dynamic panels."
            )

        # Panel specific context
        if is_panel:
            enhanced_prompt += f"\n\nCONTEXT: This is panel {panel_index+1} of a vertical webtoon sequence. Close-up, high impact."

        # Add visual SFX
        if hasattr(scene, "visual_sfx") and scene.visual_sfx:
            enhanced_prompt += (
                f"\n\nINCLUDE: Bold comic-style text sound effect '{scene.visual_sfx}'."
            )

        # Add bubble placeholders
        if hasattr(scene, "bubble_metadata") and scene.bubble_metadata:
            enhanced_prompt += "\n\nIMPORTANT: Leave space for speech bubbles. Render text ONLY if explicitly asked."

        return ImagePrompt(
            scene_id=f"{scene.scene_id}_p{panel_index}" if is_panel else scene.scene_id,
            base_prompt=enhanced_prompt,
            characters=scene.characters_present,
            style=self.config.image.style,
            aspect_ratio=self.config.image.aspect_ratio,  # Always generate 9:16 for now and crop? Or maybe 1:1 for panels?
            negative_prompt=self.config.image.negative_prompt,
        )

    def _stitch_panels(self, image_paths: list[Path], template: str, output_path: Path) -> Path:
        """Stitch multiple panel images into a single vertical image."""
        from PIL import Image, ImageOps

        target_w, target_h = 1080, 1920
        canvas = Image.new("RGB", (target_w, target_h), (255, 255, 255))

        count = len(image_paths)
        if count == 0:
            return output_path

        # Simple equal split for now
        # TICKET-029: 3-panel and 4-panel templates
        # Calculate height per panel with gutter
        gutter = 20
        available_h = target_h - (gutter * (count - 1))
        panel_h = available_h // count

        current_y = 0
        for p_path in image_paths:
            img = Image.open(p_path)

            # Smart crop/resize to fill panel slot (target_w x panel_h)
            # Source is likely 9:16 (1080x1920) or similar
            # We need to crop the center to fit 1080 x panel_h

            img_ratio = img.width / img.height
            target_ratio = target_w / panel_h

            if img_ratio > target_ratio:
                # Image is wider than slot - scale to height, crop width
                new_h = panel_h
                new_w = int(new_h * img_ratio)
            else:
                # Image is taller than slot - scale to width, crop height
                new_w = target_w
                new_h = int(new_w / img_ratio)

            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            # Center crop
            left = (new_w - target_w) // 2
            top = (new_h - panel_h) // 2
            right = left + target_w
            bottom = top + panel_h

            img = img.crop((left, top, right, bottom))

            # Paste
            canvas.paste(img, (0, current_y))

            current_y += panel_h + gutter

        canvas.save(output_path)
        return output_path

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
