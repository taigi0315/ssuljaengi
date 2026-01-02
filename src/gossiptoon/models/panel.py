"""Panel layout models for Webtoon-style scene composition.

Defines the structure for multi-panel vertical layouts typical in webtoons.
"""

from enum import Enum
from typing import List
from pydantic import BaseModel


class PanelTemplateType(str, Enum):
    """Available panel layout templates."""

    SINGLE = "single_image"
    VERTICAL_3 = "template_a_3panel"
    VERTICAL_4 = "template_b_4panel"


class PanelConfig(BaseModel):
    """Configuration for a single panel within a layout."""

    panel_index: int
    x: int
    y: int
    width: int
    height: int


class PanelLayout(BaseModel):
    """Complete layout definition for a scene."""

    template_id: PanelTemplateType
    aspect_ratio: tuple[int, int] = (9, 16)
    panels: List[PanelConfig]
