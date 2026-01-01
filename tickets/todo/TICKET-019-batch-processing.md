# TICKET-019: Batch Processing & Queue System

**Priority**: High (P1)  
**Status**: Todo  
**Assignee**: AI Agent  
**Created**: 2025-12-31  
**Depends On**: TICKET-018 (Reddit Auto-Crawler)

## Problem

Currently, users can only generate one video at a time. For content production at scale, we need the ability to queue multiple stories and process them in batch.

## Goal

Implement a batch processing system that can:

1. Queue multiple story URLs
2. Process them sequentially or in parallel
3. Track progress and handle errors gracefully
4. Integrate with discovered stories from TICKET-018

## Requirements

### Functional Requirements

1. **Batch Command**

   - `gossiptoon batch <url1> <url2> ...` - Process multiple URLs
   - `gossiptoon batch --file urls.txt` - Read URLs from file
   - `gossiptoon batch --discover` - Auto-discover and batch process

2. **Progress Tracking**

   - Show overall progress (e.g., "3/10 videos complete")
   - Show current video being processed
   - Estimated time remaining

3. **Error Handling**

   - Continue processing remaining videos if one fails
   - Log errors with context
   - Generate summary report at end

4. **Concurrency Options**
   - Sequential processing (default, safer)
   - Parallel processing (`--parallel N` for N concurrent workers)

### Non-Functional Requirements

1. **Resumability**: Can resume interrupted batch jobs
2. **Resource Management**: Don't exceed API rate limits
3. **Reporting**: Generate summary of successful/failed videos

## Implementation Plan

### Phase A: Batch Command Structure

- [ ] Add `gossiptoon batch` command to CLI
- [ ] Support multiple URL arguments
- [ ] Support `--file` option to read from text file
- [ ] Implement `--discover` integration

### Phase B: Sequential Processing

- [ ] Create `BatchProcessor` class
- [ ] Implement sequential video generation loop
- [ ] Add progress tracking with Rich progress bar
- [ ] Handle errors gracefully (log and continue)

### Phase C: Summary Reporting

- [ ] Track successful/failed videos
- [ ] Generate summary table at end
- [ ] Save detailed log to file

### Phase D (Optional): Parallel Processing

- [ ] Add `--parallel` option
- [ ] Implement worker pool (asyncio.gather with semaphore)
- [ ] Handle rate limiting across workers

## API Design

### BatchProcessor Class

```python
class BatchProcessor:
    def __init__(
        self,
        orchestrator: PipelineOrchestrator,
        max_parallel: int = 1,
    ):
        """Initialize batch processor."""

    async def process_batch(
        self,
        story_urls: List[str],
    ) -> BatchResult:
        """Process multiple stories in batch."""

class BatchResult(BaseModel):
    total: int
    successful: int
    failed: int
    results: List[VideoResult]

class VideoResult(BaseModel):
    url: str
    project_id: Optional[str]
    status: str  # "success" | "failed"
    error: Optional[str]
    output_path: Optional[Path]
```

## CLI Usage Examples

```bash
# Batch process multiple URLs
gossiptoon batch \\
  https://reddit.com/r/AITA/... \\
  https://reddit.com/r/TIFU/...

# Read URLs from file
gossiptoon batch --file stories.txt

# Auto-discover and batch process top 10
gossiptoon batch --discover --limit 10

# Parallel processing (2 concurrent videos)
gossiptoon batch --file stories.txt --parallel 2
```

## Acceptance Criteria

- [ ] Can process multiple URLs sequentially
- [ ] Shows progress for batch operation
- [ ] Continues processing if one video fails
- [ ] Generates summary report
- [ ] Can read URLs from file
- [ ] Integration with `discover` command works
- [ ] E2E test with 3+ stories

## Related Tickets

- TICKET-018: Reddit Auto-Crawler (provides story discovery)
- TICKET-020: Subtitle Fix (ensures video quality)

## Notes

- Start with sequential processing for safety
- Parallel processing is optional (Phase D)
- Consider adding `--dry-run` to preview batch
