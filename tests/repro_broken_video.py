
import asyncio
import os
from pathlib import Path
from gossiptoon.video.ffmpeg_builder import FFmpegBuilder, VideoSegment
from gossiptoon.video.effects.ken_burns import KenBurnsConfig, KenBurnsEffect

async def repro_corruption():
    """Reproduce video corruption using testsrc and generated filter graph."""
    builder = FFmpegBuilder(fps=30, output_width=1080, output_height=1920)
    
    # We will manually construct a command that mimics what Assembler produces,
    # but using 'testsrc' instead of file inputs to avoid needing assets.
    # However, FFmpegBuilder takes paths.
    
    # To use FFmpegBuilder as-is, we need dummy files, OR we can mock the input building.
    # Actually, simpler approach: Use the Builder to get the FILTER STRING, then manually run ffmpeg with testsrc.
    
    kb_config = KenBurnsConfig(enabled=True)
    effect = KenBurnsEffect(kb_config)
    
    # We want to see the filter string for an effect segment and a static segment
    
    # 1. Effect Segment Filter
    # Mocking what _apply_effects + standardization does
    # This is effectively unit-testing the filter string generation logic in isolation
    
    # Static Segment Logic from Builder:
    # scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:-1:-1:color=black,setsar=1,format=yuv420p
    
    # Effect Segment Logic from Builder:
    # [v0]zoompan=...[tmp];[tmp]setsar=1,format=yuv420p
    
    print("--- REPRO START ---")
    
    # Let's try to actually run a command with REAL dummy inputs if possible, or just synthetic noise
    # We can generate 2 small dummy images using ffmpeg first
    
    os.system("ffmpeg -y -f lavfi -i color=c=red:s=1080x1920 -frames:v 1 dummy1.png")
    os.system("ffmpeg -y -f lavfi -i color=c=blue:s=1080x1920 -frames:v 1 dummy2.png")
    os.system("ffmpeg -y -f lavfi -i anullsrc=r=44100:cl=stereo -t 6 audio.wav")

    seg1 = VideoSegment(image_path=Path("dummy1.png"), duration=3.0)
    seg2 = VideoSegment(image_path=Path("dummy2.png"), duration=3.0, effects=[effect])
    
    output_file = Path("repro_output.mp4")
    
    cmd = builder.build_video_command(
        segments=[seg1, seg2],
        master_audio=Path("audio.wav"),
        output_file=output_file
    )
    
    cmd_str = cmd.to_string()
    print(f"\nCommand:\n{cmd_str}\n")
    
    import subprocess
    
    # Execute
    print("Executing FFmpeg...")
    # Use to_list() to avoid shell quoting issues with semicolons in filter_complex
    try:
        subprocess.run(cmd.to_list(), check=True)
        exit_code = 0
    except subprocess.CalledProcessError:
        exit_code = 1
    
    if exit_code != 0:
        print("❌ FFmpeg failed to execute!")
        return

    # Check output
    if not output_file.exists():
        print("❌ Output file not found!")
        return
        
    size = output_file.stat().st_size
    print(f"Output size: {size} bytes")
    
    if size < 1000:
        print("❌ File too small (likely corrupt headers only)")
    else:
        print("✅ File generated. Try playing 'repro_output.mp4'.")
        # Run ffprobe to check validity
        os.system(f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {output_file}")

if __name__ == "__main__":
    asyncio.run(repro_corruption())
