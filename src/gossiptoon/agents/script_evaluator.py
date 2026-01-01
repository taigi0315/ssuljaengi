import logging
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser as LangChainPydanticOutputParser # Avoid conflict if any

from gossiptoon.core.config import ConfigManager
from gossiptoon.models.story import Story
from gossiptoon.models.script import Script, Scene, Act, ActType, EmotionTone, CameraEffectType

logger = logging.getLogger(__name__)

class ScriptEvaluator:
    """Agent responsible for validating, formatting, and polishing the script."""

    SYSTEM_PROMPT = """
You are the Chief Editor and Technical Director for a YouTube Shorts production studio.
Your job is to take a DRAFT SCRIPT and format it into a strict JSON structure for video production.

**Responsibilities:**
1.  **Format Validation**: Ensure the output matches the `Script` schema exactly.
2.  **Enum Correction**: Map descriptions to strict Enums from the ALLOWED LISTS below.
    *   **ALLOWED EMOTIONS**: {valid_emotions}
    *   **ALLOWED CAMERA EFFECTS**: {valid_effects}
    *   **CRITICAL**: You MUST NOT use any value outside these lists. If a draft value is close, map it to the nearest valid one (e.g., "mad" -> `angry`, "zoom" -> `zoom_in`).
3.  **Timing & Pacing**:
    *   Ensure the TOTAL duration is between 50s and 60s.
    *   Adjust `estimated_duration_seconds` for each scene based on word count (approx 2.5 words/sec).
4.  **Structure Enforcement**:
    *   Ensure exactly 5 Acts: Hook, Setup, Crisis, Climax, Resolution.
    *   Hook must be short (0.5-3s).
    *   Climax must be intense (10-15s).

**Input:**
*   Original Reddit Story (for context)
*   Draft Script (text or rough JSON)

**Output:**
*   A fully valid `Script` JSON object.
"""

    def __init__(self, config: ConfigManager):
        self.config = config
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=self.config.api.google_api_key,
            temperature=0.2, # Low temperature for strict validation
            convert_system_message_to_human=True
        )
        self.structured_llm = self.llm.with_structured_output(Script)

    async def evaluate_and_fix(self, draft_content: str, story: Story) -> Script:
        """Process the draft script into a valid Script object."""
        logger.info("Evaluating and formatting draft script...")

        # Prepare dynamic enum lists
        valid_emotions = ", ".join([e.value for e in EmotionTone])
        valid_effects = ", ".join([e.value for e in CameraEffectType])

        prompt = ChatPromptTemplate.from_messages([
            ("system", self.SYSTEM_PROMPT),
            ("user", "ORIGINAL STORY:\n{story_title}\n{story_body}\n\nDRAFT SCRIPT:\n{draft}")
        ])

        chain = prompt | self.structured_llm

        try:
            script = await chain.ainvoke({
                "story_title": story.title,
                "story_body": story.content,
                "draft": draft_content,
                "valid_emotions": valid_emotions,
                "valid_effects": valid_effects
            })
            
            logger.info(f"Script evaluated: {len(script.acts)} acts, {script.get_scene_count()} scenes.")
            return script
        except Exception as e:
            logger.error(f"Script evaluation failed: {e}")
            raise e
