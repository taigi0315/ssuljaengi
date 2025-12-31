"""LangGraph state management for the GossipToon pipeline."""

import logging
from typing import Annotated, Optional, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END

from gossiptoon.models.audio import AudioProject
from gossiptoon.models.script import Script
from gossiptoon.models.story import Story
from gossiptoon.models.video import VideoProject
from gossiptoon.models.visual import VisualProject

logger = logging.getLogger(__name__)


def add_messages(left: Sequence[BaseMessage], right: Sequence[BaseMessage]) -> Sequence[BaseMessage]:
    """Add messages to the state.

    Args:
        left: Existing messages
        right: New messages to add

    Returns:
        Combined message sequence
    """
    return list(left) + list(right)


class GossipToonState(TypedDict):
    """State for the GossipToon agent workflow.

    This state is passed between nodes in the LangGraph workflow
    and contains all intermediate results from the pipeline.
    """

    # LangChain messages for agent communication
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # Pipeline data
    story: Optional[Story]
    script: Optional[Script]
    audio_project: Optional[AudioProject]
    visual_project: Optional[VisualProject]
    video_project: Optional[VideoProject]

    # Workflow metadata
    current_step: str
    errors: list[str]
    retry_count: int

    # Configuration overrides (optional)
    config_overrides: dict[str, any]


class WorkflowBuilder:
    """Builder for creating the GossipToon LangGraph workflow."""

    def __init__(self) -> None:
        """Initialize workflow builder."""
        self.graph = StateGraph(GossipToonState)
        self.checkpointer = MemorySaver()

    def build(self) -> StateGraph:
        """Build the complete workflow graph.

        Returns:
            Compiled StateGraph
        """
        # Add nodes (these will be implemented as the pipeline progresses)
        self.graph.add_node("find_story", self._find_story_node)
        self.graph.add_node("write_script", self._write_script_node)
        self.graph.add_node("generate_audio", self._generate_audio_node)
        self.graph.add_node("create_visuals", self._create_visuals_node)
        self.graph.add_node("assemble_video", self._assemble_video_node)
        self.graph.add_node("handle_error", self._handle_error_node)

        # Define flow
        self.graph.set_entry_point("find_story")
        self.graph.add_edge("find_story", "write_script")
        self.graph.add_edge("write_script", "generate_audio")
        self.graph.add_edge("generate_audio", "create_visuals")
        self.graph.add_edge("create_visuals", "assemble_video")
        self.graph.add_edge("assemble_video", END)

        # Error handling edges (conditional)
        self.graph.add_conditional_edges(
            "handle_error",
            self._should_retry,
            {
                "retry": "find_story",
                "fail": END,
            },
        )

        # Compile with checkpointer for state persistence
        return self.graph.compile(checkpointer=self.checkpointer)

    def _find_story_node(self, state: GossipToonState) -> GossipToonState:
        """Node for finding viral Reddit stories.

        Args:
            state: Current workflow state

        Returns:
            Updated state with story
        """
        logger.info("Node: find_story")
        state["current_step"] = "find_story"

        try:
            # Story finding logic will be implemented by pipeline orchestrator
            # This is just a placeholder
            logger.info("Story finding node executed (placeholder)")
            return state
        except Exception as e:
            logger.error(f"Story finding failed: {e}")
            state["errors"].append(str(e))
            state["retry_count"] += 1
            return state

    def _write_script_node(self, state: GossipToonState) -> GossipToonState:
        """Node for writing video script.

        Args:
            state: Current workflow state

        Returns:
            Updated state with script
        """
        logger.info("Node: write_script")
        state["current_step"] = "write_script"

        try:
            # Script writing logic will be implemented by pipeline orchestrator
            logger.info("Script writing node executed (placeholder)")
            return state
        except Exception as e:
            logger.error(f"Script writing failed: {e}")
            state["errors"].append(str(e))
            state["retry_count"] += 1
            return state

    def _generate_audio_node(self, state: GossipToonState) -> GossipToonState:
        """Node for generating audio with TTS and timestamps.

        Args:
            state: Current workflow state

        Returns:
            Updated state with audio project
        """
        logger.info("Node: generate_audio")
        state["current_step"] = "generate_audio"

        try:
            # Audio generation logic (Phase 3)
            logger.info("Audio generation node executed (placeholder)")
            return state
        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            state["errors"].append(str(e))
            state["retry_count"] += 1
            return state

    def _create_visuals_node(self, state: GossipToonState) -> GossipToonState:
        """Node for creating visual assets.

        Args:
            state: Current workflow state

        Returns:
            Updated state with visual project
        """
        logger.info("Node: create_visuals")
        state["current_step"] = "create_visuals"

        try:
            # Visual generation logic (Phase 4)
            logger.info("Visual creation node executed (placeholder)")
            return state
        except Exception as e:
            logger.error(f"Visual creation failed: {e}")
            state["errors"].append(str(e))
            state["retry_count"] += 1
            return state

    def _assemble_video_node(self, state: GossipToonState) -> GossipToonState:
        """Node for assembling final video.

        Args:
            state: Current workflow state

        Returns:
            Updated state with video project
        """
        logger.info("Node: assemble_video")
        state["current_step"] = "assemble_video"

        try:
            # Video assembly logic (Phase 5)
            logger.info("Video assembly node executed (placeholder)")
            return state
        except Exception as e:
            logger.error(f"Video assembly failed: {e}")
            state["errors"].append(str(e))
            state["retry_count"] += 1
            return state

    def _handle_error_node(self, state: GossipToonState) -> GossipToonState:
        """Node for handling errors.

        Args:
            state: Current workflow state

        Returns:
            Updated state
        """
        logger.info("Node: handle_error")
        state["current_step"] = "handle_error"

        logger.warning(
            f"Error handling triggered. Retry count: {state['retry_count']}"
        )
        logger.warning(f"Errors: {state['errors']}")

        return state

    def _should_retry(self, state: GossipToonState) -> str:
        """Determine if workflow should retry after error.

        Args:
            state: Current workflow state

        Returns:
            "retry" or "fail"
        """
        max_retries = 3
        if state["retry_count"] < max_retries:
            logger.info(f"Retrying (attempt {state['retry_count'] + 1}/{max_retries})")
            return "retry"
        else:
            logger.error(f"Max retries ({max_retries}) exceeded. Failing workflow.")
            return "fail"


def create_initial_state() -> GossipToonState:
    """Create initial workflow state.

    Returns:
        Initial state dictionary
    """
    return {
        "messages": [],
        "story": None,
        "script": None,
        "audio_project": None,
        "visual_project": None,
        "video_project": None,
        "current_step": "init",
        "errors": [],
        "retry_count": 0,
        "config_overrides": {},
    }
