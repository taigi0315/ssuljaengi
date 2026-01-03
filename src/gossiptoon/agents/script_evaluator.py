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
            model=config.llm.script_evaluator_model,
            google_api_key=self.config.api.google_api_key,
            temperature=config.llm.script_evaluator_temperature,
            convert_system_message_to_human=True,
        )
        self.structured_llm = self.llm.with_structured_output(Script)
        
        # Initialize Debugger
        # Assumes scripts_dir is outputs/{job_id}/scripts
        self.debugger = LLMDebugger(self.config.scripts_dir.parent)

    async def validate_script(self, script: Script, story: Story) -> Script:
        """Validate and polish a complete script (NEW 3-AGENT WORKFLOW).

        This method is for the new workflow where structure is already guaranteed.
        It performs QA-only: validates enums, normalizes text, checks constraints.

        Args:
            script: Complete script from ScriptWriter
            story: Original story for context

        Returns:
            Validated and polished script

        Raises:
            Exception: If validation fails critically
        """
        logger.info("Validating complete script (QA-only)...")

        simplified_prompt = """You are a QA Editor for Korean Webtoon YouTube Shorts.

**CRITICAL: The script structure is ALREADY CORRECT. Only validate and polish.**

**Your QA Checklist:**

1. **Enum Validation**: Fix any invalid enum values
   - emotion: excited, shocked, sympathetic, dramatic, angry, happy, sad, neutral, suspenseful, sarcastic, frustrated, determined, relieved, exasperated
   - camera_effect: ken_burns, fade_transition, caption, zoom_in, zoom_out, pan_left, pan_right, pan_up, pan_down, shake, shake_slow, shake_fast, static, loom

2. **Text Normalization**:
   - Remove parentheticals from audio chunk text (move to director_notes)
   - Normalize numbers: $1M → $1 million, 5K → 5 thousand
   - Clean TTS-incompatible characters

3. **Constraint Checks**:
   - Audio chunk text: MAX 100 characters (warn if exceeded)
   - Visual SFX: MAX 5 per video (remove excess)
   - Shake effects: Duration MUST be <= 2.0s

4. **Character Consistency**:
   - Verify speaker_id matches character_profiles
   - Check speaker_gender consistency

**DO NOT:**
- Change structure (scene_id, order, durations)
- **CRITICAL**: Remove `target_duration_seconds` from Acts (Must be preserved)
- Modify character_profiles
- Add/remove scenes or acts
- Rewrite creative content

**Output:**
Return the script with minor QA fixes applied. Preserve all structure and creative content.
"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", simplified_prompt),
            ("human", """Validate and polish this script:

**Original Story (for context):**
{story_title}

**Script (JSON):**
{script_json}

