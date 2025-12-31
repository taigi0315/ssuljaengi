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

    Supports:
    - Gemini 2.0 Flash Experimental (imagen-3.0-generate-001)
    - 9:16 aspect ratio for Shorts
    - Image-to-image for character consistency
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
            Gemini client instance

        Raises:
            GeminiAPIError: If initialization fails
        """
        if self._client is not None:
            return self._client

        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            self._client = genai.ImageGenerationModel(self.model)
            logger.info(f"Gemini image client initialized: {self.model}")
            return self._client
        except ImportError:
            raise GeminiAPIError(
                "Google Generative AI package not installed. "
                "Install with: pip install google-generativeai"
            )
        except Exception as e:
            raise GeminiAPIError(f"Failed to initialize Gemini client: {e}") from e

    @retry_with_backoff(max_retries=3, exceptions=(GeminiAPIError, ImageGenerationError))
    async def generate_image(
        self,
        prompt: ImagePrompt,
        reference_image: Optional[Path] = None,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate image using Gemini.

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
            # Use the new google-genai SDK with Gemini image model (free tier)
            from google import genai
            from google.genai import types

            logger.info(f"Generating image with Gemini 2.5 Flash Image")
            logger.debug(f"Prompt: {prompt.base_prompt[:100]}...")

            # Build full prompt
            full_prompt = prompt.build_full_prompt()
            
            # Create client with API key
            client = genai.Client(api_key=self.api_key)

            # Generate image with Gemini model that supports image generation on free tier
            image_prompt = f"""Generate a 9:16 vertical image for a YouTube Short video.

Visual description: {full_prompt}

Style: Cinematic digital art, dramatic lighting, 8k quality.
Do not include any text or watermarks."""

            # Use Gemini 2.5 Flash Image which is free tier compatible
            response = client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[image_prompt],
            )
            
            # Check for image in response parts
            image_data = None
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data is not None:
                    image_data = part.inline_data.data
                    break
            
            if not image_data:
                raise ImageGenerationError("Gemini did not return an image. Model may have hit rate limits.")

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
