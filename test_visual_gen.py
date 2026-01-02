#!/usr/bin/env python3
"""Test script to generate visuals only from existing project."""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gossiptoon.core.config import ConfigManager
from gossiptoon.visual.director import VisualDirector
from gossiptoon.pipeline.checkpoint import CheckpointManager

async def main():
    project_id = "project_20260101_165025"
    
    # Load config
    config = ConfigManager()
    config.set_job_context(project_id)
    
    # Load checkpoint
    checkpoint_mgr = CheckpointManager(config.checkpoints_dir)
    checkpoint = checkpoint_mgr.load_checkpoint(project_id)
    
    print(f"✓ Loaded checkpoint: {checkpoint.current_stage.value}")
    
    # Get script and audio
    script = checkpoint.script_data["script"]
    audio_project = checkpoint.audio_data["audio_project"]
    
    print(f"✓ Script: {len(script['acts'])} acts, {sum(len(act['scenes']) for act in script['acts'])} scenes")
    print(f"✓ Audio: {len(audio_project['segments'])} audio segments")
    
    # Initialize VisualDirector
    visual_director = VisualDirector(config)
    
    # Parse script dict to Script object
    from gossiptoon.models.script import Script
    script_obj = Script(**script)
    
    print("\n🎨 Generating visuals with bubble_metadata...")
    visual_project = await visual_director.create_visual_project(script_obj)
    
    print(f"\n✓ Generated {len(visual_project.assets)} images")
    
    # Check first image for bubbles
    first_scene = script['acts'][0]['scenes'][0]
    bubble_count = len(first_scene.get('bubble_metadata', []))
    print(f"\n📊 First scene has {bubble_count} speech bubbles in metadata")
    print(f"   Image: {visual_project.assets[0].image_path}")
    
    print("\n✅ Visual test complete! Check the generated images.")

if __name__ == "__main__":
    asyncio.run(main())
