"""Script Writer Agent for converting stories into structured video scripts."""

import json
import logging
from datetime import datetime
from typing import Any

from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory

from gossiptoon.core.config import ConfigManager
from gossiptoon.core.constants import ACT_DURATION_RANGES, ActType, EmotionTone, CameraEffectType
from gossiptoon.core.exceptions import ScriptGenerationError
from gossiptoon.models.script import Act, Scene, Script
from gossiptoon.models.story import Story
from gossiptoon.utils.retry import retry_with_backoff
from gossiptoon.agents.script_evaluator import ScriptEvaluator

logger = logging.getLogger(__name__)


class ScriptWriterAgent:
    """Agent for converting stories into structured 5-act video scripts."""

    SYSTEM_PROMPT = """You are a master scriptwriter for YouTube Shorts.

**Task**: Write a compelling, viral 5-Act video script based on a Reddit story.

**Goal**: Maximize viewer retention through fast pacing and strong emotional engagement.

**Vibe**: High energy, dramatic, emotional, but SAFE for general audiences.
- Focus on emotional reactions rather than extreme shock.
- Use natural language.
- Keep it punchy.

**Structure (Five Acts):**
1. **The Hook** (0-3s): Immediate attention grabber. "Flash Forward" to the climax or a shocking statement.
2. **Setup** (3-10s): Context and background.
3. **Escalation** (10-20s): Tension builds.
4. **Climax** (20-35s): Peak moment.
5. **Resolution** (35-45s): Outcome or twist.

**Output Format**:
You can write the script in a loose JSON format or structured blocks. Focus on the CONTENT:
- **Narrations:** MAX 30 words per scene. Concise & punchy.
- **Visuals:** Vivid, comic-book style descriptions.
- **Emotions:** Describe the emotion (e.g., "angry", "sad", "shocked").
- **Camera:** Suggest camera moves (e.g., "zoom in", "pan left").
"""

    USER_PROMPT_TEMPLATE = """Convert this Reddit story into a high-tempo YouTube Short:

**Story Title:** {title}

**Story Content:**
{content}

**Story Category:** {category}

**Instructions:**
1. Read the entire story and identify the key dramatic beats
2. Structure into exactly 5 acts. **Act 1 MUST be a Flash Forward/Cold Open to the Climax.**
3. For each act, create 1-3 scenes with punchy narration
4. Ensure visual descriptions are vivid and specific for image generation
5. Assign emotion tones that match the dramatic intensity
6. Estimate realistic scene durations (consider TTS pacing)

{format_instructions}

Output the draft script. Focus on creativity. Formatting will be handled by the editor."""

    MAX_SCENES = 15
    MIN_SCENES = 12

    def __init__(self, config: ConfigManager) -> None:
        """Initialize Script Writer Agent.

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

        # Use LangChain's ChatGoogleGenerativeAI (Unstructured for creativity)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.9, # High temperature for creativity
            google_api_key=config.api.google_api_key,
            safety_settings=safety_settings,
        )
        self.prompt = self._create_prompt()
        self.evaluator = ScriptEvaluator(config)

    def _create_prompt(self) -> ChatPromptTemplate:
        """Create prompt template with specific constraints.

        Returns:
            Chat prompt template
        """
        # Simplify Prompt - No strict enums
        return ChatPromptTemplate.from_messages(
            [
                ("system", self.SYSTEM_PROMPT),
                ("human", self.USER_PROMPT_TEMPLATE),
            ]
        )

    @retry_with_backoff(max_retries=3, exceptions=(ScriptGenerationError,))
    async def write_script(self, story: Story) -> Script:
        """Generate structured script from story.

        Args:
            story: Story to convert

        Returns:
            Generated script

        Raises:
            ScriptGenerationError: If script generation fails
        """
        logger.info(f"Generating script for story: {story.id}")

        try:
            # Build prompt
            messages = self.prompt.format_messages(
                title=story.title,
                content=story.content,
                category=story.category.value,
                format_instructions="", 
            )
            
            # Step 1: Generate Creative Draft (Unstructured)
            logger.info("Generating creative draft script (unstructured)...")
            response = await self.llm.ainvoke(messages)
            draft_content = response.content
            logger.info(f"Draft generated (length: {len(draft_content)} chars)")

            # Step 2: Evaluate and Format (Strict)
            logger.info("Calling Script Evaluator to format and validate...")
            script = await self.evaluator.evaluate_and_fix(draft_content, story)

            # Validate and enhance script (Metadata, etc)
            script = self._validate_and_enhance_script(script, story)

            logger.info(f"Generated script with {script.get_scene_count()} scenes")

            # Save script
            self._save_script(script)

            return script

        except Exception as e:
            logger.error(f"Script generation failed: {e}")
            raise ScriptGenerationError(f"Failed to generate script: {e}") from e

    def _validate_and_enhance_script(self, script: Script, story: Story) -> Script:
        """Validate script and enhance with metadata.

        Args:
            script: Generated script
            story: Source story

        Returns:
            Validated and enhanced script

        Raises:
            ScriptGenerationError: If validation fails
        """
        # Generate script ID if not set
        if not script.script_id or script.script_id == "string":
            script.script_id = f"script_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{story.id.split('_')[-1]}"

        # Set story ID
        if not script.story_id or script.story_id == "string":
            script.story_id = story.id

        # Validate five acts in order
        self._validate_five_acts(script)

        # Validate durations
        self._validate_durations(script)

        # Validate character consistency
        self._validate_characters(script)

        # Check narration lengths
        self._validate_narration_lengths(script)

        # Backfill scene.act from parent Act if missing (Gemini optimization)
        for act in script.acts:
            for scene in act.scenes:
                if scene.act is None:
                    scene.act = act.act_type

        return script

    def _validate_five_acts(self, script: Script) -> None:
        """Validate that script has exactly 5 acts in correct order.

        Args:
            script: Script to validate

        Raises:
            ScriptGenerationError: If acts are invalid
        """
        if len(script.acts) != 5:
            raise ScriptGenerationError(f"Script must have exactly 5 acts, got {len(script.acts)}")

        expected_order = [
            ActType.HOOK,
            ActType.BUILD,
            ActType.CRISIS,
            ActType.CLIMAX,
            ActType.RESOLUTION,
        ]
        actual_order = [act.act_type for act in script.acts]

        if actual_order != expected_order:
            raise ScriptGenerationError(
                f"Acts must be in order {expected_order}, got {actual_order}"
            )

    def _validate_durations(self, script: Script) -> None:
        """Validate script durations.

        Args:
            script: Script to validate
        """
        total_duration = sum(
            scene.estimated_duration_seconds for scene in script.get_all_scenes()
        )

        if total_duration < 50:
            logger.warning(f"Script duration {total_duration}s is short (target 55-58s)")
        elif total_duration > 65:
            logger.warning(f"Script duration {total_duration}s is long (target 55-58s)")

        # Update total estimated duration
        script.total_estimated_duration = total_duration

        # Validate act durations
        for act in script.acts:
            act_duration = sum(s.estimated_duration_seconds for s in act.scenes)
            if act.act_type in ACT_DURATION_RANGES:
                min_dur, max_dur = ACT_DURATION_RANGES[act.act_type]
                if not (min_dur <= act_duration <= max_dur):
                    logger.warning(
                        f"{act.act_type.value} duration {act_duration}s outside "
                        f"recommended range {min_dur}-{max_dur}s"
                    )

    def _validate_characters(self, script: Script) -> None:
        """Validate character consistency.

        Args:
            script: Script to validate

        Raises:
            ScriptGenerationError: If too many characters
        """
        characters = script.get_characters()

        if len(characters) > 5:
            logger.warning(
                f"Script has {len(characters)} characters (recommended max 5 for visual consistency)"
            )

        logger.info(f"Script characters: {', '.join(characters)}")

    def _validate_narration_lengths(self, script: Script) -> None:
        """Validate narration lengths are appropriate for shorts.

        Args:
            script: Script to validate
        """
        for scene in script.get_all_scenes():
            word_count = len(scene.narration.split())
            if word_count > 50:
                logger.warning(
                    f"Scene {scene.scene_id} narration is long ({word_count} words, max 50)"
                )

    def _save_script(self, script: Script) -> None:
        """Save script to output directory.

        Args:
            script: Script to save
        """
        output_path = self.config.scripts_dir / f"{script.script_id}.json"

        with open(output_path, "w") as f:
            json.dump(script.model_dump(mode="json"), f, indent=2, default=str)

        logger.info(f"Script saved to {output_path}")

        # Also save a human-readable version
        readable_path = self.config.scripts_dir / f"{script.script_id}_readable.txt"
        self._save_readable_script(script, readable_path)

    def _save_readable_script(self, script: Script, output_path: Any) -> None:
        """Save human-readable version of script.

        Args:
            script: Script to save
            output_path: Path to save to
        """
        with open(output_path, "w") as f:
            f.write(f"Script: {script.title}\n")
            f.write(f"ID: {script.script_id}\n")
            f.write(f"Story ID: {script.story_id}\n")
            f.write(f"Total Duration: {script.total_estimated_duration}s\n")
            f.write(f"Characters: {', '.join(script.get_characters())}\n")
            f.write("\n" + "=" * 80 + "\n\n")

            for act in script.acts:
                f.write(f"\n{act.act_type.value.upper()} ({act.target_duration_seconds}s)\n")
                f.write("-" * 80 + "\n\n")

                for scene in act.scenes:
                    f.write(f"Scene {scene.order + 1}: {scene.scene_id}\n")
                    f.write(f"Duration: {scene.estimated_duration_seconds}s\n")
                    f.write(f"Emotion: {scene.emotion.value}\n")
                    f.write(f"Characters: {', '.join(scene.characters_present)}\n\n")
                    f.write(f"NARRATION:\n{scene.narration}\n\n")
                    f.write(f"VISUAL:\n{scene.visual_description}\n\n")
                    f.write("-" * 40 + "\n\n")

        logger.info(f"Readable script saved to {output_path}")
