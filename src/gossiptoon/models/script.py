"""Script data models for video generation."""

from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from gossiptoon.core.constants import (
    ACT_DURATION_RANGES,
    MAX_SCENE_NARRATION_WORDS,
    MAX_SCRIPT_DURATION,
    MIN_SCRIPT_DURATION,
    ActType,
    CameraEffectType,
    EmotionTone,
)
from gossiptoon.models.audio import AudioChunk, BubbleMetadata
from gossiptoon.models.panel import PanelTemplateType


class CharacterProfile(BaseModel):
    """Profile for a character in the story."""

    name: str = Field(..., description="English name")
    age: str = Field(..., description="Age group (e.g. '20s')")
    gender: str = Field(..., description="Gender")
    role: str = Field(..., description="Role (Protagonist, Antagonist, Supporting)")
    personality_vibe: str = Field(..., description="Personality descriptor")
    body_type: str = Field(..., description="Body type")
    hair_style_color: str = Field(..., description="Hair style and color")
    face_details_expression: str = Field(..., description="Facial details")
    outfit: str = Field(..., description="Outfit description")


class Scene(BaseModel):
    """A single scene within an act.

    Supports both legacy narration-based scenes and new webtoon-style
    multi-character dialogue scenes.
    """

    scene_id: str = Field(..., description="Unique scene identifier")
    act: Optional[ActType] = Field(None, description="Which act this scene belongs to")
    order: int = Field(ge=0, description="Scene order within act")

    # Legacy narration field (optional for backward compatibility)
    narration: Optional[str] = Field(
        None, min_length=10, max_length=500, description="Scene narration (legacy)"
    )

    # NEW: Webtoon-style multi-character dialogue
    audio_chunks: list[AudioChunk] = Field(
        default_factory=list,
        description="Sequence of narration and dialogue chunks for multi-character scenes",
    )

    # NEW: Webtoon panel description
    panel_layout: Optional[str] = Field(
        None,
        min_length=1,
        description="Visual scene description in Korean webtoon panel style",
    )

    # NEW: Chat bubble metadata
    bubble_metadata: list[BubbleMetadata] = Field(
        default_factory=list,
        description="Chat bubble positions and styles for dialogue",
    )

    # NEW: Structured Panel System (Ticket-029)
    panel_template: Optional[PanelTemplateType] = Field(
        None, description="Template ID for multi-panel layouts (e.g. 3-panel vertical)"
    )
    panel_descriptions: Optional[list[str]] = Field(
        None, description="List of visual descriptions per panel (if template selected)"
    )

    # Existing fields
    emotion: EmotionTone = Field(..., description="Emotion tone for TTS")
    visual_description: str = Field(
        ..., min_length=20, description="Detailed visual description for image generation"
    )
    characters_present: list[str] = Field(
        default_factory=list, description="Character names in this scene"
    )
    estimated_duration_seconds: float = Field(
        ge=0.5, le=20.0, description="Estimated scene duration (relaxed max for BUILD/CRISIS acts)"
    )
    camera_effect: Optional[CameraEffectType] = Field(
        default=None, description="Recommended camera movement/effect for this scene"
    )
    visual_sfx: Optional[str] = Field(
        None, description="Optional comic-style sound effect text (e.g., 'BAM!', 'DOOM', 'WHAM!')"
    )

    @field_validator("emotion", mode="before")
    @classmethod
    def validate_emotion_robust(cls, v: Any) -> Any:
        try:
            # If it's a string, check if it's a valid enum value
            if isinstance(v, str):
                # Normalize case
                v = v.lower()
                # Check if valid
                if any(e.value == v for e in EmotionTone):
                    return v
            # If we get here (or if it's already an enum), let Pydantic handle it or fail
            # But to be robust, we can map common errors or default to NEUTRAL
            start_val = v.lower() if isinstance(v, str) else str(v)
            if start_val not in [e.value for e in EmotionTone]:
                print(f"Warning: Invalid emotion '{v}', defaulting to 'neutral'")
                return EmotionTone.NEUTRAL
        except Exception:
            pass
        return v

    @field_validator("camera_effect", mode="before")
    @classmethod
    def validate_camera_effect_robust(cls, v: Any) -> Any:
        if v is None:
            return None
        try:
            if isinstance(v, str):
                v_lower = v.lower()
                if any(e.value == v_lower for e in CameraEffectType):
                    return v_lower

                # Handle common hallucinations
                if v_lower == "quick_cuts":
                    return CameraEffectType.SHAKE  # Best approx

                print(f"Warning: Invalid camera_effect '{v}', defaulting to 'static'")
                return CameraEffectType.STATIC
        except Exception:
            pass
        return v

    @field_validator("narration")
    @classmethod
    def validate_narration_length(cls, v: Optional[str]) -> Optional[str]:
        """Ensure narration is concise for shorts.

        Args:
            v: Narration text

        Returns:
            Validated narration

        Raises:
            ValueError: If narration exceeds word limit
        """
        if v is None:
            return v

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

    def model_post_init(self, __context: Any) -> None:
        """Validate that either narration or audio_chunks is present.

        Raises:
            ValueError: If neither narration nor audio_chunks is provided
        """
        if not self.narration and not self.audio_chunks:
            # Allow empty for scaffold stage
            # print("Warning: Scene has neither 'narration' nor 'audio_chunks' (acceptable for scaffold)")
            pass

    def is_webtoon_style(self) -> bool:
        """Check if this is a webtoon-style scene with dialogue.

        Returns:
            True if scene uses audio_chunks, False if legacy narration
        """
        return len(self.audio_chunks) > 0

    def get_all_speakers(self) -> list[str]:
        """Get unique speakers in this scene.

        Returns:
            List of speaker IDs
        """
        if not self.is_webtoon_style():
            return ["Narrator"]

        speakers = set(chunk.speaker_id for chunk in self.audio_chunks)
        return sorted(list(speakers))

    def get_dialogue_chunks(self) -> list[AudioChunk]:
        """Get only dialogue chunks (exclude narration).

        Returns:
            List of dialogue AudioChunks
        """
        from gossiptoon.models.audio import AudioChunkType

        return [chunk for chunk in self.audio_chunks if chunk.chunk_type == AudioChunkType.DIALOGUE]

    def get_narration_word_count(self) -> int:
        """Get word count of narration.

        Returns:
            Number of words
        """
        return len(self.narration.split())

    class Config:
        """Pydantic config."""

        pass


class Act(BaseModel):
    """Represents one act in the five-act structure."""

    act_type: ActType = Field(..., description="Type of act")
    scenes: list[Scene] = Field(min_length=1, max_length=5, description="Scenes in this act")
    target_duration_seconds: float = Field(ge=1.0, le=20.0, description="Target act duration")

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
            # Auto-correct scene order from LLM (often 1-based)
            if scene.order != idx:
                scene.order = idx
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
    title: str = Field(..., min_length=10, max_length=300, description="Script title")
    acts: list[Act] = Field(min_length=5, max_length=5, description="Five acts")
    total_estimated_duration: float = Field(
        ge=MIN_SCRIPT_DURATION,
        le=MAX_SCRIPT_DURATION,
        description="Total estimated duration",
    )
    target_audience: str = Field(default="general", description="Target audience")
    content_warnings: list[str] = Field(default_factory=list, description="Content warnings if any")
    character_profiles: list[CharacterProfile] = Field(
        default_factory=list, description="Character profiles for consistent visuals/voice"
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
            raise ValueError(f"Acts must be in order {expected_order}, got {actual_order}")

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
            print(f"Warning: Total duration {v}s not optimal for shorts " f"(recommended 50-58s)")
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

        pass