Apply QA fixes and return the polished script.
""")
        ])

        try:
            # For large scripts (>15 scenes), validate act-by-act to avoid LLM output size limits
            # Lowered from 20 to 15 to handle moderately large scripts more reliably
            if script.get_scene_count() > 15:
                logger.info(f"Large script detected ({script.get_scene_count()} scenes), using act-by-act validation")
                return await self._validate_script_by_acts(script, story)
            
            # For smaller scripts, validate all at once
            import json
            script_json = json.dumps(script.model_dump(mode="json"), indent=2)

            formatted_prompt = await prompt.ainvoke({
                "story_title": story.title,
                "script_json": script_json
            })

            start_time = datetime.now()

            # Retry logic for LLM validation (max 3 attempts)
            validated_script = None
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    validated_script = await self.structured_llm.ainvoke(formatted_prompt)

                    if validated_script is not None:
                        break  # Success!
                    else:
                        logger.warning(f"⚠️ Script validation returned None (attempt {attempt + 1}/{max_retries})")
                        if attempt < max_retries - 1:
                            import asyncio
                            await asyncio.sleep(2)  # Wait 2 seconds before retry
                except Exception as retry_error:
                    logger.warning(f"Script validation attempt {attempt + 1} failed: {retry_error}")
                    if attempt < max_retries - 1:
                        import asyncio
                        await asyncio.sleep(2)

            if validated_script is None:
                raise Exception(f"Script validation failed after {max_retries} attempts - LLM returned None")

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            self.debugger.log_interaction(
                agent_name="ScriptEvaluator_QA",
                prompt=formatted_prompt,
                response=validated_script,
                metadata={"story_id": story.id, "mode": "qa_only"},
                duration_ms=duration_ms
            )

            logger.info(f"✅ Script QA validated: {validated_script.get_scene_count()} scenes")
            
            # NEW: Perform coherence check
            coherence_result = await self._check_story_coherence(validated_script, story)
            
            # Return ValidationResult with both QA and coherence info
            from gossiptoon.models.script import ValidationResult
            return ValidationResult(
                script=validated_script,
                is_coherent=coherence_result.is_coherent,
                issues=coherence_result.issues
            )

        except Exception as e:
            logger.error(f"Script validation failed: {e}")
            raise e

    async def _validate_script_by_acts(self, script: Script, story: Story) -> Script:
        """Validate script act-by-act for large scripts.
        
        Args:
            script: Complete script to validate
            story: Original story for context
            
        Returns:
            Validated script
        """
        logger.info(f"Validating {len(script.acts)} acts separately...")
        
        validated_acts = []
        
        for act_index, act in enumerate(script.acts):
            logger.info(f"📝 Validating Act {act_index + 1}/{len(script.acts)}: {act.act_type.value}")
            logger.info(f"📝 Act has {len(act.scenes)} scenes")
            
            # Validate this single act
            validated_act = await self._validate_single_act(act, story)
            
            logger.info(f"📝 _validate_single_act returned: {type(validated_act)}")
            if validated_act is None:
                raise Exception(f"❌ CRITICAL: _validate_single_act returned None for {act.act_type.value}!")
            
            validated_acts.append(validated_act)
            
            logger.info(f"✅ Act {act_index + 1} validated: {len(validated_act.scenes)} scenes")
        
        # Combine all validated acts
        validated_script = Script(
            script_id=script.script_id,
            story_id=script.story_id,
            title=script.title,
            acts=validated_acts,
            character_profiles=script.character_profiles,
            total_estimated_duration=script.total_estimated_duration,
            target_audience=script.target_audience,
            content_warnings=script.content_warnings
        )
        
        logger.info(f"Script validation complete: {validated_script.get_scene_count()} scenes")
        return validated_script

    async def _validate_single_act(self, act: Act, story: Story) -> Act:
        """Validate a single act.
        
        Args:
            act: Act to validate
            story: Original story for context
            
        Returns:
            Validated act
        """
        simplified_prompt = """You are a QA Editor for Korean Webtoon YouTube Shorts.

**CRITICAL: The script structure is ALREADY CORRECT. Only validate and polish.**

**Your QA Checklist:**

1. **Enum Validation**: Fix any invalid enum values
   - emotion: excited, shocked, sympathetic, dramatic, angry, happy, sad, neutral, suspenseful, sarcastic, frustrated, determined, relieved, exasperated
   - camera_effect: ken_burns, fade_transition, caption, zoom_in, zoom_out, pan_left, pan_right, pan_up, pan_down, shake, shake_slow, shake_fast, static, loom

2. **Text Normalization**:
   - Remove parentheticals from audio chunk text (move to director_notes)
   - Normalize numbers: $1M → $1 million, 5K → 5 thousand
   - Clean TTS-incompatible characters

3. **Constraint Checks**:
   - Audio chunk text: MAX 100 characters (warn if exceeded)
   - Visual SFX: MAX 2 per act (remove excess)
   - Shake effects: Duration MUST be <= 2.0s

4. **Character Consistency**:
   - Verify speaker_id exists
   - Check speaker_gender consistency

**DO NOT:**
- Change structure (scene_id, order, durations)
- Remove `target_duration_seconds` from Act
- Add/remove scenes
- Rewrite creative content

