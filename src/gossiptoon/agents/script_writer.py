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

    SYSTEM_PROMPT = """You are a master Korean Webtoon scriptwriter for YouTube Shorts.

**Task**: Write a compelling, dialogue-driven 5-Act video script based on a Reddit story.

**Goal**: Maximize viewer retention through multi-character dialogue, dramatic interactions, and emotional engagement.

**Style**: Korean Webtoon - vibrant, expressive, dialogue-heavy, with chat bubbles and dynamic panel compositions.

**CRITICAL: Multi-Character Dialogue**
- Transform narration into CHARACTER DIALOGUE whenever possible
- Use 2-5 characters per story
- Create conversations, confrontations, and emotional exchanges
- Narrator only for scene-setting or transitions

**Structure (Five Acts):**
1. **The Hook** (0-3s): Immediate dialogue hook or dramatic statement
2. **Setup** (3-10s): Character introduction through dialogue
3. **Escalation** (10-20s): Tension builds through conversation/confrontation
4. **Climax** (20-35s): Peak emotional dialogue exchange
5. **Resolution** (35-45s): Outcome revealed through dialogue or reflection

**Scene Structure (WEBTOON STYLE):**
Each scene must have:

1. **audio_chunks** (list): Sequence of narration and dialogue
   - chunk_type: "narration", "dialogue", or "internal"
   - speaker_id: Character name or "Narrator"
   - speaker_gender: "male" or "female" (for voice selection)
   - text: What is said (MAX 30 words)
   - director_notes: Detailed TTS style instruction
   - bubble_position: "top-left", "top-right", "center", "bottom-left", "bottom-right"
   - bubble_style: "speech", "thought", "shout", "whisper"

2. **panel_layout**: Korean webtoon panel description
   - Describe visual composition
   - Character positions and expressions
   - Dramatic lighting/shadows
   - Camera angle

3. **bubble_metadata**: Chat bubble overlay info
   - Links to audio_chunk
   - Position and style for each dialogue

**Director's Notes Examples:**
- Narration: "a mysterious narrator setting the scene in a noir film, deep and ominous"
- Dialogue: "a betrayed friend confronting someone, voice cracking with emotion"
- Internal: "internal monologue of regret, whispered and introspective"
- Shout: "an angry mother yelling at her child, voice trembling with fury"
- Whisper: "a secretive confession, barely audible, filled with shame"

**Character Guidelines:**
- Identify 2-5 main characters from the story
- Assign realistic genders based on context
- Give each character a distinct voice through director_notes
- Maintain character consistency across scenes

**Pacing:**
- Hook: 0.5-3s (immediate attention grab with dialogue)
- Build: 8-12s (character introduction, dialogue)
- Crisis: 10-15s (conflict escalation, rapid dialogue)
- Climax: 10-15s (peak drama, emotional dialogue)
- Resolution: 6-10s (conclusion, reflection)

**Example Scene (WEBTOON STYLE):**
```json
{
  "scene_id": "crisis_01",
  "audio_chunks": [
    {
      "chunk_id": "crisis_01_narrator_01",
      "chunk_type": "narration",
      "speaker_id": "Narrator",
      "speaker_gender": "female",
      "text": "The truth was about to come out.",
      "director_notes": "a suspenseful narrator building tension, hushed and mysterious",
      "estimated_duration": 2.5
    },
    {
      "chunk_id": "crisis_01_mother_01",
      "chunk_type": "dialogue",
      "speaker_id": "Mother",
      "speaker_gender": "female",
      "text": "How could you do this to me?!",
      "director_notes": "a betrayed mother confronting her child, voice trembling with hurt and anger",
      "estimated_duration": 2.0,
      "bubble_position": "top-right",
      "bubble_style": "shout"
    },
    {
      "chunk_id": "crisis_01_john_01",
      "chunk_type": "dialogue",
      "speaker_id": "John",
      "speaker_gender": "male",
      "text": "I had no choice...",
      "director_notes": "a guilty confession with defensive undertones, avoiding eye contact",
      "estimated_duration": 1.5,
      "bubble_position": "bottom-left",
      "bubble_style": "whisper"
    }
  ],
  "panel_layout": "Korean webtoon panel: Close-up on Mother's shocked face, tears forming, dramatic lighting from window. John in background, head down.",
  "bubble_metadata": [
    {
      "chunk_id": "crisis_01_mother_01",
      "text": "How could you do this to me?!",
      "position": "top-right",
      "style": "shout",
      "character_name": "Mother"
    },
    {
      "chunk_id": "crisis_01_john_01",
      "text": "I had no choice...",
      "position": "bottom-left",
      "style": "whisper",
      "character_name": "John"
    }
  ],
  "emotion": "dramatic",
  "visual_description": "Dramatic confrontation scene in dimly lit kitchen, Mother's face showing betrayal and hurt, John looking guilty and defensive",
  "characters_present": ["Mother", "John"],
  "estimated_duration_seconds": 6.0
}
```

**IMPORTANT:**
- Prioritize DIALOGUE over narration
- Create realistic conversations
- Use director_notes to add emotional depth
- Assign bubble positions to avoid overlap
- Maintain webtoon aesthetic (vibrant, expressive, dramatic)
"""

    USER_PROMPT_TEMPLATE = """Convert this Reddit story into a Korean Webtoon-style YouTube Short:

**Story Title:** {title}

**Story Content:**
{content}

**Story Category:** {category}

**Instructions:**
1. **Identify 2-5 main characters** from the story (give them names if not provided)
2. **Assign realistic genders** to each character based on context (male/female)
3. **Transform narration into CHARACTER DIALOGUE** whenever possible
   - Use conversations instead of descriptions
   - Create confrontations and emotional exchanges
   - Show, don't tell through dialogue
4. **Structure into exactly 5 acts** following the webtoon style
5. **For each scene, create audio_chunks:**
   - Start with narration chunk for scene-setting (if needed)
   - Add dialogue chunks for character conversations
   - Include internal monologue chunks for thoughts
   - Each chunk MAX 30 words
6. **Add detailed director_notes** for each chunk:
   - Describe the emotional delivery
   - Specify voice characteristics
   - Include context for TTS styling
   - Examples: "a betrayed friend confronting someone, voice cracking with emotion"
7. **Specify bubble positions** for dialogue to avoid overlap:
   - Use: top-left, top-right, center, bottom-left, bottom-right
   - Vary positions for visual interest
8. **Create panel_layout** descriptions in Korean webtoon style:
   - Describe character positions and expressions
   - Include dramatic lighting/shadows
   - Specify camera angles
9. **Generate bubble_metadata** for all dialogue chunks

**Output Format:**
Generate scenes with this structure:
- audio_chunks: List of AudioChunk objects (narration/dialogue/internal)
- panel_layout: Korean webtoon panel description
- bubble_metadata: List of BubbleMetadata objects matching dialogue
- visual_description: Vivid scene description for image generation
- characters_present: List of character names in this scene
- emotion: Overall scene emotion
- estimated_duration_seconds: Realistic duration

{format_instructions}

**Remember:** 
- Prioritize DIALOGUE over narration
- Make conversations feel natural and engaging
- Use director_notes to add emotional depth
- Create a visually dynamic webtoon experience!"""

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
            temperature=0.9,  # High temperature for creativity
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
            script.script_id = (
                f"script_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{story.id.split('_')[-1]}"
            )

        # Set story ID
        if not script.story_id or script.story_id == "string":
            script.story_id = story.id

        # Validate five acts in order
        self._validate_five_acts(script)

        # Validate durations
        self._validate_durations(script)

        # Validate character consistency
        self._validate_characters(script)

        # Check audio chunks (supports both webtoon and legacy)
        self._validate_audio_chunks(script)

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
        total_duration = sum(scene.estimated_duration_seconds for scene in script.get_all_scenes())

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

    def _validate_audio_chunks(self, script: Script) -> None:
        """Validate audio chunks in webtoon-style scenes or narration in legacy scenes.

        Args:
            script: Script to validate
        """
        for scene in script.get_all_scenes():
            # Check if webtoon-style
            if hasattr(scene, "is_webtoon_style") and scene.is_webtoon_style():
                if not scene.audio_chunks:
                    logger.warning(f"Webtoon scene {scene.scene_id} has no audio_chunks")
                    continue

                # Validate chunk text lengths
                for chunk in scene.audio_chunks:
                    word_count = len(chunk.text.split())
                    if word_count > 30:
                        logger.warning(
                            f"Chunk {chunk.chunk_id} text is long ({word_count} words, max 30)"
                        )

                    # Validate director_notes
                    if len(chunk.director_notes) < 10:
                        logger.warning(
                            f"Chunk {chunk.chunk_id} has short director_notes ({len(chunk.director_notes)} chars, min 10)"
                        )

                # Validate bubble_metadata matches dialogue chunks
                if hasattr(scene, "get_dialogue_chunks"):
                    dialogue_chunks = scene.get_dialogue_chunks()
                    if len(scene.bubble_metadata) != len(dialogue_chunks):
                        logger.warning(
                            f"Scene {scene.scene_id}: bubble_metadata count ({len(scene.bubble_metadata)}) "
                            f"doesn't match dialogue chunks ({len(dialogue_chunks)})"
                        )
            else:
                # Legacy validation
                if scene.narration:
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
        """Save human-readable version of script (supports webtoon style).

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

                    # Check if webtoon-style
                    if hasattr(scene, "is_webtoon_style") and scene.is_webtoon_style():
                        # Webtoon format
                        if scene.panel_layout:
                            f.write(f"PANEL LAYOUT:\n{scene.panel_layout}\n\n")

                        f.write(f"AUDIO CHUNKS ({len(scene.audio_chunks)}):\n")
                        for i, chunk in enumerate(scene.audio_chunks, 1):
                            f.write(
                                f"\n  [{i}] {chunk.chunk_type.value.upper()} - {chunk.speaker_id}"
                            )
                            if hasattr(chunk, "speaker_gender") and chunk.speaker_gender:
                                f.write(f" ({chunk.speaker_gender})")
                            f.write("\n")
                            f.write(f"      Text: {chunk.text}\n")
                            f.write(f"      Director: {chunk.director_notes}\n")
                            if hasattr(chunk, "bubble_position") and chunk.bubble_position:
                                f.write(
                                    f"      Bubble: {chunk.bubble_position} ({chunk.bubble_style})\n"
                                )

                        if scene.bubble_metadata:
                            f.write(f"\n  CHAT BUBBLES ({len(scene.bubble_metadata)}):\n")
                            for bubble in scene.bubble_metadata:
                                f.write(f'    - {bubble.character_name}: "{bubble.text}" ')
                                f.write(f"[{bubble.position}, {bubble.style}]\n")
                    else:
                        # Legacy format
                        if scene.narration:
                            f.write(f"NARRATION:\n{scene.narration}\n\n")

                    f.write(f"\nVISUAL:\n{scene.visual_description}\n\n")
                    f.write("-" * 40 + "\n\n")

        logger.info(f"Readable script saved to {output_path}")
