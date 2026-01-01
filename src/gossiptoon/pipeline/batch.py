"""Batch processing system for multiple video generation."""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field

from gossiptoon.pipeline.orchestrator import PipelineOrchestrator, PipelineResult

logger = logging.getLogger(__name__)


class VideoResult(BaseModel):
    """Result of a single video generation."""

    url: str = Field(..., description="Story URL")
    project_id: Optional[str] = Field(None, description="Project ID if successful")
    status: str = Field(..., description="success | failed")
    error: Optional[str] = Field(None, description="Error message if failed")
    output_path: Optional[Path] = Field(None, description="Output video path")
    duration: Optional[float] = Field(None, description="Video duration in seconds")


class BatchResult(BaseModel):
    """Summary of batch processing results."""

    total: int = Field(..., description="Total number of stories")
    successful: int = Field(..., description="Number of successful videos")
    failed: int = Field(..., description="Number of failed videos")
    results: List[VideoResult] = Field(default_factory=list, description="Individual results")
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    total_duration_seconds: Optional[float] = None


class BatchProcessor:
    """Batch video generation processor."""

    def __init__(
        self,
        orchestrator: PipelineOrchestrator,
        max_parallel: int = 1,
    ):
        """Initialize batch processor.

        Args:
            orchestrator: Pipeline orchestrator instance
            max_parallel: Maximum number of parallel videos (default: 1 = sequential)
        """
        self.orchestrator = orchestrator
        self.max_parallel = max_parallel
        logger.info(f"BatchProcessor initialized (max_parallel={max_parallel})")

    async def process_batch(
        self,
        story_urls: List[str],
    ) -> BatchResult:
        """Process multiple stories in batch.

        Args:
            story_urls: List of Reddit story URLs

        Returns:
            BatchResult with summary and individual results
        """
        logger.info(f"Starting batch processing of {len(story_urls)} stories")

        batch_result = BatchResult(
            total=len(story_urls),
            successful=0,
            failed=0,
        )

        # Process sequentially for now (Phase B)
        for i, url in enumerate(story_urls, 1):
            logger.info(f"Processing story {i}/{len(story_urls)}: {url}")

            try:
                # Run pipeline for this story
                pipeline_result = await self.orchestrator.run(story_url=url)

                if pipeline_result.success:
                    video_result = VideoResult(
                        url=url,
                        project_id=pipeline_result.project_id,
                        status="success",
                        output_path=pipeline_result.video_project.output_path
                        if pipeline_result.video_project
                        else None,
                        duration=pipeline_result.video_project.total_duration
                        if pipeline_result.video_project
                        else None,
                    )
                    batch_result.successful += 1
                    logger.info(f"✓ Story {i} completed successfully")
                else:
                    video_result = VideoResult(
                        url=url,
                        project_id=pipeline_result.project_id,
                        status="failed",
                        error=str(pipeline_result.error),
                    )
                    batch_result.failed +=1
                    logger.warning(f"✗ Story {i} failed: {pipeline_result.error}")

                batch_result.results.append(video_result)

            except Exception as e:
                logger.error(f"✗ Unexpected error processing story {i}: {e}")
                video_result = VideoResult(
                    url=url,
                    status="failed",
                    error=str(e),
                )
                batch_result.failed += 1
                batch_result.results.append(video_result)

        # Finalize
        batch_result.completed_at = datetime.now()
        batch_result.total_duration_seconds = (
            batch_result.completed_at - batch_result.started_at
        ).total_seconds()

        logger.info(
            f"Batch processing complete: "
            f"{batch_result.successful}/{batch_result.total} successful, "
            f"{batch_result.failed} failed"
        )

        return batch_result
