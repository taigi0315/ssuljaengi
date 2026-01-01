
import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path.cwd() / "src"))

from gossiptoon.core.config import ConfigManager
from gossiptoon.visual.gemini_client import GeminiImageClient
from gossiptoon.models.visual import ImagePrompt

async def test_visual_fallback():
    try:
        config = ConfigManager()
        # Use invalid model to trigger fallback path
        client = GeminiImageClient(config.api.google_api_key, model="INVALID_MODEL_ID")
        
        print(f"Testing Gemini Image Client Fallback...")
        
        prompt = ImagePrompt(
            scene_id="test_fallback_scene",
            base_prompt="This prompt should fail API and trigger fallback.",
            style="Digital Art",
            aspect_ratio="9:16",
            negative_prompt="bad quality"
        )
        
        output_path = Path("test_fallback_image.png")
        
        # This should print warning and generate placeholder
        path = await client.generate_image(
            prompt=prompt,
            output_path=output_path
        )
        
        print(f"Success! Image saved to {path} (Check if it is a placeholder)")
        
    except Exception as e:
        print(f"Failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(test_visual_fallback())
