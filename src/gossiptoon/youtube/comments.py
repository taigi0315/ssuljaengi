"""YouTube Comment Manager."""
from pathlib import Path
from typing import Dict, Optional
import yaml
from gossiptoon.core.config import ConfigManager

class CommentManager:
    """Manages YouTube comment generation and pinning."""

    def __init__(self, config: Optional[ConfigManager] = None):
        """Initialize CommentManager."""
        self.config = config or ConfigManager()
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, Dict[str, str]]:
        """Load comment templates from config."""
        # Try to find the templates file
        # Priority: Configured path -> Local config dir -> Package config dir
        
        # This assumes the standardized location based on the implementation plan
        # Ideally this path should be in the main ConfigManager, but for now we look in known spots
        project_root = Path(__file__).parents[3] # src/gossiptoon/youtube/comments.py -> ... -> root
        possible_paths = [
             project_root / "config" / "comment_templates.yaml",
             Path("config/comment_templates.yaml"),
        ]
        
        for path in possible_paths:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f)
        
        # Fallback default templates if file not found
        return {
            "engagement_default": {
                "template": "🔗 Original story: {source_url}\n\nWhat do you think? 👇"
            }
        }

    def generate_comment(
        self,
        source_url: str,
        template_name: str = "engagement_default",
        extra_vars: Optional[Dict[str, str]] = None
    ) -> str:
        """Generate comment text from template."""
        if template_name not in self.templates:
            # Fallback to default if template not found
            template_name = "engagement_default"
            
        template_data = self.templates.get(template_name, {})
        template_text = template_data.get("template", "")
        
        # Prepare variables
        variables = {
            "source_url": source_url,
            "protagonist": "OP", # Default
        }
        if extra_vars:
            variables.update(extra_vars)
            
        # Format
        try:
            return template_text.format(**variables)
        except KeyError as e:
            # If a key is missing in variables but present in template, 
            # we might want to fail gracefully or leave it. 
            # For now, let's return a safe string.
            return template_text.replace("{source_url}", source_url)

    def post_comment(self, video_id: str, text: str) -> str:
        """Post a comment on a video (Placeholder for API)."""
        raise NotImplementedError("API integration pending TICKET-023")

    def pin_comment(self, comment_id: str) -> bool:
        """Pin a comment (Placeholder for API)."""
        raise NotImplementedError("API integration pending TICKET-023")
