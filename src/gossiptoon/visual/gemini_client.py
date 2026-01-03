"""Gemini image generation client implementation."""

import base64
import logging
from pathlib import Path
from typing import Optional

from gossiptoon.core.exceptions import GeminiAPIError, ImageGenerationError
from gossiptoon.models.visual import ImagePrompt
from gossiptoon.utils.retry import retry_with_backoff
from gossiptoon.visual.base import ImageClient

logger = logging.getLogger(__name__)


class GeminiImageClient(ImageClient):
    """Google Gemini image generation client.

    CRITICAL: This client MUST use model "gemini-2.5-flash-image" for image generation.
    
    DO NOT change the model to:
    - imagen-3.0-generate-001 (404 - requires paid tier)
    - image-generation-002 (404 - requires paid tier)
    - gemini-2.0-flash-exp (does NOT support image generation)
    
    See docs/IMAGE_GENERATION.md for full implementation details and debugging history.
    
    Supports:
    - Free tier image generation via gemini-2.5-flash-image
    - 9:16 aspect ratio for YouTube Shorts
    - Text-to-image generation
    """

    def __init__(
        self,
        api_key: str,
        model: str = "imagen-3.0-generate-001",
    ) -> None:
        """Initialize Gemini image client.

        Args:
            api_key: Google API key
            model: Gemini model identifier
        """
        self.api_key = api_key
        self.model = model
        self._client: Optional[any] = None

    def _init_client(self) -> any:
        """Initialize Gemini SDK client (lazy loading).

        Returns:
            Gemini client instance (google.genai.Client)

        Raises:
            GeminiAPIError: If initialization fails
        """
        if self._client is not None:
            return self._client

        try:
            from google import genai
            
            self._client = genai.Client(api_key=self.api_key)
            logger.info(f"Gemini image client initialized (google-genai SDK)")
            return self._client
        except ImportError:
            raise GeminiAPIError(
                "Google GenAI package not installed. "
                "Install with: pip install google-genai"
            )
        except Exception as e:
            if "invalid_grant" in str(e):
                logger.error("Google Auth Error: invalid_grant.")
            raise GeminiAPIError(f"Failed to initialize Gemini client: {e}") from e

    @retry_with_backoff(
        max_retries=3,
        exceptions=(GeminiAPIError, ImageGenerationError),
        custom_intervals=[1.0, 10.0, 30.0],  # Fixed intervals: 1s, 10s, 30s for rate limiting
    )
    async def generate_image(
        self,
        prompt: ImagePrompt,
        reference_image: Optional[Path] = None,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate image using Gemini (with fallback).

        Args:
            prompt: Image prompt with parameters
            reference_image: Optional reference for I2I
            output_path: Optional output path

        Returns:
            Path to generated image

        Raises:
            ImageGenerationError: If generation fails
        """
        try:
            client = self._init_client()
            
            logger.info(f"Generating image with {self.model}")
            logger.info(f"Generating image with {self.model}")
            
            # Handle both string prompts and ImagePrompt objects
            if isinstance(prompt, str):
                full_prompt = prompt
                logger.debug(f"Prompt (string): {prompt[:100]}...")
            else:
                logger.debug(f"Prompt: {prompt.base_prompt[:100]}...")
                # Build full prompt
                full_prompt = prompt.build_full_prompt()
            
            # Save image path setup
            if output_path is None:
                output_path = Path(f"image_{hash(full_prompt)}.png")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use Gemini 2.5 Flash Image (official image generation model)
            # Docs: https://ai.google.dev/gemini-api/docs/image-generation
            from google import genai
            from google.genai import types

            logger.info(f"Generating image with Gemini 2.5 Flash Image")
            
            # Create client with API key
            client = genai.Client(api_key=self.api_key)

            # Generate image with Gemini 2.5 Flash Image model
            image_prompt = f"""Generate a 9:16 vertical image for a YouTube Short video.

Visual description: {full_prompt}

Style: Cinematic digital art, dramatic lighting, 8k quality.
Style: Cinematic digital art, dramatic lighting, 8k quality.
CRITICAL: Do not include any Korean text or Hangul characters. If any text appears, it MUST be in English. No watermarks."""

            # Use Gemini 2.5 Flash Image (correct model name)
            response = client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[image_prompt],
            )
            
            # Check for image in response parts
            image_data = None
            for part in response.parts:
                if part.inline_data is not None:
                    # Image comes back as inline_data automatically
                    image_data = part.inline_data.data
                    break

            if not image_data:
                # Try to see if there's an error or empty content
                 logger.warning(f"Gemini response structure: {response}")
                 raise ImageGenerationError("Gemini did not return an image data (inline_data).")

            # Save image
            if output_path is None:
                output_path = Path(f"image_{hash(full_prompt)}.png")

            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write image bytes directly
            with open(output_path, "wb") as f:
                f.write(image_data)

            logger.info(f"Image saved to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Gemini image generation failed: {e}")
            raise ImageGenerationError(f"Image generation failed: {e}") from e

    def get_model_name(self) -> str:
        """Get model name.

        Returns:
            Model identifier
        """
        return self.model

    def supports_i2i(self) -> bool:
        """Check if model supports I2I.

        Returns:
            True for Gemini models
        """
        return True

    def get_recommended_params(self) -> dict[str, any]:
        """Get recommended parameters for Gemini.

        Returns:
            Recommended parameters
        """
        return {
            "temperature": 0.4,
            "aspect_ratio": "9:16",
            "style": "cinematic digital art, dramatic lighting, 8k quality",
            "negative_prompt": "text, watermark, blurry, low quality, distorted, deformed",
        }
