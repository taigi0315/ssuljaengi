"""EngagementWriter agent for generating viewer participation hooks.

This agent analyzes the script and strategically places 2-3 text overlays
to maximize viewer engagement (comments, shares, retention).
"""

import logging
from typing import Optional

from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from gossiptoon.models.engagement import EngagementProject
from gossiptoon.models.script import Script

logger = logging.getLogger(__name__)


class EngagementWriter:
    """LangChain agent for generating viewer engagement hooks."""

    SYSTEM_PROMPT = """You are an expert YouTube Shorts engagement strategist.

**Task**: Analyze the provided script and generate 2-3 strategic text overlays 
to maximize viewer engagement (comments, shares, retention).

**Guidelines:**
1. **Frequency**: Exactly 2-3 hooks per video (don't overwhelm)
2. **Placement**: Hook, Crisis, or Climax acts (dramatic peaks)
3. **Timing**: Within scene - start (0.0), middle (0.5), or end (1.0)
4. **Length**: Max 60 characters (readable in 2-3 seconds)

**Styles (Mix these):**
- **question**: Provoke thought - "Would YOU do this?"
- **comment**: Build anticipation - "Wait for it..." 
- **reaction**: Binary choice - "Team Mom or Team DIL? 👇"
- **sympathy**: Emotional connection - "Imagine being her..."
- **conflict**: Spark debate - "Who's wrong here?"

**Best Practices:**
- Use emojis sparingly (🤔 ✅ 🚩 👀 👇)
- Reference specific story elements
- Avoid spoilers - tease, don't reveal
- Create curiosity gaps
- Align with scene emotion
- Make it conversational and relatable

**Examples:**
- Crisis scene: "Red flag or justified? 🚩" (conflict)
- Climax scene: "Plot twist incoming... 👀" (comment)
- Resolution: "Am I the villain here? 🤔" (question)
- Hook: "Would YOU forgive this?!" (question)
- Setup: "Team Grandma 👵 or Team DIL?" (reaction)

**Output Format**: JSON matching EngagementProject schema."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize EngagementWriter agent.

        Args:
            api_key: OpenAI API key (optional, uses env var if not provided)
        """
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.8,  # Higher for creative hooks
            api_key=api_key,
        )
        self.parser = PydanticOutputParser(pydantic_object=EngagementProject)

    async def generate_engagement_hooks(self, script: Script) -> EngagementProject:
        """Generate engagement hooks from script analysis.

        Args:
            script: The generated script

        Returns:
            EngagementProject with 2-3 strategic hooks
        """
        logger.info("Generating engagement hooks...")

        # Build prompt
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.SYSTEM_PROMPT),
                (
                    "user",
                    "Script Summary:\n\n{script_summary}\n\n{format_instructions}",
                ),
            ]
        )

        # Create chain
        chain = prompt | self.llm | self.parser

        # Execute
        engagement_project = await chain.ainvoke(
            {
                "script_summary": self._format_script_summary(script),
                "format_instructions": self.parser.get_format_instructions(),
            }
        )

        logger.info(
            f"Generated {len(engagement_project.hooks)} engagement hooks: "
            f"{[h.hook_id for h in engagement_project.hooks]}"
        )

        return engagement_project

    def _format_script_summary(self, script: Script) -> str:
        """Format script for LLM analysis.

        Args:
            script: The script to summarize

        Returns:
            Formatted summary string
        """
        summary = f"**Story Duration**: {script.total_estimated_duration:.1f}s\n"
        summary += f"**Target Audience**: {script.target_audience}\n\n"

        for act in script.acts:
            summary += f"\n## {act.act_type.value.upper()} Act ({len(act.scenes)} scenes, {act.target_duration_seconds:.1f}s)\n"

            for scene in act.scenes:
                summary += (
                    f"- **{scene.scene_id}** (emotion: {scene.emotion.value}): "
                    f"{scene.narration[:80]}{'...' if len(scene.narration) > 80 else ''}\n"
                )

        return summary
