import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from gossiptoon.core.config import ConfigManager
from gossiptoon.models.story import Story, StoryCategory, RedditPostMetadata
from gossiptoon.agents.script_writer import ScriptWriterAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_refactor():
    try:
        config = ConfigManager()
        
        # Test Story
        metadata = RedditPostMetadata(
            post_id="post_123",
            subreddit="tifu",
            author="tester",
            upvotes=5000,
            num_comments=100,
            created_utc=datetime.utcnow(),
            url="https://reddit.com/r/tifu/comments/test",
            flair="M"
        )

        story = Story(
            id="test_story_001",
            title="TIFU by formatting my script wrong",
            content="""I was trying to write a python script for a video generator. 
            But I mixed up my enums and classes. The compiler yelled at me. 
            Then I refactored everything and used a separate agent for validation.
            It worked! The end.""" * 5, # Make it longer
            category=StoryCategory.TIFU,
            metadata=metadata,
            viral_score=95.0,
            tags=["coding", "fail"]
        )

        agent = ScriptWriterAgent(config)
        
        logger.info("Starting ScriptWriterAgent (Refactored)...")
        script = await agent.write_script(story)
        
        logger.info(f"Script Generated Successfully!")
        logger.info(f"Title: {script.title}")
        logger.info(f"Acts: {len(script.acts)}")
        logger.info(f"Scenes: {script.get_scene_count()}")
        logger.info(f"First Scene Narration: {script.acts[0].scenes[0].narration}")
        
        # Verify strict enums
        for scene in script.get_all_scenes():
            assert scene.emotion is not None
            assert scene.camera_effect is not None
            logger.info(f"Scene {scene.scene_id}: Emotion={scene.emotion.value}, Effect={scene.camera_effect.value}")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        # traceback
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_refactor())
