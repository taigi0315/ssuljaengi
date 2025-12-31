"""Checkpoint manager for pipeline state persistence.

Enables pipeline resumption from any stage on failure.
"""

import json
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

from gossiptoon.core.exceptions import CheckpointError

logger = logging.getLogger(__name__)


class PipelineStage(str, Enum):
    """Pipeline execution stages."""

    INITIALIZED = "initialized"
    STORY_FOUND = "story_found"
    SCRIPT_GENERATED = "script_generated"
    AUDIO_GENERATED = "audio_generated"
    VISUALS_GENERATED = "visuals_generated"
    VIDEO_ASSEMBLED = "video_assembled"
    COMPLETED = "completed"


class CheckpointData(BaseModel):
    """Checkpoint state data."""

    project_id: str = Field(..., description="Unique project identifier")
    current_stage: PipelineStage = Field(..., description="Current pipeline stage")
    created_at: datetime = Field(default_factory=datetime.now, description="Checkpoint creation time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")

    # Stage-specific data
    story_data: Optional[dict[str, Any]] = Field(None, description="Story finder output")
    script_data: Optional[dict[str, Any]] = Field(None, description="Script writer output")
    audio_data: Optional[dict[str, Any]] = Field(None, description="Audio generator output")
    visual_data: Optional[dict[str, Any]] = Field(None, description="Visual director output")
    video_data: Optional[dict[str, Any]] = Field(None, description="Video assembler output")

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    error_history: list[str] = Field(default_factory=list, description="Error messages from retries")

    class Config:
        """Pydantic config."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class CheckpointManager:
    """Manages pipeline checkpoints for recovery.

    Features:
    - Save/load checkpoint state
    - Resume from any pipeline stage
    - Track error history for debugging
    - Clean up old checkpoints
    """

    def __init__(self, checkpoint_dir: Path) -> None:
        """Initialize checkpoint manager.

        Args:
            checkpoint_dir: Directory for checkpoint files
        """
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Checkpoint manager initialized: {checkpoint_dir}")

    def save_checkpoint(
        self,
        project_id: str,
        stage: PipelineStage,
        data: dict[str, Any],
    ) -> Path:
        """Save checkpoint for current pipeline stage.

        Args:
            project_id: Project identifier
            stage: Current pipeline stage
            data: Stage-specific data to save

        Returns:
            Path to checkpoint file

        Raises:
            CheckpointError: If save fails
        """
        try:
            checkpoint_path = self._get_checkpoint_path(project_id)

            # Load existing checkpoint or create new one
            if checkpoint_path.exists():
                checkpoint = self.load_checkpoint(project_id)
                checkpoint.current_stage = stage
                checkpoint.updated_at = datetime.now()
            else:
                checkpoint = CheckpointData(
                    project_id=project_id,
                    current_stage=stage,
                )

            # Update stage-specific data
            self._update_stage_data(checkpoint, stage, data)

            # Save to disk
            checkpoint_json = checkpoint.model_dump_json(indent=2)
            checkpoint_path.write_text(checkpoint_json)

            logger.info(f"Checkpoint saved: {project_id} at stage {stage.value}")
            return checkpoint_path

        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            raise CheckpointError(f"Failed to save checkpoint: {e}") from e

    def load_checkpoint(self, project_id: str) -> CheckpointData:
        """Load checkpoint for project.

        Args:
            project_id: Project identifier

        Returns:
            Checkpoint data

        Raises:
            CheckpointError: If checkpoint not found or invalid
        """
        try:
            checkpoint_path = self._get_checkpoint_path(project_id)

            if not checkpoint_path.exists():
                raise CheckpointError(f"No checkpoint found for project: {project_id}")

            checkpoint_json = checkpoint_path.read_text()
            checkpoint = CheckpointData.model_validate_json(checkpoint_json)

            logger.info(f"Checkpoint loaded: {project_id} at stage {checkpoint.current_stage.value}")
            return checkpoint

        except CheckpointError:
            raise
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            raise CheckpointError(f"Failed to load checkpoint: {e}") from e

    def checkpoint_exists(self, project_id: str) -> bool:
        """Check if checkpoint exists for project.

        Args:
            project_id: Project identifier

        Returns:
            True if checkpoint exists
        """
        return self._get_checkpoint_path(project_id).exists()

    def delete_checkpoint(self, project_id: str) -> None:
        """Delete checkpoint for project.

        Args:
            project_id: Project identifier
        """
        checkpoint_path = self._get_checkpoint_path(project_id)
        if checkpoint_path.exists():
            checkpoint_path.unlink()
            logger.info(f"Checkpoint deleted: {project_id}")

    def add_error(self, project_id: str, error_message: str) -> None:
        """Add error message to checkpoint history.

        Args:
            project_id: Project identifier
            error_message: Error message to record
        """
        try:
            checkpoint = self.load_checkpoint(project_id)
            checkpoint.error_history.append(f"{datetime.now().isoformat()}: {error_message}")
            checkpoint.updated_at = datetime.now()

            checkpoint_path = self._get_checkpoint_path(project_id)
            checkpoint_json = checkpoint.model_dump_json(indent=2)
            checkpoint_path.write_text(checkpoint_json)

            logger.debug(f"Error added to checkpoint: {project_id}")

        except Exception as e:
            logger.warning(f"Failed to add error to checkpoint: {e}")

    def list_checkpoints(self) -> list[str]:
        """List all checkpoint project IDs.

        Returns:
            List of project IDs with checkpoints
        """
        checkpoints = []
        for path in self.checkpoint_dir.glob("checkpoint_*.json"):
            project_id = path.stem.replace("checkpoint_", "")
            checkpoints.append(project_id)
        return sorted(checkpoints)

    def clean_old_checkpoints(self, max_age_days: int = 7) -> int:
        """Delete checkpoints older than specified age.

        Args:
            max_age_days: Maximum age in days

        Returns:
            Number of checkpoints deleted
        """
        deleted = 0
        cutoff = datetime.now().timestamp() - (max_age_days * 86400)

        for path in self.checkpoint_dir.glob("checkpoint_*.json"):
            if path.stat().st_mtime < cutoff:
                path.unlink()
                deleted += 1
                logger.debug(f"Deleted old checkpoint: {path.name}")

        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old checkpoints")

        return deleted

    def _get_checkpoint_path(self, project_id: str) -> Path:
        """Get checkpoint file path for project.

        Args:
            project_id: Project identifier

        Returns:
            Path to checkpoint file
        """
        return self.checkpoint_dir / f"checkpoint_{project_id}.json"

    def _update_stage_data(
        self,
        checkpoint: CheckpointData,
        stage: PipelineStage,
        data: dict[str, Any],
    ) -> None:
        """Update stage-specific data in checkpoint.

        Args:
            checkpoint: Checkpoint object
            stage: Pipeline stage
            data: Data to store
        """
        if stage == PipelineStage.STORY_FOUND:
            checkpoint.story_data = data
        elif stage == PipelineStage.SCRIPT_GENERATED:
            checkpoint.script_data = data
        elif stage == PipelineStage.AUDIO_GENERATED:
            checkpoint.audio_data = data
        elif stage == PipelineStage.VISUALS_GENERATED:
            checkpoint.visual_data = data
        elif stage == PipelineStage.VIDEO_ASSEMBLED:
            checkpoint.video_data = data

    def get_next_stage(self, current_stage: PipelineStage) -> Optional[PipelineStage]:
        """Get next pipeline stage.

        Args:
            current_stage: Current stage

        Returns:
            Next stage or None if at end
        """
        stage_order = [
            PipelineStage.INITIALIZED,
            PipelineStage.STORY_FOUND,
            PipelineStage.SCRIPT_GENERATED,
            PipelineStage.AUDIO_GENERATED,
            PipelineStage.VISUALS_GENERATED,
            PipelineStage.VIDEO_ASSEMBLED,
            PipelineStage.COMPLETED,
        ]

        try:
            current_idx = stage_order.index(current_stage)
            if current_idx < len(stage_order) - 1:
                return stage_order[current_idx + 1]
            return None
        except ValueError:
            return None
