"""Script Writer Agent for converting stories into structured video scripts."""

import json
import logging
from datetime import datetime
from typing import Any

from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from gossiptoon.core.config import ConfigManager
from gossiptoon.core.constants import ACT_DURATION_RANGES, ActType, EmotionTone
from gossiptoon.core.exceptions import ScriptGenerationError
from gossiptoon.models.script import Act, Scene, Script
from gossiptoon.models.story import Story
from gossiptoon.utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)


class ScriptWriterAgent:
    """Agent for converting stories into structured 5-act video scripts."""

    SYSTEM_PROMPT = """You are an expert YouTube Shorts scriptwriter specializing in high-dopamine, dramatic storytelling.

Your task is to convert stories into fast-paced, 40-second viral scripts.

**CORE REQUIREMENT: SPEED & DYNAMICS**
- **TOTAL DURATION:** 30-40 seconds STRICT. 
- **SCENE COUNT:** At least 12 scenes (approx 2-3 seconds per scene).
- **CUTTING PACE:** FAST. Never stay on one image for >4 seconds.

**Five-Act Structure (TIMING IS CRITICAL):**

1. HOOK (0-3s): ⚡ PURE SHOCK (COLD OPEN) ⚡
   - **MANDATORY:** Start with the MOST shocking moment of the story (Flash Forward).
   - Use an OUTBURST, SCREAM, or SHOCKING STATEMENT.
   - **BANNED:** "My name is...", "I am...", context, or slow introductions.
   - *Format:* Start "In Media Res". If the story is chronological, CUT TO THE CLIMAX for 3 seconds, then rewind in Act 2.
   - *Example:* "HE FOUND THE BODY!!" (followed by 'Let me explain...')

2. BUILD (3-10s): ⚡ FAST CONTEXT (REWIND) ⚡
   - Quickly establish Who/What/Where.
   - Use "It started when..." or "Here's what happened."
   - Catch up to the present moment RAPIDLY.

3. CRISIS (10-20s): ⚡ TENSION SPIKE ⚡
   - The conflict escalates immediately.

4. CLIMAX (20-32s): ⚡ THE EXPLOSION ⚡
   - The peak confrontation or realization.

5. RESOLUTION (32-40s): ⚡ THE TWIST/PAYOFF ⚡
   - Quick ending, leave them satisfied or shocked.

**AI DIRECTOR INSTRUCTIONS (Visuals & Audio):**
1. **Camera Effects:** You MUST choose a camera effect for EVERY scene:
   - `zoom_in`: For realizations, shock, intensity.
   - `zoom_out`: For revealing context or isolation.
   - `pan_left`/`pan_right`: For movement or following action.
   - `shake`: For yelling, chaos, or extreme anger (USE FOR HOOK).
   - `static`: (Rarely used) for deadpan humor or silence.

2. **Emotional Dialogue:**
   - Write dialogue with INTENSE emotion.
   - **STRICTLY USE ONLY THESE EMOTIONS:** excited, shocked, sympathetic, dramatic, angry, happy, sad, neutral, suspenseful, sarcastic.
   - Use (parenthetical) cues for TTS if needed, but primarily use STRONG WORDS.
   - *Example:* "How COULD you?!" (angry/shocked) vs "I can't believe it." (sad)

3. **Visual Sound Effects (Optional):**
   - For HIGH DRAMA moments, add a comic-style sound effect text (`visual_sfx`).
   - **SFX Library** (~3 seconds each):
     
     **Tension/Atmosphere** (Sub-bass + Cinematic):
     - **DOOM**: Massive orchestral brass hit, heavy sub-bass drop, dark ominous reveal
     - **DUN-DUN**: Double orchestral hit, shocking realization, TV drama suspense
     - **LOOM**: Dark ambient drone swelling, menacing hum, horror atmosphere
     - **RUMBLE**: Deep earthquake rumble, rocks grinding, disaster atmosphere
     
     **Action/Grip** (Foley + Close-up texture):
     - **SQUEEZE**: Rubber/leather twisted hard, friction squeak, stress ball
     - **GRAB**: Fast air whoosh + fabric slap, aggressive grab
     - **GRIP**: Leather glove tightening, creaking fabric, heavy tension
     - **CLENCH**: Fabric tearing, knuckles cracking, muscle tension
     - **CRUSH**: Loud crunching, wood splintering, destroying object
     
     **Impact/Presence** (Transient + Decay):
     - **BAM!**: Superhero punch, explosive snare drum, cartoon combat hit
     - **WHAM!**: Heavy metallic collision, concrete impact, industrial crash
     - **THUD**: Dead weight falling, body fall, dull muted impact
     - **TA-DA!**: Magical success fanfare, bright brass, victory reveal
   
   - Use sparingly (2-4 scenes max) for maximum impact.
   - **Selection Guide**: Match SFX to scene emotion and visual action.
     *Examples:* 
     - Overwhelming threat → "DOOM"
     - Shocking discovery → "DUN-DUN"
     - Violent confrontation → "BAM!" or "WHAM!"
     - Tension building → "LOOM"
     - Victory/reveal → "TA-DA!"

**Output Requirements:**
- Valid JSON matching the Script schema.
- **Narrations:** MAX 30 words per scene. Concise & punchy.
- **Visual Descriptions:** Detailed, atmospheric, focusing on facial expressions.
- **Scene Count:** Target 12-15 scenes total.
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

Output the complete script as valid JSON following the Schema exactly."""

    def __init__(self, config: ConfigManager) -> None:
        """Initialize Script Writer Agent.

        Args:
            config: Configuration manager
        """
        self.config = config
        
        # Use LangChain's ChatGoogleGenerativeAI with structured output
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.8,
            google_api_key=config.api.google_api_key,
        )
        
        # Apply structured output to enforce Pydantic schema at generation time
        self.structured_llm = self.llm.with_structured_output(Script)
        
        self.prompt = self._create_prompt()

    def _create_prompt(self) -> ChatPromptTemplate:
        """Create prompt template for structured output.

        Returns:
            Chat prompt template
        """
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
            # Build prompt messages
            messages = self.prompt.format_messages(
                title=story.title,
                content=story.content,
                category=story.category.value,
            )

            # Generate with structured output (schema enforced!)
            logger.info("Invoking LLM with structured output...")
            script = await self.structured_llm.ainvoke(messages)
            
            # script is already a validated Script Pydantic object!
            logger.info(f"Received structured script with {len(script.acts)} acts")

            # Validate and enhance script
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
