"""Test script to manually apply SFX to existing audio."""

import asyncio
import json
from pathlib import Path

from gossiptoon.audio.sfx_mapper import SFXMapper
from gossiptoon.audio.sfx_mixer import AudioSFXMixer
from gossiptoon.models.script import Script

# Project ID
PROJECT_ID = "project_20251231_181426"
PROJECT_DIR = Path(f"outputs/{PROJECT_ID}")

async def test_sfx_overlay():
    """Test SFX overlay on existing project."""
    
    # Load script
    script_files = list((PROJECT_DIR / "scripts").glob("*.json"))
    if not script_files:
        print("No script file found!")
        return
    
    with open(script_files[0]) as f:
        script_data = json.load(f)
    
    script = Script(**script_data)
    
    # Find master audio
    audio_dir = PROJECT_DIR / "audio"
    master_audio = list(audio_dir.glob("*_master*.mp3"))
    if not master_audio:
        print("No master audio found!")
        return
    
    master_audio_path = master_audio[0]
    print(f"Master audio: {master_audio_path}")
    
    # Collect SFX
    mapper = SFXMapper()
    mixer = AudioSFXMixer(sfx_volume=0.7)
    
    sfx_list = []
    current_offset = 0.0
    
    # Load audio project to get segment durations
    audio_project_file = list(audio_dir.glob("*_project.json"))[0]
    with open(audio_project_file) as f:
        audio_data = json.load(f)
    
    segment_durations = [seg["duration_seconds"] for seg in audio_data["segments"]]
    
    for scene, duration in zip(script.get_all_scenes(), segment_durations):
        if hasattr(scene, 'visual_sfx') and scene.visual_sfx:
            print(f"Scene {scene.scene_id}: SFX={scene.visual_sfx} at {current_offset:.2f}s")
            
            sfx_path = mapper.get_sfx_path(scene.visual_sfx)
            if sfx_path and sfx_path.exists():
                sfx_list.append((sfx_path, current_offset))
                print(f"  → {sfx_path}")
            else:
                print(f"  → SFX file NOT FOUND: {scene.visual_sfx}")
        
        current_offset += duration
    
    if sfx_list:
        print(f"\nApplying {len(sfx_list)} SFX...")
        output_path = audio_dir / "master_with_sfx_test.mp3"
        
        mixed_path = mixer.overlay_multiple_sfx(
            master_audio_path,
            sfx_list,
            output_path=output_path
        )
        
        print(f"\n✅ Mixed audio saved to: {mixed_path}")
    else:
        print("\nNo SFX to overlay")

if __name__ == "__main__":
    asyncio.run(test_sfx_overlay())
