
import subprocess
import sys
from pathlib import Path

def check_remux(input_file: str):
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"Error: {input_file} not found")
        sys.exit(1)
        
    output_path = input_path.parent / f"remuxed_{input_path.name}"
    
    print(f"Attempting to remux {input_path} to {output_path}...")
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-c", "copy",
        str(output_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Remux successful.")
        print(f"Created {output_path}")
        print("Try playing this file.")
    else:
        print("❌ Remux failed.")
        print("Stderr:")
        print(result.stderr)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 check_remux.py <input_file>")
        sys.exit(1)
    check_remux(sys.argv[1])
