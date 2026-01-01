
import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path.cwd() / "src"))

from gossiptoon.core.config import ConfigManager
from gossiptoon.audio.elevenlabs_client import ElevenLabsClient

async def test_audio():
    try:
        config = ConfigManager()
        client = ElevenLabsClient(config.api.elevenlabs_api_key)
        
        print(f"Testing ElevenLabs with key: {config.api.elevenlabs_api_key[:5]}...")
        
        output_path = Path("test_audio.mp3")
        
        path = await client.generate_speech(
            text="Hello! This is a test of the audio generation system.",
            voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel
            output_path=output_path
        )
        
        print(f"Success! Audio saved to {path}")
        print(f"File size: {path.stat().st_size} bytes")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_audio())
