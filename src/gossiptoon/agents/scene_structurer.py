"""Scene Structurer Agent - Generates script scaffolds with perfect structure."""

import logging
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory
from langchain_core.prompts import ChatPromptTemplate

from gossiptoon.core.config import ConfigManager
from gossiptoon.core.exceptions import ScriptGenerationError
from gossiptoon.models.script import Script
from gossiptoon.models.story import Story
from gossiptoon.utils.llm_debugger import LLMDebugger

logger = logging.getLogger(__name__)


class SceneStructurerAgent:
    """Agent for generating script structure scaffolds.

    This agent is responsible ONLY for creating the structural skeleton of a script.
    It does NOT generate creative content (dialogue, visuals, etc).
    """

    SYSTEM_PROMPT = """You are a Script Structure Architect for Korean Webtoon YouTube Shorts.

**CRITICAL: Your ONLY job is to generate the STRUCTURAL SCAFFOLD, NOT creative content.**

**Task**: Analyze a Reddit story and create a perfectly structured script skeleton.

**What You MUST Generate:**

1. **Character Profiles (2-5 characters)**:
   - Identify main characters from the story
   - Create detailed visual profiles for each:
     * name: English name (e.g., "Jake", "Emma")
     * age: e.g., "20s", "45"
     * gender: "Male" or "Female"
     * role: "Protagonist", "Antagonist", "Supporting"
     * personality_vibe: Short descriptor (e.g., "Gloomy", "Bubbly")
     * body_type: e.g., "Slim", "Muscular", "Average"
     * hair_style_color: Detailed description
     * face_details_expression: Facial features and default expression
     * outfit: Detailed clothing description

2. **5-Act Structure** (EXACT ORDER):
   - Act 1: HOOK (target: 0.5-2s)
   - Act 2: BUILD (target: 2-4s)
   - Act 3: CRISIS (target: 3-4s)
   - Act 4: CLIMAX (target: 3-4s)
   - Act 5: RESOLUTION (target: 2-3s)

   For each act:
   - `act_type`: Correct enum value (hook, build, crisis, climax, resolution)
   - `target_duration_seconds`: Duration for the act (calculated)
   - `scenes`: Array of scene scaffolds (1-3 scenes per act)

3. **Scene Scaffolds** (For each scene):
   REQUIRED FIELDS (YOU MUST FILL THESE):
   - `scene_id`: Unique ID (format: "act_type_##", e.g., "hook_01")
   - `order`: Integer sequence within act (0, 1, 2...)
   - `estimated_duration_seconds`: Duration (2.0-4.0s, avg 3.0s)
   - `characters_present`: List of character names in this scene
   - `emotion`: Placeholder emotion (e.g., "neutral", "dramatic")
   - `visual_description`: PLACEHOLDER ONLY (e.g., "Scene description goes here")

   EMPTY FIELDS (Leave empty for ScriptWriter to fill):
   - `audio_chunks`: [] (empty array)
   - `panel_layout`: null
   - `bubble_metadata`: [] (empty array)
   - `camera_effect`: null
   - `visual_sfx`: null
   - `narration`: null (for legacy compatibility)

4. **Script Metadata**:
   - `script_id`: Generate unique ID (format: "script_YYYYMMDD_HHMMSS_random")
   - `story_id`: Copy from input story
   - `title`: Extract from story title
   - `total_estimated_duration`: Sum of all scene durations (MUST be 40-58s)
   - `target_audience`: "general"
   - `content_warnings`: [] (empty array)

**Duration Calculation Rules:**
- Total video duration: 40-58 seconds (target: 50s)
- Scene duration: 2.0-4.0s (average 3.0s)
- Number of scenes: 12-15 scenes total across 5 acts
- Hook: 1 scene (2s)
- Build: 2-3 scenes (6-9s total)
- Crisis: 3-4 scenes (9-12s total)
- Climax: 3-4 scenes (9-12s total)
- Resolution: 2-3 scenes (6-9s total)

**Scene Allocation Strategy:**
Based on story complexity:
- Simple story (< 500 words): 12 scenes
- Medium story (500-1000 words): 14 scenes
- Complex story (> 1000 words): 15 scenes

Distribute scenes to match story pacing.

**CRITICAL RULES:**
1. DO NOT generate creative content (dialogue, visual descriptions)
2. ALL structural fields must be filled correctly
3. ALL creative fields must be empty/null/[]
4. `order` must start at 0 for each act
5. `total_estimated_duration` MUST equal sum of scene durations
6. Every scene MUST have valid `emotion` enum value
7. Scene IDs must be unique across entire script

**Valid Emotion Enums** (use these for placeholder):
excited, shocked, sympathetic, dramatic, angry, happy, sad, neutral, suspenseful, sarcastic, frustrated, determined, relieved, exasperated

**Example Output Structure:**
```json
{
  "script_id": "script_20260102_120000_abc123",
  "story_id": "story_id_from_input",
  "title": "Story Title Here",
  "total_estimated_duration": 42.0,
  "target_audience": "general",
  "content_warnings": [],
  "character_profiles": [
    {
      "name": "Emily",
      "age": "20s",
      "gender": "Female",
      "role": "Protagonist",
      "personality_vibe": "Anxious, Caring",
      "body_type": "Slim",
      "hair_style_color": "Long wavy brown hair",
      "face_details_expression": "Wide eyes, worried expression",
      "outfit": "Casual sweater and jeans"
    }
  ],
  "acts": [
    {
      "act_type": "hook",
      "target_duration_seconds": 2.0,
      "scenes": [
        {
          "scene_id": "hook_01",
          "order": 0,
          "audio_chunks": [],
          "panel_layout": null,
          "bubble_metadata": [],
          "emotion": "neutral",
          "visual_description": "Placeholder for visual description",
          "characters_present": ["Emily"],
          "estimated_duration_seconds": 2.0,
          "camera_effect": null,
          "visual_sfx": null,
          "narration": null
        }
      ]
    }
  ]
}
```

**Your Output:**
Generate a complete script scaffold with perfect structure, ready for ScriptWriter to fill with creative content.
"""

    def __init__(self, config: ConfigManager) -> None:
        """Initialize Scene Structurer Agent.

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

        # Low temperature for deterministic structural output
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.1,  # Very low for consistent structure
            google_api_key=config.api.google_api_key,
            safety_settings=safety_settings,
        )

        # Use structured output to guarantee schema compliance
        self.structured_llm = self.llm.with_structured_output(Script)

        self.prompt = self._create_prompt()

        # Initialize Debugger
        self.debugger = LLMDebugger(self.config.scripts_dir.parent)

        # Log initialization
        key = config.api.google_api_key
        masked_key = f"{key[:4]}...{key[-4:]}" if key and len(key) > 8 else "INVALID"
        logger.info(f"Initialized SceneStructurer with model=gemini-2.5-flash, temp=0.1, key={masked_key}")

    def _create_prompt(self) -> ChatPromptTemplate:
        """Create prompt template for structure generation.

        Returns:
            Chat prompt template
        """
        return ChatPromptTemplate.from_messages(
            [
                ("system", self.SYSTEM_PROMPT),
                ("human", """Analyze this Reddit story and generate a structural scaffold:

