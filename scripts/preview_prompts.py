
import asyncio
import logging
from pathlib import Path
from typing import Optional

from gossiptoon.core.config import ConfigManager
from gossiptoon.models.script import Script, Act, Scene
from gossiptoon.core.constants import ActType
from gossiptoon.visual.director import VisualDirector
from gossiptoon.visual.base import ImageClient
from gossiptoon.models.visual import ImagePrompt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockImageClient(ImageClient):
    """Mock client to capture prompts instead of generating images."""
    
    def __init__(self):
        self.captured_prompts = []

    async def generate_image(
        self,
        prompt: ImagePrompt,
        output_path: Path,
        reference_image: Optional[Path] = None,
    ) -> Path:
        logger.info(f"CAPTURED PROMPT for {prompt.scene_id}")
        self.captured_prompts.append({
            "scene_id": prompt.scene_id,
            "base_prompt": prompt.base_prompt,
            "style": prompt.style,
            "negative_prompt": prompt.negative_prompt,
            "characters": prompt.characters
        })
        return output_path # Return dummy path

    def get_model_name(self) -> str:
        return "mock-renderer"

    def supports_i2i(self) -> bool:
        return False

    def get_recommended_params(self) -> dict:
        return {"model": "mock", "quality": "standard"}

async def main():
    config = ConfigManager()
    mock_client = MockImageClient()
    director = VisualDirector(config, image_client=mock_client)

    # 1. Create Mock Script
    scene0 = Scene(
        scene_id="scene_00_intro",
        act=ActType.HOOK,
        order=0,
        nav="INT. CAFE - DAY",
        action="Hero checks his phone.",
        narration="I couldn't believe what I was seeing.",
        emotion="shocked",
        visual_description="A handsome young man (Hero) sitting at a modern cafe table, looking at his smartphone with wide eyes. Sunlight streams through the window.",
        estimated_duration_seconds=5.0,
        characters_present=["Hero"]
    )
    
    act1 = Act(act_type=ActType.HOOK, scenes=[scene0], target_duration_seconds=5.0)
    
    # Fill other acts to satisfy validation
    acts = [act1]
    for act_type in [ActType.BUILD, ActType.CRISIS, ActType.CLIMAX, ActType.RESOLUTION]:
        dummy_scene = Scene(
            scene_id=f"scene_{act_type}_dummy",
            act=act_type,
            order=0,
            narration="Placeholder narration.",
            emotion="neutral",
            visual_description="A placeholder visual description that is definitely long enough to satisfy twenty characters.",
            estimated_duration_seconds=5.0,
            characters_present=[]
        )
        acts.append(Act(act_type=act_type, scenes=[dummy_scene], target_duration_seconds=5.0))

    script = Script(
        script_id="preview_script",
        story_id="preview_story",
        title="Prompt Preview Test",
        acts=acts,
        total_estimated_duration=40.0,
        characters_list=["Hero"] # This triggers character sheet generation
    )

    # 2. Run Director
    await director.create_visual_project(script)

    # 3. Write Report
    output_file = Path("prompt_preview.md")
    with open(output_file, "w") as f:
        f.write("# Visual Prompt Preview\n\n")
        f.write(f"**Global Style**: {config.image.style}\n\n")
        f.write("---\n\n")
        
        for p in mock_client.captured_prompts:
            f.write(f"## ID: {p['scene_id']}\n")
            f.write(f"### Base Prompt\n```text\n{p['base_prompt']}\n```\n")
            f.write(f"### Negative Prompt\n`{p['negative_prompt']}`\n")
            f.write(f"### Style Applied\n`{p['style']}`\n")
            f.write("\n---\n")

    print(f"\n✅ Prompts captured and written to {output_file.absolute()}")

if __name__ == "__main__":
    asyncio.run(main())
