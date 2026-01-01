
import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path.cwd() / "src"))

from gossiptoon.core.config import ConfigManager
from gossiptoon.visual.gemini_client import GeminiImageClient
from gossiptoon.models.visual import ImagePrompt

async def test_visual():
    try:
        config = ConfigManager()
        # Initialize with specific model we are using
        client = GeminiImageClient(config.api.google_api_key, model="imagen-3.0-generate-001")
        
        print(f"Testing Gemini Image Gen with key: {config.api.google_api_key[:5]}...")
        
        prompt = ImagePrompt(
            scene_id="test_scene",
            base_prompt="A cute cat sitting on a windowsill, sunset lighting, cozy atmosphere.",
            style="Digital Art",
            aspect_ratio="9:16",
            negative_prompt="bad quality"
        )
        
        output_path = Path("test_image.png")
        
        path = await client.generate_image(
            prompt=prompt,
            output_path=output_path
        )
        
        print(f"Success! Image saved to {path}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_visual())
