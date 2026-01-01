"""Script data models for video generation."""

from typing import Optional

from pydantic import BaseModel, Field, field_validator

from gossiptoon.core.constants import (
    ACT_DURATION_RANGES,
    MAX_SCENE_NARRATION_WORDS,
    MAX_SCRIPT_DURATION,
    MIN_SCRIPT_DURATION,
    ActType,
    CameraEffect,
    EmotionTone,
)


class Scene(BaseModel):
    """A single scene within an act."""

    scene_id: str = Field(..., description="Unique scene identifier")
    act: ActType = Field(..., description="Which act this scene belongs to")
    order: int = Field(ge=0, description="Scene order within act")
    narration: str = Field(..., min_length=10, max_length=500, description="Scene narration")
    emotion: EmotionTone = Field(..., description="Emotion tone for TTS")
    visual_description: str = Field(
        ..., min_length=20, description="Detailed visual description for image generation"
    )
    characters_present: list[str] = Field(
        default_factory=list, description="Character names in this scene"
    )
    estimated_duration_seconds: float = Field(
        ge=0.5, le=15.0, description="Estimated scene duration (shorter max for faster pacing)"
    )
    camera_effect: Optional[CameraEffect] = Field(
        default=None, description="Recommended camera movement/effect for this scene"
    )
    visual_sfx: Optional[str] = Field(
        None,
        description="Optional comic-style sound effect text (e.g., 'BAM!', 'DOOM', 'WHAM!')"
    )

    @field_validator("narration")
    @classmethod
    def validate_narration_length(cls, v: str) -> str:
        """Ensure narration is concise for shorts.

        Args:
            v: Narration text

        Returns:
            Validated narration

        Raises:
            ValueError: If narration exceeds word limit
        """
        word_count = len(v.split())
        if word_count > MAX_SCENE_NARRATION_WORDS:
            raise ValueError(
                f"Narration too long: {word_count} words (max {MAX_SCENE_NARRATION_WORDS})"
            )
        return v

    @field_validator("visual_description")
    @classmethod
    def validate_visual_description(cls, v: str) -> str:
        """Ensure visual description is detailed enough.

        Args:
            v: Visual description

        Returns:
            Validated description
        """
        word_count = len(v.split())
        if word_count < 5:
            raise ValueError("Visual description too short (minimum 5 words)")
        return v

    def get_narration_word_count(self) -> int:
        """Get word count of narration.

        Returns:
            Number of words
        """
        return len(self.narration.split())

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "scene_id": "scene_hook_01",
                "act": "hook",
                "order": 0,
                "narration": "You won't believe what happened at my sister's wedding last week.",
                "emotion": "shocked",
                "visual_description": "A shocked young woman in casual clothes, "
                "standing in a modern living room, hands on her face in disbelief",
                "characters_present": ["narrator"],
                "estimated_duration_seconds": 4.5,
            }
        }


class Act(BaseModel):
    """Represents one act in the five-act structure."""

    act_type: ActType = Field(..., description="Type of act")
    scenes: list[Scene] = Field(min_length=1, max_length=5, description="Scenes in this act")
    target_duration_seconds: float = Field(
        ge=1.0, le=20.0, description="Target act duration"
    )

    @field_validator("scenes")
    @classmethod
    def validate_scene_order(cls, v: list[Scene], info: object) -> list[Scene]:
        """Ensure scenes are properly ordered.

        Args:
            v: List of scenes
            info: Validation info

        Returns:
            Validated scenes

        Raises:
            ValueError: If scene order is invalid
        """
        for idx, scene in enumerate(v):
            if scene.order != idx:
                raise ValueError(f"Scene order mismatch at index {idx}: expected {idx}, got {scene.order}")
        return v

    @field_validator("target_duration_seconds")
    @classmethod
    def validate_duration_range(cls, v: float, info: object) -> float:
        """Validate duration is within acceptable range for act type.

        Args:
            v: Target duration
            info: Validation info

        Returns:
            Validated duration
        """
        # Get act_type from info if available
        if hasattr(info, "data") and "act_type" in info.data:
            act_type = info.data["act_type"]
            if act_type in ACT_DURATION_RANGES:
                min_dur, max_dur = ACT_DURATION_RANGES[act_type]
                if not (min_dur <= v <= max_dur):
                    print(
                        f"Warning: {act_type} duration {v}s outside "
                        f"recommended range {min_dur}-{max_dur}s"
                    )
        return v

    def get_total_estimated_duration(self) -> float:
        """Calculate total estimated duration from scenes.

        Returns:
            Total duration in seconds
        """
        return sum(scene.estimated_duration_seconds for scene in self.scenes)

    def get_all_characters(self) -> list[str]:
        """Get unique characters in this act.

        Returns:
            List of character names
        """
        characters = set()
        for scene in self.scenes:
            characters.update(scene.characters_present)
        return sorted(list(characters))


class Script(BaseModel):
    """Complete video script with five-act structure."""

    script_id: str = Field(..., description="Unique script identifier")
    story_id: str = Field(..., description="Reference to source story")
    title: str = Field(..., min_length=10, max_length=100, description="Script title")
    acts: list[Act] = Field(min_length=5, max_length=5, description="Five acts")
    total_estimated_duration: float = Field(
        ge=MIN_SCRIPT_DURATION,
        le=MAX_SCRIPT_DURATION,
        description="Total estimated duration",
    )
    target_audience: str = Field(default="general", description="Target audience")
    content_warnings: list[str] = Field(
        default_factory=list, description="Content warnings if any"
    )

    @field_validator("acts")
    @classmethod
    def validate_five_acts_in_order(cls, v: list[Act]) -> list[Act]:
        """Ensure all five acts are present in correct order.

        Args:
            v: List of acts

        Returns:
            Validated acts

        Raises:
            ValueError: If acts are not in correct order
        """
        expected_order = [
            ActType.HOOK,
            ActType.BUILD,
            ActType.CRISIS,
            ActType.CLIMAX,
            ActType.RESOLUTION,
        ]
        actual_order = [act.act_type for act in v]

        if actual_order != expected_order:
            raise ValueError(
                f"Acts must be in order {expected_order}, got {actual_order}"
            )

        return v

    @field_validator("total_estimated_duration")
    @classmethod
    def validate_total_duration(cls, v: float) -> float:
        """Warn if duration is not ideal for shorts.

        Args:
            v: Total duration

        Returns:
            Validated duration
        """
        if v < 50 or v > 58:
            print(
                f"Warning: Total duration {v}s not optimal for shorts "
                f"(recommended 50-58s)"
            )
        return v

    def get_all_scenes(self) -> list[Scene]:
        """Flatten all scenes from all acts.

        Returns:
            List of all scenes in order
        """
        return [scene for act in self.acts for scene in act.scenes]

    def get_characters(self) -> list[str]:
        """Extract unique characters across all scenes.

        Returns:
            Sorted list of character names
        """
        characters = set()
        for scene in self.get_all_scenes():
            characters.update(scene.characters_present)
        return sorted(list(characters))

    def get_scene_count(self) -> int:
        """Get total number of scenes.

        Returns:
            Scene count
        """
        return len(self.get_all_scenes())

    def get_act_by_type(self, act_type: ActType) -> Optional[Act]:
        """Get act by type.

        Args:
            act_type: Act type to find

        Returns:
            Act if found, None otherwise
        """
        return next((act for act in self.acts if act.act_type == act_type), None)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "script_id": "script_20250101_abc123",
                "story_id": "story_20250101_abc123",
                "title": "The Wedding Disaster",
                "total_estimated_duration": 55.0,
                "target_audience": "18-35 years old",
            }
        }
