"""Configuration management for GossipToon."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

from gossiptoon.core.constants import (
    DEFAULT_AUDIO_CODEC,
    DEFAULT_MAX_RETRIES,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REQUEST_TIMEOUT,
    DEFAULT_VIDEO_CODEC,
    DEFAULT_VIDEO_FPS,
    DEFAULT_VIDEO_PRESET,
    DEFAULT_VIDEO_RESOLUTION,
    DEFAULT_WHISPER_MODEL,
)
from gossiptoon.core.exceptions import ConfigurationError


class APIConfig(BaseModel):
    """API configuration for external services."""

    openai_api_key: Optional[str] = Field(None, description="OpenAI API key (deprecated, not used)")
    google_api_key: str = Field(..., description="Google Gemini API key")
    elevenlabs_api_key: str = Field(..., description="ElevenLabs API key")
    tavily_api_key: Optional[str] = Field(None, description="Tavily search API key")
    reddit_client_id: Optional[str] = Field(None, description="Reddit client ID")
    reddit_client_secret: Optional[str] = Field(None, description="Reddit client secret")
    reddit_user_agent: str = Field(default="GossipToon/0.1.0", description="Reddit user agent")

    @field_validator("google_api_key", "elevenlabs_api_key")
    @classmethod
    def validate_required_keys(cls, v: str, info: object) -> str:
        """Validate that required API keys are not empty."""
        if not v or v.startswith("..."):
            field_name = info.field_name if hasattr(info, "field_name") else "API key"
            raise ValueError(f"{field_name} is required and cannot be empty")
        return v


class VideoConfig(BaseModel):
    """Video rendering configuration."""

    resolution: str = Field(default=DEFAULT_VIDEO_RESOLUTION, description="Video resolution")
    fps: int = Field(default=DEFAULT_VIDEO_FPS, ge=24, le=60, description="Frames per second")
    video_codec: str = Field(default=DEFAULT_VIDEO_CODEC, description="Video codec")
    audio_codec: str = Field(default=DEFAULT_AUDIO_CODEC, description="Audio codec")
    preset: str = Field(default=DEFAULT_VIDEO_PRESET, description="FFmpeg preset")
    bitrate: str = Field(default="5M", description="Video bitrate")

    # Dynamic Video Configuration
    target_duration: int = Field(default=40, description="Target video duration in seconds")
    min_scenes: int = Field(default=12, description="Minimum number of scenes for dynamic pacing")

    # Effect configuration
    ken_burns_enabled: bool = Field(default=True, description="Enable Ken Burns effect")
    use_ai_camera_effects: bool = Field(
        default=True, description="Allow AI to choose camera effects per scene"
    )
    captions_enabled: bool = Field(default=True, description="Enable dynamic captions")

    @field_validator("resolution")
    @classmethod
    def validate_resolution(cls, v: str) -> str:
        """Validate resolution format."""
        if "x" not in v:
            raise ValueError("Resolution must be in format WIDTHxHEIGHT (e.g., 1080x1920)")
        try:
            width, height = map(int, v.split("x"))
            if width <= 0 or height <= 0:
                raise ValueError("Resolution dimensions must be positive")
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid resolution format: {v}") from e
        return v

    @property
    def width(self) -> int:
        """Get video width from resolution.

        Returns:
            Video width in pixels
        """
        return int(self.resolution.split("x")[0])

    @property
    def height(self) -> int:
        """Get video height from resolution.

        Returns:
            Video height in pixels
        """
        return int(self.resolution.split("x")[1])


class AudioConfig(BaseModel):
    """Audio generation configuration."""

    default_voice_id: str = Field(
        default="21m00Tcm4TlvDq8ikWAM", description="Default ElevenLabs voice ID"
    )
    whisper_model: str = Field(default=DEFAULT_WHISPER_MODEL, description="Whisper model size")

    # Audio Dynamics
    speed_factor: float = Field(default=1.1, description="Audio speedup factor (e.g., 1.1 = +10%)")
    normalize_audio: bool = Field(default=True, description="Normalize audio volume")

    @field_validator("whisper_model")
    @classmethod
    def validate_whisper_model(cls, v: str) -> str:
        """Validate Whisper model name."""
        valid_models = ["tiny", "base", "small", "medium", "large"]
        if v not in valid_models:
            raise ValueError(f"Whisper model must be one of {valid_models}")
        return v


class ImageConfig(BaseModel):
    """Image generation configuration."""

    style: str = Field(
        default=(
            "A panel from a Korean webtoon, digital illustration style, with clean line art and expressive characters. "
            "The characters have large, expressive eyes and stylish, contemporary clothing. "
            "The background is detailed but clean, with soft, bright digital coloring. "
            "The overall aesthetic is modern, clean, and vibrant, typical of a popular romance or drama webtoon."
        ),
        description="Default image style",
    )
    aspect_ratio: str = Field(default="9:16", description="Image aspect ratio")
    negative_prompt: str = Field(
        default="text, watermark, blurry, low quality, distorted, speech bubbles, jagged lines, messy sketch",
        description="Negative prompt",
    )


class ScriptConfig(BaseModel):
    """Script generation configuration."""

    webtoon_mode: bool = Field(default=True, description="Enable webtoon-style script generation")
    min_dialogue_chars: int = Field(default=5, description="Minimum characters for dialogue chunks")
    max_dialogue_chars: int = Field(
        default=100, description="Maximum characters for dialogue chunks"
    )

    # Legacy narration limits
    min_narration_chars: int = Field(default=10, description="Minimum characters for narration")
    max_narration_chars: int = Field(default=200, description="Maximum characters for narration")

    @field_validator("max_dialogue_chars")
    @classmethod
    def validate_dialogue_limit(cls, v: int) -> int:
        if v < 20:
            raise ValueError("Max dialogue limit too low (min 20)")
        return v


class AppConfig(BaseModel):
    """Application-level configuration."""

    output_dir: Path = Field(default=DEFAULT_OUTPUT_DIR, description="Output directory")
    log_level: str = Field(default="INFO", description="Logging level")
    max_retries: int = Field(
        default=DEFAULT_MAX_RETRIES, ge=0, le=10, description="Max retry attempts"
    )
    request_timeout: int = Field(
        default=DEFAULT_REQUEST_TIMEOUT, ge=5, le=300, description="Request timeout in seconds"
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v_upper

    @field_validator("output_dir")
    @classmethod
    def validate_output_dir(cls, v: Path) -> Path:
        """Ensure output directory exists."""
        v.mkdir(parents=True, exist_ok=True)
        return v


class ConfigManager:
    """Main configuration manager."""

    def __init__(self, env_file: Optional[Path] = None) -> None:
        """Initialize configuration manager.

        Args:
            env_file: Optional path to .env file. If None, searches for .env in project root.
        """
        # Load environment variables
        if env_file and env_file.exists():
            load_dotenv(env_file)
        else:
            load_dotenv()  # Loads from .env in current directory or parent directories

        try:
            self.api = APIConfig(
                openai_api_key=os.getenv("OPENAI_API_KEY"),  # Optional, deprecated
                google_api_key=self._get_env("GOOGLE_API_KEY"),
                elevenlabs_api_key=self._get_env("ELEVENLABS_API_KEY"),
                tavily_api_key=os.getenv("TAVILY_API_KEY"),
                reddit_client_id=os.getenv("REDDIT_CLIENT_ID"),
                reddit_client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
                reddit_user_agent=os.getenv("REDDIT_USER_AGENT", "GossipToon/0.1.0"),
            )

            self.video = VideoConfig(
                resolution=os.getenv("DEFAULT_VIDEO_RESOLUTION", DEFAULT_VIDEO_RESOLUTION),
                fps=int(os.getenv("DEFAULT_VIDEO_FPS", DEFAULT_VIDEO_FPS)),
                video_codec=os.getenv("DEFAULT_VIDEO_CODEC", DEFAULT_VIDEO_CODEC),
                audio_codec=os.getenv("DEFAULT_AUDIO_CODEC", DEFAULT_AUDIO_CODEC),
                preset=os.getenv("DEFAULT_VIDEO_PRESET", DEFAULT_VIDEO_PRESET),
                bitrate=os.getenv("DEFAULT_VIDEO_BITRATE", "5M"),
            )

            self.audio = AudioConfig(
                default_voice_id=os.getenv("DEFAULT_VOICE_ID", "21m00Tcm4TlvDq8ikWAM"),
                whisper_model=os.getenv("WHISPER_MODEL", DEFAULT_WHISPER_MODEL),
            )

            self.image = ImageConfig(
                style=os.getenv(
                    "IMAGE_STYLE",
                    (
                        "A panel from a Korean webtoon, digital illustration style, with clean line art and expressive characters. "
                        "The characters have large, expressive eyes and stylish, contemporary clothing. "
                        "The background is detailed but clean, with soft, bright digital coloring. "
                        "The overall aesthetic is modern, clean, and vibrant, typical of a popular romance or drama webtoon."
                    ),
                ),
                aspect_ratio=os.getenv("IMAGE_ASPECT_RATIO", "9:16"),
                negative_prompt=os.getenv(
                    "IMAGE_NEGATIVE_PROMPT",
                    "text, watermark, blurry, low quality, distorted, speech bubbles, jagged lines, messy sketch",
                ),
            )

            self.script = ScriptConfig(
                webtoon_mode=os.getenv("WEBTOON_MODE", "True").lower() == "true",
                min_dialogue_chars=int(os.getenv("MIN_DIALOGUE_CHARS", "5")),
                max_dialogue_chars=int(os.getenv("MAX_DIALOGUE_CHARS", "100")),
            )

            output_dir_str = os.getenv("OUTPUT_DIR", str(DEFAULT_OUTPUT_DIR))
            self._base_output_dir = Path(output_dir_str)
            self.app = AppConfig(
                output_dir=self._base_output_dir,
                log_level=os.getenv("LOG_LEVEL", "INFO"),
                max_retries=int(os.getenv("MAX_RETRIES", DEFAULT_MAX_RETRIES)),
                request_timeout=int(os.getenv("REQUEST_TIMEOUT", DEFAULT_REQUEST_TIMEOUT)),
            )

        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}") from e

    def set_job_context(self, job_id: str) -> None:
        """Set job context for output directory organization.

        Args:
            job_id: Unique job identifier (e.g., project_id)
        """
        job_dir = self._base_output_dir / job_id
        self.app.output_dir = job_dir

        # Ensure directories exist
        self.stories_dir
        self.scripts_dir
        self.audio_dir
        self.images_dir
        self.videos_dir
        self.checkpoints_dir

    @staticmethod
    def _get_env(key: str) -> str:
        """Get environment variable or raise error if missing.

        Args:
            key: Environment variable name

        Returns:
            Environment variable value

        Raises:
            ConfigurationError: If environment variable is missing
        """
        value = os.getenv(key)
        if not value:
            raise ConfigurationError(
                f"Missing required environment variable: {key}. "
                f"Please set it in your .env file or environment."
            )
        return value

    def validate(self) -> None:
        """Validate all configuration settings.

        Raises:
            ConfigurationError: If configuration is invalid
        """
        # Configuration is validated during initialization by Pydantic
        # This method is provided for explicit validation calls
        pass

    @property
    def stories_dir(self) -> Path:
        """Get stories output directory."""
        path = self.app.output_dir / "stories"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def scripts_dir(self) -> Path:
        """Get scripts output directory."""
        path = self.app.output_dir / "scripts"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def audio_dir(self) -> Path:
        """Get audio output directory."""
        path = self.app.output_dir / "audio"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def images_dir(self) -> Path:
        """Get images output directory."""
        path = self.app.output_dir / "images"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def videos_dir(self) -> Path:
        """Get videos output directory."""
        path = self.app.output_dir / "videos"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def checkpoints_dir(self) -> Path:
        """Get checkpoints output directory."""
        path = self.app.output_dir / "checkpoints"
        path.mkdir(parents=True, exist_ok=True)
        return path
