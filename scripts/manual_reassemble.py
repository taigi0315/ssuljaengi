
import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path.cwd() / "src"))

from gossiptoon.core.config import ConfigManager
from gossiptoon.pipeline.checkpoint import CheckpointManager
from gossiptoon.models.audio import AudioProject
from gossiptoon.models.visual import VisualProject
from gossiptoon.video.assembler import VideoAssembler

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def reassemble(project_id: str):
    logger.info(f"Starting manual reassembly for {project_id}")
    
    # 1. Init Config
    config = ConfigManager()
    
    # 2. Set Context
    config.set_job_context(project_id)
    
    # 3. Load Checkpoint
    checkpoint_manager = CheckpointManager(config.checkpoints_dir)
    print(f"DEBUG: Checkpoint Dir: {config.checkpoints_dir}")
    print(f"DEBUG: Checkpoint Path: {checkpoint_manager._get_checkpoint_path(project_id)}")
    
    if not checkpoint_manager.checkpoint_exists(project_id):
        logger.error(f"Checkpoint not found for {project_id}")
        return

    checkpoint = checkpoint_manager.load_checkpoint(project_id)
    
    # 4. Extract Projects
    if not checkpoint.visual_data or "visual_project" not in checkpoint.visual_data:
        logger.error("No visual project in checkpoint")
        return
        
    if not checkpoint.audio_data or "audio_project" not in checkpoint.audio_data:
        logger.error("No audio project in checkpoint")
        return

    visual_project = VisualProject.model_validate(checkpoint.visual_data["visual_project"])
    audio_project = AudioProject.model_validate(checkpoint.audio_data["audio_project"])
    
    logger.info(f"Loaded projects. Visual Assets: {len(visual_project.assets)}, Audio Duration: {audio_project.total_duration}s")
    
    # 5. Initialize Video Assembler
    assembler = VideoAssembler(config)
    
    # 6. Run Assembly
    logger.info("Running assemble_video...")
    video_project = await assembler.assemble_video(visual_project, audio_project)
    
    logger.info(f"Reassembly Complete! Output: {video_project.output_path}")

if __name__ == "__main__":
    PROJECT_ID = "project_20251231_165437"
    asyncio.run(reassemble(PROJECT_ID))
