from typing import List, Optional
from pydantic import BaseModel, Field

class YouTubeMetadata(BaseModel):
    """Structured metadata for YouTube video upload."""
    
    title: str = Field(
        ..., 
        description="SEO-optimized video title (max 100 chars)",
        max_length=100
    )
    description: str = Field(
        ..., 
        description="Video description including summary, credits, and hashtags",
        max_length=5000
    )
    tags: List[str] = Field(
        ..., 
        description="List of keywords/tags (max 500 chars total)",
        # No strict validation here, logic layer handles length
    )
    category_id: str = Field(
        default="24",
        description="YouTube Category ID (24 = Entertainment)"
    )
    thumbnail_text: Optional[str] = Field(
        default=None,
        description="Suggested text overlay for the thumbnail"
    )
    
    def to_markdown(self) -> str:
        """Convert to human-readable markdown format."""
        return f"""# YouTube Upload Metadata

## Title
{self.title}

## Description
{self.description}

## Tags
{", ".join(self.tags)}

## Thumbnail Text
{self.thumbnail_text or "N/A"}
"""

    def to_upload_text(self) -> str:
        """Convert to copy-paste friendly text format."""
        return f"""TITLE:
{self.title}

DESCRIPTION:
{self.description}

TAGS:
{",".join(self.tags)}

THUMBNAIL_TEXT:
{self.thumbnail_text or "N/A"}
"""
