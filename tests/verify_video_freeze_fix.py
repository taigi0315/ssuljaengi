
import asyncio
from pathlib import Path
from gossiptoon.video.ffmpeg_builder import FFmpegBuilder, VideoSegment
from gossiptoon.video.effects.ken_burns import KenBurnsConfig, KenBurnsEffect

def test_command_structure():
    """Verify that the generated command contains the standardization filters."""
    builder = FFmpegBuilder()
    
    # Create segments
    seg_static = VideoSegment(image_path=Path("img1.png"), duration=3.0)
    
    kb_config = KenBurnsConfig(enabled=True)
    seg_effect = VideoSegment(
        image_path=Path("img2.png"), 
        duration=3.0,
        effects=[KenBurnsEffect(kb_config)]
    )
    
    audio = Path("audio.mp3")
    output = Path("output.mp4")
    
    cmd = builder.build_video_command(
        segments=[seg_static, seg_effect],
        master_audio=audio,
        output_file=output
    )
    
    cmd_str = cmd.to_string()
    print("Generated Command:\n", cmd_str)
    
    # Verification checks
    # 1. Check static segment standardization
    assert "setsar=1,format=yuv420p" in cmd_str, "Static segment standardization missing"
    
    # 2. Check effect segment standardization
    # Since we added it explicitly, it should appear twice or be present for the effect chain
    # We look for the pattern [tmp_eff_...]setsar=1,format=yuv420p...
    
    if "setsar=1,format=yuv420p" in cmd_str:
        print("\n✅ Standardization filters found!")
    else:
        print("\n❌ Standardization filters MISSING!")
        exit(1)

if __name__ == "__main__":
    test_command_structure()
