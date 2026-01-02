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
from gossiptoon.utils.llm_debugger import LLMDebugger
from gossiptoon.agents.script_evaluator import ScriptEvaluator

logger = logging.getLogger(__name__)


class ScriptWriterAgent:
    """Agent for converting stories into structured 5-act video scripts."""

    SYSTEM_PROMPT = """You are a master Korean Webtoon scriptwriter for YouTube Shorts.

**Task**: Write a raw, gossip-style, unfiltered 5-Act video script based on a Reddit story.

**Goal**: Maximize viewer retention through "imperfect" character dialogue, shock value, and emotional reactivity.

**Style**: 
- **Gossip Vibe**: Characters sound like real people (20s-30s) spilling tea to friends.
- **Imperfect Speech**: Use slang, fillers ("um", "like", "literally"), and natural interruptions.
- **Reaction > Exposition**: Characters shouldn't just narrate; they should *react* ("Can you believe this??").
- **Visuals**: Dynamic webtoon panels, close-ups, and dramatic framing.

**CRITICAL: Tone Guidelines (GOSSIP STYLE)**
- ❌ Professional/Clean: "I was very angry at him."
- ✅ Gossip/Raw: "I was literally shaking. Like, are you serious right now??"
- ❌ Exposition: "He came home late."
- ✅ Reaction: "And guess what? He strolls in at 3 AM. 3 FREAKING AM."
- **Use Fillers**: Natural speech has pauses. "Um...", "Wait...", "So..."

**CRITICAL: Multi-Character Dialogue**
- Transform narration into CHARACTER DIALOGUE whenever possible
- Use 2-5 characters per story
- Create conversations, confrontations, and emotional exchanges
- Narrator only for scene-setting or transitions

**CRITICAL: Character Design Standards**
You MUST define `character_profiles` for all 2-5 characters BEFORE writing acts.
For each character, include:
- Name (English only)
- Age (e.g., "20s") & Gender
- Role (Protagonist/Antagonist)
- Personality Vibe (e.g., "Gloomy", "Bubbly")
- Body Type (e.g., "Slim", "Muscular")
- Hair (e.g., "Long messy black hair")
- Face (e.g., "Sharp eyes with mole")
- Outfit (e.g., "Worn-out gray hoodie")

**Structure (Five Acts):**
1. **The Hook** (0-3s): IMMERSIVE FLASH-FORWARD. Start with the *most dramatic/shocking* moment of the story (dialogue or action). Do NOT start chronologically.
2. **Setup** (3-10s): Jump back in time. Introduce characters and context leading up to the hook.
3. **Escalation** (10-20s): Tension builds through conversation/confrontation.
4. **Climax** (20-35s): Peak emotional dialogue exchange (The return to the Hook moment).
5. **Resolution** (35-45s): Concisely reveal the outcome of the conflict, then pivot to a provocative engagement question.

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

2. **panel_layout**: Webtoon panel description (INSTANT READABILITY)
   - **CRITICAL**: We only have 3 seconds. Capture ONE specific key moment.
   - ❌ "They fight and he runs away" (Too complex, takes time to process)
   - ✅ "Close-up of his fist connecting with jaw, sweat flying" (Instant impact)
   - Focus on FACIAL EXPRESSIONS and DRAMATIC ANGLES (High/Low angle).
   - Use Close-ups (CU) or Extreme Close-ups (ECU) for maximum emotion on mobile screens.

3. **bubble_metadata**: Chat bubble overlay info
   - Links to audio_chunk
   - Position and style for each dialogue

4. **visual_sfx** (OPTIONAL): Sound effect keyword for dramatic moments
   - Use sparingly (only for HIGH-IMPACT scenes: climax, shock, revelation)
   - Choose from available SFX library:
     * TENSION: DOOM, DUN-DUN, LOOM, RUMBLE (shocking reveals, ominous moments)
     * ACTION: SQUEEZE, GRAB, GRIP, CLENCH, CRUSH (physical intensity)
     * IMPACT: BAM!, WHAM!, THUD, TA-DA! (sudden events, victory)
   - Examples:
     - Crisis scene with betrayal reveal: "DUN-DUN"
     - Climax scene with confrontation: "BAM!"
     - Resolution scene with happy ending: "TA-DA!"
     - Dark secret revealed: "DOOM"
   - **IMPORTANT**: Only 1-2 SFX per video (overuse kills impact)

5. **camera_effect** (OPTIONAL): Visual movement
   - Use to enhance scene emotion
   - Options:
     * static: No movement (dialogue, calm moments)
     * zoom_in: Slow push in (focus, revelation)
     * zoom_out: Slow pull out (context, isolation)
     * pan_left / pan_right: Exploration
     * shake: Standard drama shake
     * shake_slow: Subtle tension (unease)
     * shake_fast: Intense shock (impact) - MAX 1.5s

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

**Pacing (FAST MODE - Optimized for Shorts/TikTok):**
- Hook: 0.5-2s (immediate attention grab, instant impact)
- Setup: 2-4s (quick character intro, minimal narration)
- Crisis: 3-4s (conflict reveal, dramatic moment)
- Climax: 3-4s (peak drama, emotional punch)
- Resolution: 2-3s (quick wrap-up, cliffhanger or punchline)

**CRITICAL**: Total video should be 30-45s max. Keep scenes SHORT and PUNCHY.
**Target**: 3 seconds average per scene for maximum retention.

**Example Output Structure:**
```json
{
  "script_id": "example_script_001",
  "title": "The Secret in the Attic",
  "character_profiles": [
    {
      "name": "Mother",
      "age": "45",
      "gender": "Female",
      "role": "Protagonist",
      "personality_vibe": "Worried, Overprotective",
      "body_type": "Average",
      "hair_style_color": "Short curly brown hair",
      "face_details_expression": "Wrinkles of worry, warm eyes",
      "outfit": "Floral apron over house clothes"
    },
    {
      "name": "John",
      "age": "20s",
      "gender": "Male",
      "role": "Antagonist",
      "personality_vibe": "Guilty, Nervous",
      "body_type": "Slim",
      "hair_style_color": "Messy black hair",
      "face_details_expression": "Pale skin, dark circles",
      "outfit": "Black hoodie and jeans"
    }
  ],
  "acts": [
    {
      "act_type": "hook",
      "scenes": [...]
    },
    {
      "act_type": "crisis",
      "scenes": [
        {
          "scene_id": "crisis_01",
          "audio_chunks": [...],
          "visual_description": "Extreme Close-up (ECU) of Mother...",
          "panel_layout": "...",
          "camera_effect": "shake_slow"
        }
      ]
    }
  ]
}
```

**Engagement Ending:**
The video MUST end with a question or controversial statement to provoke comments.
- "Was I wrong?"
- "What would you have done?"
- "Team Mom or Team Dad?"
**CRITICAL**: Never end with a generic conclusion. Force the viewer to engage.

**IMPORTANT:**
- Use NARRATION to lead the story (60-70%)
- Add DIALOGUE for key emotional moments (30-40%)
- Narrator is the main character (first-person POV, Reddit style)
- Use director_notes to add emotional depth
- Assign bubble positions to avoid overlap
- Maintain webtoon aesthetic (vibrant, expressive, dramatic)
- **TONE**: Polarizing. Highlight conflict. Create "Us vs Them" dynamics.
"""

    USER_PROMPT_TEMPLATE = """Convert this Reddit story into a Webtoon-style YouTube Short:

**Story Title:** {title}

**Story Content:**
{content}

**Story Category:** {category}

**Instructions:**
1. **Identify 2-5 main characters
   - Give them English names if not provided in the story
2. **Assign realistic genders** to each character based on context (male/female)
3. **Use NARRATION to lead the story (60-70%)**
   - Main character narrates in first-person (like original Reddit post)
   - Narrator guides the story progression
   - Add DIALOGUE for key emotional moments (30-40%)
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
8. **Create panel_layout** descriptions in webtoon style:
   - Describe character positions and expressions
   - Include dramatic lighting/shadows
   - Specify camera angles
9. **Generate bubble_metadata** for all dialogue chunks

**Output Format:**
Generate scenes with this structure:
- audio_chunks: List of AudioChunk objects (narration/dialogue/internal)
- panel_layout: Webtoon panel description
- bubble_metadata: List of BubbleMetadata objects matching dialogue
- visual_description: Vivid scene description for image generation
- characters_present: List of character names in this scene
- emotion: Overall scene emotion
- estimated_duration_seconds: Realistic duration

{format_instructions}

**Remember:** 
- NARRATION leads the story (60-70%), dialogue highlights emotions (30-40%)
- Main character narrates like the original Reddit post
- Use director_notes to add emotional depth
- Create a visually dynamic webtoon experience!"""

    LEGACY_SYSTEM_PROMPT = """You are an expert scriptwriter for YouTube Shorts.

**Task**: Write a compelling 5-Act video script based on a Reddit story.

**Style**: Narrated story with minimal dialogue, focus on pacing and visual description.

**Structure (Five Acts):**
1. **The Hook** (0-3s)
2. **Setup** (3-10s)
3. **Escalation** (10-20s)
4. **Climax** (20-35s)
5. **Resolution** (35-45s)

**Scene Structure:**
Each scene must have:
- narration: The voiceover text (MAX 50 words)
- visual_description: Detailed description for image generation (photorealistic style)
- emotion: Scene emotion
- estimated_duration_seconds: Duration

**Example Scene:**
```json
{
  "scene_id": "scene_01",
  "narration": "It was a dark and stormy night...",
  "visual_description": "Dark storm clouds gathering over a spooky house",
  "emotion": "suspenseful",
  "estimated_duration_seconds": 3.5
}
```

**IMPORTANT:**
- Focus on clear, engaging narration.
- Keep sentences short and punchy.
"""

    LEGACY_USER_PROMPT_TEMPLATE = """Convert this Reddit story into a YouTube Short script:

**Story Title:** {title}

**Content:**
{content}

**Category:** {category}

**Instructions:**
1. Break down the story into 5 structured acts.
2. Write concise narration for each scene.
3. Provide vivid visual descriptions.
4. Keep total duration under 60 seconds.

**Output Format:**
Generate scenes with:
- narration
- visual_description
- emotion
- estimated_duration_seconds

{format_instructions}
"""

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

        # Validate API Key
        if not config.api.google_api_key or config.api.google_api_key == "INVALID":
            logger.error("Google API Key is missing or invalid")
            raise ValueError("Google API Key is missing or invalid. Check .env file.")

        # Use LangChain's ChatGoogleGenerativeAI (Unstructured for creativity)
        # Revert to Gemini 2.0 Flash Exp as per WEBTOON_ENGINE.md
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            temperature=0.9,  # High temperature for creativity
            google_api_key=config.api.google_api_key,
            safety_settings=safety_settings,
        )
        self.prompt = self._create_prompt()
        self.evaluator = ScriptEvaluator(config)

        # Initialize Debugger
        # Assumes scripts_dir is outputs/{job_id}/scripts, so parent is outputs/{job_id}
        self.debugger = LLMDebugger(self.config.scripts_dir.parent)

        # Log masked API key for verification
        key = config.api.google_api_key
        masked_key = f"{key[:4]}...{key[-4:]}" if key and len(key) > 8 else "INVALID"
        logger.info(f"Initialized ScriptWriter with model=gemini-2.0-flash-exp, key={masked_key}")

    def _create_prompt(self) -> ChatPromptTemplate:
        """Create prompt template with specific constraints.

        Returns:
            Chat prompt template
        """
        # Inject config values into system prompt
        if self.config.script.webtoon_mode:
            system_prompt = self.SYSTEM_PROMPT.replace(
                "MAX 30 words", f"MAX {self.config.script.max_dialogue_chars} characters"
            )
            # Escape braces for LangChain formatting (JSON examples)
            system_prompt = system_prompt.replace("{", "{{").replace("}", "}}")
            user_prompt = self.USER_PROMPT_TEMPLATE
        else:
            system_prompt = self.LEGACY_SYSTEM_PROMPT.replace("{", "{{").replace("}", "}}")
            user_prompt = self.LEGACY_USER_PROMPT_TEMPLATE

        # Simplify Prompt - No strict enums
        return ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", user_prompt),
            ]
        )

    def _create_scaffold_system_prompt(self) -> str:
        """Create system prompt for scaffold-filling mode.

        Returns:
            System prompt for filling scaffolds with creative content
        """
        return """You are a Creative Content Writer for Korean Webtoon YouTube Shorts.

**CRITICAL: Tone = GOSSIP / DRAMA / TEA-SPILLING**
- Make it sound RAW and UNFILTERED.
- Use slang, fillers ("like", "literally", "omg"), and rhetorical questions.
- Focus on EMOTIONAL IMPACT over grammatical correctness.

**Your Task**: Fill an existing script scaffold with dialogue, visuals, and creative elements.

**What You Receive:**
- Original Reddit story (for context)
- Complete script scaffold with:
  * Character profiles (already created)
  * 5-act structure (already built)
  * Scene IDs, order, durations (already set)
  * Empty audio_chunks, visual_description, panel_layout

**What You Must Generate:**

1. **Audio Chunks** (for each scene):
   - Create 1-3 audio chunks per scene
   - Types: "narration", "dialogue", or "internal"
   - Use character names from provided profiles
   - Include "speaker_gender": "male" or "female"
   - MAX 100 characters per chunk
   - Add director_notes (MIN 10 chars) for TTS styling
   - For dialogue: add bubble_position and bubble_style

2. **Visual Description**:
   - Vivid, detailed description for image generation
   - Include character poses, expressions, environment
   - Photorealistic or webtoon style (as appropriate)
   - MIN 30 characters

3. **Panel Layout** (Webtoon style):
   - **Template Selection**: 
     - "single_image": Standard establishing shot
     - "template_a_3panel": 3 vertical panels (Action scquences, rapid pacing)
     - "template_b_4panel": 4 vertical panels (Dialogue-heavy, reaction shots)
   - **Panel Descriptions**:
     - If using single_image: Provide 1 vivid description
     - If using 3-panel: Provide array of 3 descriptions [top, middle, bottom]
     - If using 4-panel: Provide array of 4 descriptions [top, middle-1, middle-2, bottom]
   - Focus on facial expressions and angles for each panel

4. **Bubble Metadata**:
   - One entry per dialogue audio chunk
   - Match character_name, text, position, style

5. **Camera Effect** (optional):
   - Choose from: static, zoom_in, zoom_out, pan_left, pan_right, shake, shake_slow, shake_fast
   - Use null for most scenes

6. **Visual SFX** (optional, max 2 total):
   - HIGH-IMPACT scenes only
   - Options: DOOM, DUN-DUN, LOOM, RUMBLE, SQUEEZE, GRAB, BAM!, BOOM!, WHAM!, THUD, TA-DA!

**CRITICAL RULES:**
1. DO NOT change any structural fields (scene_id, order, estimated_duration_seconds)
2. DO NOT modify character_profiles
3. DO NOT change act structure or target_duration_seconds
4. DO NOT add/remove scenes
5. ONLY fill creative content fields

**NARRATIVE RESTRUCTURING (Hook-First):**
- **Act 1 (Hook)**: MUST contain the MOST shocking/dramatic moment from the story. Use a "Flash Forward" technique. Do NOT start with "I was born..." or background info. Start with the scream, the slap, or the discovery.
- **Act 2 (Setup)**: Rewind. "Two days earlier..." or "It started when...". Build context.
- **Act 5 (Resolution/Ending)**: MUST end with an ENGAGEMENT TRIGGER. Ask the audience a question. "Am I the jerk?", "Who was right?". Open-ended and controversial.

**Style Guidelines:**
- **Tone**: Polarizing & Dramatic. Emphasize conflict. Make the viewer choose a side.
- Use NARRATION to lead (60-70%)
- Add DIALOGUE for emotional moments (30-40%)
- Main character narrates in first-person (Reddit style)
- Create vibrant, expressive webtoon panels
- Maintain character consistency

**Output:**
Return the COMPLETE Script object with all creative fields filled.
DO NOT return just the creative content - return the full Script with structure intact.
"""

    async def fill_scaffold(self, story: Story, scaffold: Script) -> Script:
        """Fill script scaffold with creative content.

        This is the NEW workflow: receives structure from SceneStructurer,
        fills in dialogue, visuals, and creative elements.

        Args:
            story: Original story for context
            scaffold: Script structure from SceneStructurer

        Returns:
            Complete script with creative content

        Raises:
            ScriptGenerationError: If content generation fails
        """
        logger.info(f"Filling scaffold for story: {story.id}")
        logger.info(
            f"Scaffold has {scaffold.get_scene_count()} scenes, "
            f"{len(scaffold.character_profiles)} characters"
        )

        try:
            # Create scaffold-filling prompt
            scaffold_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", self._create_scaffold_system_prompt()),
                    (
                        "human",
                        """Fill this script scaffold with creative content:

**Original Story:**
Title: {title}
Content: {content}
Category: {category}

**Script Scaffold (JSON):**
{scaffold_json}

**Your Task:**
1. For EACH scene in the scaffold, fill in:
   - audio_chunks: Create dialogue/narration (use provided character profiles)
   - visual_description: Vivid description for image generation (overall vibe)
   - panel_template: Select "single_image", "template_a_3panel", or "template_b_4panel"
   - panel_descriptions: List of strings (count MUST match template: 1, 3, or 4)
   - bubble_metadata: Match dialogue chunks
   - camera_effect: Choose appropriate effect (or null)
   - visual_sfx: Add if scene is high-impact (max 2 total)

2. KEEP ALL STRUCTURAL FIELDS UNCHANGED:
   - scene_id, order, estimated_duration_seconds
   - characters_present, emotion
   - character_profiles, acts structure

3. Follow webtoon style guidelines
4. Maintain character consistency
5. Keep audio chunks under {max_chars} characters

Generate the COMPLETE script with all creative content filled in.
""",
                    ),
                ]
            )

            # Format scaffold as JSON
            import json

            scaffold_json = json.dumps(scaffold.model_dump(mode="json"), indent=2)

            # Build messages
            messages = scaffold_prompt.format_messages(
                title=story.title,
                content=story.content,
                category=story.category.value,
                scaffold_json=scaffold_json,
                max_chars=self.config.script.max_dialogue_chars,
            )

            # Generate creative content
            logger.info("Generating creative content to fill scaffold...")
            start_time = datetime.now()

            filled_script = await self.llm.with_structured_output(Script).ainvoke(messages)

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            # Log interaction
            try:
                self.debugger.log_interaction(
                    agent_name="ScriptWriter_FillScaffold",
                    prompt=messages,
                    response=filled_script,
                    metadata={
                        "story_id": story.id,
                        "mode": "scaffold_fill",
                        "scene_count": scaffold.get_scene_count(),
                    },
                    duration_ms=duration_ms,
                )
            except Exception as log_e:
                logger.warning(f"Failed to log interaction: {log_e}")

            logger.info(f"Filled scaffold with creative content")

            return filled_script

        except Exception as e:
            logger.error(f"Scaffold filling failed: {e}")
            raise ScriptGenerationError(f"Failed to fill scaffold: {e}") from e

    @retry_with_backoff(max_retries=3, exceptions=(ScriptGenerationError,))
    async def write_script(self, story: Story) -> Script:
        """Generate structured script from story (LEGACY METHOD).

        This is the OLD 2-agent workflow. Kept for backward compatibility.
        New workflow should use SceneStructurer.generate_scaffold() then fill_scaffold().

        Args:
            story: Story to convert

        Returns:
            Generated script

        Raises:
            ScriptGenerationError: If script generation fails
        """
        logger.info(f"Generating script for story: {story.id} (LEGACY 2-AGENT WORKFLOW)")

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
            start_time = datetime.now()

            try:
                response = await self.llm.ainvoke(messages)
            except Exception as inner_e:
                logger.error(f"LLM Invoke Failed: {inner_e}")
                raise inner_e

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            # Log interaction
            try:
                self.debugger.log_interaction(
                    agent_name="ScriptWriter",
                    prompt=messages,
                    response=response,
                    metadata={
                        "story_id": story.id,
                        "mode": "webtoon" if self.config.script.webtoon_mode else "legacy",
                    },
                    duration_ms=duration_ms,
                )
            except Exception as log_e:
                logger.warning(f"Failed to log interaction: {log_e}")

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
                    # Check character length based on config
                    char_count = len(chunk.text)
                    max_chars = self.config.script.max_dialogue_chars

                    if char_count > max_chars:
                        logger.warning(
                            f"Chunk {chunk.chunk_id} text is long ({char_count} chars, max {max_chars})"
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
                    max_legacy = self.config.script.max_narration_chars // 5  # Approx words
                    if word_count > max_legacy:
                        logger.warning(
                            f"Scene {scene.scene_id} narration is long ({word_count} words, max {max_legacy})"
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
