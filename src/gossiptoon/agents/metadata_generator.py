"""YouTube Metadata Generator Agent."""

import logging
from typing import Optional

from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from gossiptoon.core.config import ConfigManager
from gossiptoon.models.metadata import YouTubeMetadata
from gossiptoon.models.script import Script
from gossiptoon.models.story import Story
from gossiptoon.utils.llm_debugger import LLMDebugger

logger = logging.getLogger(__name__)


class MetadataGeneratorAgent:
    """Agent for generating YouTube optimized titles, descriptions, and tags.
    
    Uses Gemini 2.5 Flash to create click-worthy metadata.
    """

    SYSTEM_PROMPT = """You are a World-Class YouTube Growth Expert.
Your goal is to write high-CTR (Click Through Rate) metadata for Reddit Story videos (YouTube Shorts).

# OBJECTIVE
Generate 1 Title, 1 Description, and a list of Tags optimized for the YouTube algorithm.

# RULES FOR TITLE
- MUST be punchy, dramatic, and click-worthy (but not misleading).
- MAX 60 characters (optimized for mobile view).
- Include 1-2 relevant emojis if impactful.
- NO "Part 1" or numbering unless instructed.
- Focus on the main conflict or emotional hook.
- Examples: 
  - "I Canceled My Wedding 😱"
  - "My Mom Stole My Lottery Ticket 😡"
  - "AITA for banning my sister?"

# RULES FOR DESCRIPTION
- Start with a 1-2 sentence "Hook Summary" of the story.
- Include a "Credit" line with EXACT format:
  "📖 Original Story: {source_url}"
  "💬 Read the full discussion and updates on Reddit!"
- Include viral hashtags at the bottom: #shorts #redditstories #aita #reddit
- Tone: Engaging and mysterious.

# RULES FOR TAGS
- Comma-separated list of keywords.
- Include niche tags (e.g., "family drama", "wedding disasters") and broad tags ("reddit", "shorts").
- Lowercase only.

# RULES FOR THUMBNAIL TEXT
- Very short, punchy text to overlay on the video cover.
- Max 3-4 words.
- Example: "SHE DID WHAT?!", "INSTANT KARMA", "WEDDING RUINED"
"""

    USER_PROMPT_TEMPLATE = """Generate YouTube metadata for this story:

SOURCE STORY:
Title: {story_title}
Subreddit: r/{subreddit}
Content: {story_content_preview}...

SCRIPT HOOK:
{hook_content}

Generate:
1. Title (max 60 chars)
2. Description
3. Tags (10-15 tags)
4. Thumbnail Text (max 4 words)
"""

    def __init__(self, config: ConfigManager):
        """Initialize agent.
        
        Args:
            config: Configuration manager
        """
        self.config = config
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=config.api.google_api_key,
            temperature=0.8,  # High creativity for catchy titles
            max_retries=3,
        )
        self.debugger = LLMDebugger(config.outputs_dir)

    async def generate_metadata(
        self,
        story: Story,
        script: Script
    ) -> YouTubeMetadata:
        """Generate YouTube metadata for a story/script.
        
        Args:
            story: The source story
            script: The generated script (to access the hook)
            
        Returns:
            YouTubeMetadata object
        """
        logger.info(f"Generating YouTube metadata for story: {story.id}")

        # Prepare prompt inputs
        hook_scene = script.acts[0].scenes[0] if script.acts and script.acts[0].scenes else None
        hook_text = ""
        
        if hook_scene:
            if hasattr(hook_scene, "audio_chunks") and hook_scene.audio_chunks:
                 # Webtoon style: Combine chunk text
                 hook_text = " ".join([c.text for c in hook_scene.audio_chunks])
            elif hasattr(hook_scene, "narration") and hook_scene.narration:
                 # Legacy style
                 hook_text = hook_scene.narration

        prompt = self._create_prompt()
        
        # Configure structured output
        structured_llm = self.llm.with_structured_output(YouTubeMetadata)

        try:
            # Execute LLM
            formatted_prompt = await prompt.ainvoke({
                "story_title": story.title,
                "subreddit": story.metadata.subreddit if story.metadata else "reddit",
                "source_url": story.metadata.url if story.metadata else "N/A",
                "story_content_preview": story.content[:1000], # First 1000 chars context
                "hook_content": hook_text
            })
            
            response: YouTubeMetadata = await structured_llm.ainvoke(formatted_prompt)

            # Log success
            self.debugger.log_interaction(
                agent_name="MetadataGenerator",
                prompt=formatted_prompt,
                response=response,
                metadata={"story_id": story.id}
            )
            
            logger.info("Metadata generation complete")
            return response

        except Exception as e:
            logger.error(f"Metadata generation failed: {e}")
            self.debugger.log_interaction(
                agent_name="MetadataGenerator",
                prompt=f"FAILED PROMPT GENERATION OR EXECUTION",
                response=str(e),
                metadata={"error": True}
            )
            raise

    def _create_prompt(self) -> ChatPromptTemplate:
        """Create the chat prompt template."""
        return ChatPromptTemplate.from_messages([
            ("system", self.SYSTEM_PROMPT),
            ("human", self.USER_PROMPT_TEMPLATE),
        ])