**Story Title:** {title}

**Story Content:**
{content}

**Story Category:** {category}

**Instructions:**
1. Identify 2-5 main characters
2. Create detailed character profiles
3. Generate 5-act structure (hook, build, crisis, climax, resolution)
4. Allocate 12-15 scenes across acts based on story length
5. Calculate scene durations to total 40-58 seconds
6. Assign characters to scenes
7. Set placeholder emotions
8. Leave ALL creative fields empty

Generate the complete script scaffold now.
"""),
            ]
        )

    async def generate_scaffold(self, story: Story) -> Script:
        """Generate script structure scaffold from story.

        Args:
            story: Story to structure

        Returns:
            Script scaffold with structure only (no creative content)

        Raises:
            ScriptGenerationError: If scaffold generation fails
        """
        logger.info(f"Generating script scaffold for story: {story.id}")

        try:
            # Build prompt
            messages = self.prompt.format_messages(
                title=story.title,
                content=story.content,
                category=story.category.value,
            )

            # Generate scaffold
            logger.info("Calling LLM to generate structure scaffold...")
            start_time = datetime.now()

            scaffold = await self.structured_llm.ainvoke(messages)

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            # Log interaction
            try:
                self.debugger.log_interaction(
                    agent_name="SceneStructurer",
                    prompt=messages,
                    response=scaffold,
                    metadata={"story_id": story.id},
                    duration_ms=duration_ms
                )
            except Exception as log_e:
                logger.warning(f"Failed to log interaction: {log_e}")

            # Validate scaffold
            self._validate_scaffold(scaffold, story)

            logger.info(
                f"Generated scaffold: {len(scaffold.acts)} acts, "
                f"{scaffold.get_scene_count()} scenes, "
                f"{scaffold.total_estimated_duration}s duration"
            )

            return scaffold

        except Exception as e:
            logger.error(f"Scaffold generation failed: {e}")
            raise ScriptGenerationError(f"Failed to generate scaffold: {e}") from e

    def _validate_scaffold(self, scaffold: Script, story: Story) -> None:
        """Validate that scaffold meets structural requirements.

        Args:
            scaffold: Generated scaffold
            story: Source story

        Raises:
            ScriptGenerationError: If scaffold is invalid
        """
        # Check required fields are present
        if not scaffold.script_id or scaffold.script_id == "string":
            scaffold.script_id = (
                f"script_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{story.id.split('_')[-1]}"
            )

        if not scaffold.story_id or scaffold.story_id == "string":
            scaffold.story_id = story.id

        # Validate 5 acts
        if len(scaffold.acts) != 5:
            raise ScriptGenerationError(
                f"Scaffold must have exactly 5 acts, got {len(scaffold.acts)}"
            )

        # Validate scene count
        scene_count = scaffold.get_scene_count()
        if not (12 <= scene_count <= 15):
            logger.warning(
                f"Scene count {scene_count} outside recommended range 12-15"
            )

        # Validate duration
        if not (40 <= scaffold.total_estimated_duration <= 58):
            logger.warning(
                f"Total duration {scaffold.total_estimated_duration}s "
                f"outside target range 40-58s"
            )

        # Validate all scenes have order field
        for act in scaffold.acts:
            for idx, scene in enumerate(act.scenes):
                if scene.order != idx:
                    logger.warning(
                        f"Scene {scene.scene_id} has incorrect order "
                        f"(expected {idx}, got {scene.order}), fixing..."
                    )
                    scene.order = idx

        # Validate character profiles exist
        if not scaffold.character_profiles:
            raise ScriptGenerationError("Scaffold must have character profiles")

        if len(scaffold.character_profiles) < 2 or len(scaffold.character_profiles) > 5:
            logger.warning(
                f"Character count {len(scaffold.character_profiles)} "
                f"outside recommended range 2-5"
            )

        # Validate creative fields are empty
        for scene in scaffold.get_all_scenes():
            if scene.audio_chunks:
                logger.warning(
                    f"Scene {scene.scene_id} has audio_chunks (should be empty in scaffold)"
                )

            # Visual description should be placeholder only
            if scene.visual_description and len(scene.visual_description) > 100:
                logger.warning(
                    f"Scene {scene.scene_id} has detailed visual_description "
                    f"(should be placeholder in scaffold)"
                )

        logger.info("Scaffold validation passed")
