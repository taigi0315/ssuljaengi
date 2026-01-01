"""Engagement models for viewer participation hooks."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EngagementStyle(str, Enum):
    """Types of engagement hooks."""

    QUESTION = "question"  # "Am I wrong here?"
    COMMENT = "comment"  # "Plot twist incoming..."
    REACTION = "reaction"  # "Team Grandma or Team DIL?"
    SYMPATHY = "sympathy"  # "Imagine being in her shoes..."
    CONFLICT = "conflict"  # "Who's the real villain?"


class EngagementHook(BaseModel):
    """Single engagement text overlay."""

    hook_id: str = Field(..., description="Unique ID (e.g., 'hook_crisis_01')")
    text: str = Field(
        ..., description="Display text (max 60 chars)", max_length=60
    )
    scene_id: str = Field(..., description="Which scene to display in")
    timing: float = Field(
        ..., description="Relative position in scene (0.0-1.0)", ge=0.0, le=1.0
    )
    style: EngagementStyle = Field(..., description="Hook type for styling")
    reasoning: str = Field(..., description="Why this hook at this moment")


class EngagementProject(BaseModel):
    """Collection of engagement hooks for a video."""

    hooks: list[EngagementHook] = Field(..., min_length=2, max_length=3)
    strategy: str = Field(..., description="Overall engagement strategy")
