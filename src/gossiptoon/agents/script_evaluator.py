import logging
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import (
    PydanticOutputParser as LangChainPydanticOutputParser,
)  # Avoid conflict if any

from gossiptoon.core.config import ConfigManager
from gossiptoon.models.story import Story
from gossiptoon.models.script import Script, Scene, Act, ActType, EmotionTone, CameraEffectType
from gossiptoon.utils.llm_debugger import LLMDebugger
from datetime import datetime

logger = logging.getLogger(__name__)


class ScriptEvaluator:
    """Agent responsible for validating, formatting, and polishing the script."""

    SYSTEM_PROMPT = """
You are the Chief Editor and Technical Director for a Korean Webtoon YouTube Shorts production studio.
Your job is to take a DRAFT SCRIPT and format it into a strict JSON structure for video production.

**Script Formats Supported:**

1. **WEBTOON STYLE (Preferred):**
   - Scenes have `audio_chunks` instead of `narration`
   - Each AudioChunk has: chunk_id, chunk_type, speaker_id, speaker_gender, text, director_notes
   - Dialogue chunks have: bubble_position, bubble_style
   - Scenes have: panel_layout, bubble_metadata
   - Multi-character dialogue with distinct voices

2. **LEGACY STYLE (Backward Compatible):**
   - Scenes have `narration` field
   - Single narrator voice
   - No audio_chunks

**Responsibilities:**

1. **Format Validation**: Ensure output matches the `Script` schema exactly.

2. **Webtoon-Style Validation:**
   - If draft has audio_chunks, validate each chunk:
     * chunk_id: Must be unique (format: "scene_id_speaker_##")
     * chunk_type: Must be "narration", "dialogue", or "internal"
     * speaker_id: Character name or "Narrator"
     * speaker_gender: Must be "male" or "female"
     * text: MAX 30 words
     * director_notes: MIN 10 characters, describe emotional delivery
   - Dialogue chunks MUST have:
     * bubble_position: "top-left", "top-right", "center", "bottom-left", "bottom-right"
     * bubble_style: "speech", "thought", "shout", "whisper"
   - bubble_metadata must match dialogue chunks
   - panel_layout must capture ONE KEY MOMENT for instant 3s readability
   - REJECT complex multi-action descriptions ("He walks in, sits down, and cries")
   - ACCEPT snapshot moments ("Close-up of him wiping a tear")
   - Focus on facial expressions and dramatic angles
   - Keep descriptions under 30 words

3. **Enum Correction**: Map descriptions to strict Enums:
   * **ALLOWED EMOTIONS**: {valid_emotions}
   * **ALLOWED CAMERA EFFECTS**: {valid_effects}
   * **CRITICAL**: Map close values (e.g., "mad" -> `angry`, "zoom" -> `zoom_in`)

4. **Timing & Pacing (FAST MODE - Optimized for Shorts):**
   - Total duration: 30-45s (STRICT - reject if exceeds 50s)
   - **Per-scene duration limits**:
     * MIN: 2.0s (scenes shorter than this feel rushed)
     * MAX: 4.0s (scenes longer than this hurt retention)
     * TARGET: 3.0s average
   - Adjust `estimated_duration_seconds` based on audio_chunks
   - Approx 2.5-3.0 words/sec for TTS
   - **ENFORCE**: Reduce scene duration if audio chunks are too long

5. **Structure Enforcement:**
   - Exactly 5 Acts: Hook, Setup, Crisis, Climax, Resolution
   - **Updated Act Durations**:
     * Hook: 0.5-2s (instant grab)
     * Setup: 2-4s (quick intro)
     * Crisis: 3-4s (conflict)
     * Climax: 3-4s (peak)
     * Resolution: 2-3s (wrap-up)

6. **Character Consistency & Profiles:**
   - **CRITICAL**: Verify `character_profiles` list is populated with detailed visual data.
   - All main speakers (except Narrator) MUST have a corresponding profile.
   - Maintain consistent speaker_id across scenes.
   - Ensure speaker_gender is consistent for each character.
   - Validate characters_present matches audio_chunks speakers.

7. **Text Normalization for TTS Compatibility:**
   - Remove stage directions and parentheticals from dialogue text
   - Examples: "(Text message tone)", "(Whispering)", "(Cries)", etc.
   - These should only appear in director_notes, NOT in the spoken text
   - Normalize all numbers and abbreviations for text-to-speech
   - Convert: $28M → $28 million, $1M → $1 million
   - Convert: 5K → 5 thousand, 2B → 2 billion
   - Spell out abbreviations that TTS can't handle
   - Ensure all text in audio_chunks is clean and TTS-friendly

8. **Sound Effects (visual_sfx) Validation:**
   - OPTIONAL field - only for HIGH-IMPACT scenes (1-2 per video max)
   - If present, must be valid SFX keyword:
     * TENSION: DOOM, DUN-DUN, LOOM, RUMBLE
     * ACTION: SQUEEZE, GRAB, GRIP, CLENCH, CRUSH
     * IMPACT: BAM!, WHAM!, THUD, TA-DA!
   - Use sparingly: climax, revelation, dramatic turning points only
   - Remove if overused (more than 2 SFX in entire video)

9. **Camera Effect Validation:**
   - Valid options: static, zoom_in, zoom_out, pan_left, pan_right, shake, shake_slow, shake_fast
   - **SHAKE CONSTRAINT**: If effect is 'shake' or 'shake_fast', duration MUST be <= 2.0s
   - If a scene has 'shake_fast' and duration > 2.0s -> Change to 'shake_slow' or reduce duration

**Input:**
* Original Reddit Story (for context)
* Draft Script (text or rough JSON)

**Output:**
* A fully valid `Script` JSON object (webtoon or legacy style)

**IMPORTANT:**
- Prioritize webtoon-style if draft has dialogue/characters
- Fall back to legacy style if draft is narration-only
- Ensure all required fields are present and valid
"""

    def __init__(self, config: ConfigManager):
        self.config = config
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=self.config.api.google_api_key,
            temperature=0.2,  # Low temperature for strict validation
            convert_system_message_to_human=True,
        )
        self.structured_llm = self.llm.with_structured_output(Script)
        
        # Initialize Debugger
        # Assumes scripts_dir is outputs/{job_id}/scripts
        self.debugger = LLMDebugger(self.config.scripts_dir.parent)

    async def evaluate_and_fix(self, draft_content: str, story: Story) -> Script:
        """Process the draft script into a valid Script object."""
        logger.info("Evaluating and formatting draft script...")

        # Prepare dynamic enum lists
        valid_emotions = ", ".join([e.value for e in EmotionTone])
        valid_effects = ", ".join([e.value for e in CameraEffectType])

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.SYSTEM_PROMPT),
                ("user", "ORIGINAL STORY:\n{story_title}\n{story_body}\n\nDRAFT SCRIPT:\n{draft}"),
            ]
        )

        chain = prompt | self.structured_llm

        try:
            # 1. Format Prompt
            input_data = {
                "story_title": story.title,
                "story_body": story.content,
                "draft": draft_content,
                "valid_emotions": valid_emotions,
                "valid_effects": valid_effects,
            }
            formatted_prompt = await prompt.ainvoke(input_data)

            # 2. Call LLM with Debugging
            start_time = datetime.now()
            script = None
            error = None
            
            try:
                script = await self.structured_llm.ainvoke(formatted_prompt)
            except Exception as e:
                error = str(e)
                raise e
            finally:
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                
                # 3. Log Interaction
                self.debugger.log_interaction(
                    agent_name="ScriptEvaluator",
                    prompt=formatted_prompt,
                    response=script if script else {"error": error},
                    metadata={"story_id": story.id},
                    duration_ms=duration_ms
                )

            logger.info(
                f"Script evaluated: {len(script.acts)} acts, {script.get_scene_count()} scenes."
            )
            return script
        except Exception as e:
            logger.error(f"Script evaluation failed: {e}")
            raise e
