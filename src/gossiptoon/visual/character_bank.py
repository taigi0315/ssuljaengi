"""Character consistency bank for maintaining visual consistency across scenes.

Uses Image-to-Image (I2I) technique: first scene generates character normally,
subsequent scenes use previous image as reference.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from gossiptoon.models.visual import CharacterConsistency

logger = logging.getLogger(__name__)


class CharacterConsistencyBank:
    """Manages character references for visual consistency.

    The "Temporal Bridge" technique:
    - Scene 1: Generate character from text description
    - Scene 2+: Use Scene 1's image as reference for I2I
    - This maintains character appearance across all scenes
    """

    def __init__(self, project_id: str, storage_dir: Path) -> None:
        """Initialize character bank.

        Args:
            project_id: Project identifier
            storage_dir: Directory to store character references
        """
        self.project_id = project_id
        self.storage_dir = storage_dir / project_id
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.characters: dict[str, CharacterConsistency] = {}
        self._load_characters()

    def add_character(
        self,
        character_name: str,
        reference_image_path: Path,
        description: str,
        first_appearance_scene_id: str,
        appearance_tags: Optional[list[str]] = None,
    ) -> CharacterConsistency:
        """Add character to bank.

        Args:
            character_name: Character name
            reference_image_path: Path to reference image
            description: Detailed appearance description
            first_appearance_scene_id: Scene where character first appears
            appearance_tags: Optional appearance tags

        Returns:
            CharacterConsistency object
        """
        logger.info(f"Adding character to bank: {character_name}")

        # Create character reference
        character = CharacterConsistency(
            character_name=character_name,
            reference_image_path=reference_image_path,
            description=description,
            first_appearance_scene_id=first_appearance_scene_id,
            appearance_tags=appearance_tags or [],
        )

        # Store in bank
        self.characters[character_name] = character

        # Save to disk
        self._save_character(character)

        logger.info(f"Character {character_name} added to bank")
        return character

    def get_character(self, character_name: str) -> Optional[CharacterConsistency]:
        """Get character reference.

        Args:
            character_name: Character name

        Returns:
            CharacterConsistency if found, None otherwise
        """
        return self.characters.get(character_name)

    def has_character(self, character_name: str) -> bool:
        """Check if character exists in bank.

        Args:
            character_name: Character name

        Returns:
            True if character exists
        """
        return character_name in self.characters

    def get_reference_image(self, character_name: str) -> Optional[Path]:
        """Get reference image path for character.

        Args:
            character_name: Character name

        Returns:
            Path to reference image if found
        """
        character = self.get_character(character_name)
        if character and character.reference_image_path.exists():
            return character.reference_image_path
        return None

    def get_character_description(self, character_name: str) -> Optional[str]:
        """Get character description for prompts.

        Args:
            character_name: Character name

        Returns:
            Character description if found
        """
        character = self.get_character(character_name)
        return character.description if character else None

    def get_all_characters(self) -> list[CharacterConsistency]:
        """Get all characters in bank.

        Returns:
            List of all characters
        """
        return list(self.characters.values())

    def update_character_reference(
        self,
        character_name: str,
        new_reference_path: Path,
    ) -> None:
        """Update character reference image.

        Useful if a better reference is generated later.

        Args:
            character_name: Character name
            new_reference_path: New reference image path
        """
        if character_name in self.characters:
            self.characters[character_name].reference_image_path = new_reference_path
            self._save_character(self.characters[character_name])
            logger.info(f"Updated reference for {character_name}")

    def _save_character(self, character: CharacterConsistency) -> None:
        """Save character to disk.

        Args:
            character: Character to save
        """
        character_file = self.storage_dir / f"{character.character_name}.json"

        with open(character_file, "w") as f:
            json.dump(character.model_dump(mode="json"), f, indent=2, default=str)

    def _load_characters(self) -> None:
        """Load characters from disk."""
        if not self.storage_dir.exists():
            return

        for character_file in self.storage_dir.glob("*.json"):
            try:
                with open(character_file) as f:
                    data = json.load(f)
                    character = CharacterConsistency.model_validate(data)
                    self.characters[character.character_name] = character
                    logger.debug(f"Loaded character: {character.character_name}")
            except Exception as e:
                logger.warning(f"Failed to load character from {character_file}: {e}")

    def save_bank(self) -> None:
        """Save entire bank metadata to disk."""
        bank_file = self.storage_dir / "bank_metadata.json"

        metadata = {
            "project_id": self.project_id,
            "num_characters": len(self.characters),
            "characters": list(self.characters.keys()),
        }

        with open(bank_file, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Character bank saved: {len(self.characters)} characters")

    def clear_bank(self) -> None:
        """Clear all characters from bank."""
        self.characters.clear()
        logger.info("Character bank cleared")
