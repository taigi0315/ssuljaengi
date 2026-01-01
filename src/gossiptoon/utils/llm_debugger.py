"""LLM Debugging Utility for capturing prompts and responses."""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class LLMDebugger:
    """Captures LLM interactions for debugging purposes.
    
    Saves prompts, responses, and metadata to JSON files in a debug directory.
    """

    def __init__(self, output_dir: Path):
        """Initialize debugger.
        
        Args:
            output_dir: Base directory for outputs (usually ConfigManager.outputs_dir / job_id)
        """
        self.debug_dir = output_dir / "debug" / "llm"
        self.debug_dir.mkdir(parents=True, exist_ok=True)

    def log_interaction(
        self,
        agent_name: str,
        prompt: Any,
        response: Any,
        metadata: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None
    ) -> None:
        """Log an LLM interaction to a JSON file.
        
        Args:
            agent_name: Name of the agent (e.g., 'ScriptWriter', 'EngagementWriter')
            prompt: The input prompt (string or list of messages)
            response: The raw response from the LLM
            metadata: Additional context (e.g., model name, config)
            duration_ms: Time taken for the call in milliseconds
        """
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{agent_name.lower()}.json"
        filepath = self.debug_dir / filename
        
        # Serialize response if it's an object
        response_data = response
        if hasattr(response, "content"):
            response_data = response.content
        elif hasattr(response, "model_dump"):
             response_data = response.model_dump()
             
        # Serialize prompt if needed (handle LangChain messages)
        prompt_data = prompt
        if hasattr(prompt, "to_string"):
            prompt_data = prompt.to_string()
        elif isinstance(prompt, list):
            prompt_data = [
                m.content if hasattr(m, "content") else str(m) 
                for m in prompt
            ]

        log_entry = {
            "timestamp": timestamp,
            "agent": agent_name,
            "duration_ms": duration_ms,
            "metadata": metadata or {},
            "prompt": prompt_data,
            "response": response_data
        }

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(log_entry, f, indent=2, ensure_ascii=False)
            logger.debug(f"Logged LLM interaction to {filepath}")
        except Exception as e:
            logger.error(f"Failed to log LLM interaction: {e}")