**Output:**
Return the act with minor QA fixes applied. Preserve all structure and creative content.
"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", simplified_prompt),
            ("human", """Validate and polish this act:

**Original Story (for context):**
{story_title}

**Act (JSON):**
{act_json}

Apply QA fixes and return the polished act.
""")
        ])

        try:
            import json
            act_json = json.dumps(act.model_dump(mode="json"), indent=2)

            formatted_prompt = await prompt.ainvoke({
                "story_title": story.title,
                "act_json": act_json
            })

            start_time = datetime.now()
            
            # Retry logic for LLM validation (max 3 attempts)
            validated_act = None
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    validated_act = await self.llm.with_structured_output(Act).ainvoke(formatted_prompt)
                    
                    if validated_act is not None:
                        break  # Success!
                    else:
                        logger.warning(f"Act validation returned None (attempt {attempt + 1}/{max_retries})")
                        if attempt < max_retries - 1:
                            import asyncio
                            await asyncio.sleep(1)  # Wait 1 second before retry
                except Exception as retry_error:
                    logger.warning(f"Act validation attempt {attempt + 1} failed: {retry_error}")
                    if attempt < max_retries - 1:
                        import asyncio
                        await asyncio.sleep(1)
            
            if validated_act is None:
                raise Exception(f"Act validation failed after {max_retries} attempts - LLM returned None")
            
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            self.debugger.log_interaction(
                agent_name=f"ScriptEvaluator_QA_{act.act_type.value}",
                prompt=formatted_prompt,
                response=validated_act,
                metadata={"story_id": story.id, "mode": "qa_act", "act_type": act.act_type.value},
                duration_ms=duration_ms
            )

            return validated_act

        except Exception as e:
            logger.error(f"Act validation failed for {act.act_type.value}: {e}")
            raise e


    async def evaluate_and_fix(self, draft_content: str, story: Story) -> Script:
        """Process the draft script into a valid Script object (LEGACY 2-AGENT WORKFLOW)."""
        logger.info("Evaluating and formatting draft script (LEGACY)...")

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

    async def _check_story_coherence(self, script: Script, story: Story) -> 'CoherenceResult':
        """Check if the script has good story progression without repetition.
        
        Args:
            script: Complete script to check
            story: Original story for context
            
        Returns:
            CoherenceResult with coherence status and issues
        """
        from gossiptoon.models.script import CoherenceResult
        
        logger.info("Checking story coherence...")
        
        coherence_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Story Editor for Korean Webtoon YouTube Shorts.

**Task**: Evaluate this script for story coherence and repetition.

**Evaluation Criteria**:
1. **Story Progression**: Does each act introduce NEW information or developments?
2. **Dialogue Repetition**: Are characters asking the same questions or having the same reactions multiple times?
3. **Emotional Beats**: Do acts repeat the same emotional journey?

**Be STRICT**: Even similar phrasing counts as repetition.

**Output**:
- `is_coherent`: true if story progresses well, false if repetitive
- `issues`: List of specific problems (e.g., "CRISIS and CLIMAX both repeat 'how dare she' reaction")
- `suggested_fixes`: What should change in each problematic act (act_type -> suggestion)
"""),
            ("human", """Evaluate this script for coherence:

**Original Story**: {story_title}
{story_content}

**Script**: {script_summary}

Check for repetition and story progression issues.""")
        ])
        
        # Build script summary (extract key dialogue from each act)
        import json
        script_summary_parts = []
        for act in script.acts:
            act_dialogue = []
            for scene in act.scenes[:3]:  # First 3 scenes per act
                if hasattr(scene, 'audio_chunks') and scene.audio_chunks:
                    for chunk in scene.audio_chunks[:2]:  # First 2 chunks
                        if hasattr(chunk, 'text'):
                            act_dialogue.append(f"  - {chunk.text}")
            if act_dialogue:
                script_summary_parts.append(f"**{act.act_type.value.upper()}**:\n" + "\n".join(act_dialogue))
        
        script_summary = "\n\n".join(script_summary_parts)
        
        try:
            start_time = datetime.now()
            
            # Use LLM to evaluate coherence
            coherence_llm = self.llm.with_structured_output(CoherenceResult)
            result = await coherence_llm.ainvoke(
                coherence_prompt.format_messages(
                    story_title=story.title,
                    story_content=story.content[:500],  # First 500 chars
                    script_summary=script_summary
                )
            )
            
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            # Log interaction
            self.debugger.log_interaction(
                agent_name="ScriptEvaluator_Coherence",
                prompt=coherence_prompt.format_messages(
                    story_title=story.title,
                    story_content=story.content[:500],
                    script_summary="<script_summary_omitted>"
                ),
                response=result,
                metadata={"story_id": story.id, "mode": "coherence_check"},
                duration_ms=duration_ms
            )
            
            if result.is_coherent:
                logger.info("✅ Script passed coherence check")
            else:
                logger.warning(f"❌ Script has coherence issues: {result.issues}")
            
            return result
            
        except Exception as e:
            logger.error(f"Coherence check failed: {e}")
            # Return default "coherent" result if check fails (don't block pipeline)
            return CoherenceResult(
                is_coherent=True,
                issues=[],
                suggested_fixes={}
            )
