import sys
from pathlib import Path
import asyncio
import traceback

# Add src to sys.path
sys.path.append(str(Path.cwd() / "src"))

from gossiptoon.pipeline.orchestrator import PipelineOrchestrator
from gossiptoon.core.config import ConfigManager

async def run_resume():
    try:
        config = ConfigManager()
        orchestrator = PipelineOrchestrator(config)
        
        project_id = "project_20251231_131217"
        print(f"Resuming project: {project_id}")
        
        # Manually enable debug prints in orchestrator if needed, but we rely on script output
        await orchestrator.run(project_id=project_id, resume=True)
        print("Resume completed successfully.")
        
    except Exception as e:
        print(f"Error executing resume: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_resume())
