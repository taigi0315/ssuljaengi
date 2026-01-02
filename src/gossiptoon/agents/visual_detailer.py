"""Visual Detailer Agent for enriching scene descriptions."""

import logging
from datetime import datetime
from typing import Optional

from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory

from gossiptoon.core.config import ConfigManager
from gossiptoon.core.exceptions import ScriptGenerationError
from gossiptoon.models.script import Script, Scene
from gossiptoon.models.story import Story
from gossiptoon.utils.retry import retry_with_backoff
from gossiptoon.utils.llm_debugger import LLMDebugger

logger = logging.getLogger(__name__)


class VisualDetailerAgent:
    """Agent for enriching visual descriptions with webtoon styling."""

    SYSTEM_PROMPT = """You are a Visual Director for a Premium Korean Webtoon (Manhwa).

**Task**: Enhance the `visual_description` for each scene to be visually stunning, detailed, and specific.

**Style Goal**: "Cinematic Korean Webtoon" (High contrast, dramatic lighting, expressive faces).

**Guidelines:**
1. **Be Specific**: Avoid generic words like "messy room". Use "cramped room piled with takeout boxes and laundry, lit by a blue computer screen".
2. **Focus on Lighting**: Always specify lighting (e.g., "harsh overhead light", "soft morning glow", "dramatic rim lighting").
3. **Camera Angles**: Use cinematic terminology (e.g., "Low angle looking up", "Dutch angle for tension", "Over-the-shoulder").
4. **Character Consistency**: Ensure characters matches their profile (hair, outfit).
5. **Facial Expressions**: Describe micro-expressions (e.g., "eyes trembling", "jaw clenched", "single tear").

**Input**: A script with basic visual descriptions.
**Output**: The same script with ENRICHED visual descriptions.
"""

    def __init__(self, config: ConfigManager) -> None:
        """Initialize Visual Detailer Agent.

        Args:
            config: Configuration manager
        """
        self.config = config

        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        # Use Gemini for speed and visual understanding
        self.llm = ChatGoogleGenerativeAI(
            model=config.llm.visual_detailer_model,
            temperature=config.llm.visual_detailer_temperature,
            google_api_key=config.api.google_api_key,
            safety_settings=safety_settings,
        )

        self.debugger = LLMDebugger(self.config.scripts_dir.parent)

    async def enrich_script_visuals(self, script: Script, story: Story) -> Script:
        """Enrich visual descriptions in the script.

        Args:
            script: Initial script
            story: Source story for context

        Returns:
            Script with enhanced visuals
        """
        logger.info(f"Enriching visuals for script: {script.script_id}")

        try:
            # We process the whole script at once to maintain consistency context
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", self.SYSTEM_PROMPT),
                    (
                        "human",
                        """Enrich the visual descriptions for this script:

**Story**: {title}
**Context**: {content_summary}...

**Script (JSON)**:
{script_json}

**Instructions**:
1. Iterate through every scene in `acts`.
2. Rewrite `visual_description` to be detailed, cinematic, and specific.
3. Rewrite `panel_layout` (if present) to be punchy and dramatic.
4. **KEEP ALL OTHER FIELDS UNCHANGED** (especially audio_chunks, scene_id, structure).
5. Ensure character details (hair/clothes) match `character_profiles`.

Return the COMPLETE validated JSON Script object.
""",
                    ),
                ]
            )
            
            # Prepare data
            import json
            script_json = json.dumps(script.model_dump(mode="json"), indent=2)
            content_summary = story.content[:500]

            logger.info("Calling Visual Detailer (LLM)...")
            start_time = datetime.now()

            # Use structured output to ensure we get a valid Script back
            enriched_script = await self.llm.with_structured_output(Script).ainvoke(
                prompt.format_messages(
                    title=story.title,
                    content_summary=content_summary,
                    script_json=script_json,
                )
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

             # Log interaction
            try:
                self.debugger.log_interaction(
                    agent_name="VisualDetailer",
                    prompt=prompt.format_messages(
                        title=story.title,
                        content_summary=content_summary,
                        script_json="<script_json_omitted>",
                    ),
                    response=enriched_script,
                    metadata={
                        "script_id": script.script_id,
                        "mode": "visual_enrichment",
                    },
                    duration_ms=duration_ms,
                )
            except Exception as log_e:
                logger.warning(f"Failed to log interaction: {log_e}")
            
            logger.info("Visual enrichment complete.")
            return enriched_script

        except Exception as e:
            logger.error(f"Visual enrichment failed: {e}")
            # Fallback: return original script if enrichment fails
            return script
