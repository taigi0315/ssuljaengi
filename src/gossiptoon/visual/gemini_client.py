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

    @retry_with_backoff(max_retries=3, exceptions=(GeminiAPIError, ImageGenerationError))
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
            logger.debug(f"Prompt: {prompt.base_prompt[:100]}...")

            # Build full prompt
            full_prompt = prompt.build_full_prompt()
            
            # Save image path setup
            if output_path is None:
                output_path = Path(f"image_{hash(full_prompt)}.png")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate images
            try:
                # Attempt generation with configured model (likely to fail if unbilled)
                response = client.models.generate_images(
                    model=self.model,
                    prompt=full_prompt,
                    config={
                        'number_of_images': 1,
                        'aspect_ratio': '9:16',
                        'safety_filter_level': 'block_only_high',
                        'person_generation': 'allow_adult',
                    }
                )
                
                if not response.generated_images:
                    raise ImageGenerationError("Gemini did not return any images.")

                # Save the first image
                response.generated_images[0].image.save(output_path)
                logger.info(f"Image saved to {output_path}")
                return output_path

            except Exception as e:
                logger.warning(f"Gemini API generation failed: {e}. Falling back to placeholder.")
                return self._generate_placeholder(prompt, output_path)

        except Exception as e:
             # Catch init errors or other unexpected crashes
            logger.error(f"Gemini image generation failed completely: {e}")
            # Even here, try fallback if client init failed
            try:
                logger.warning("Attempting fallback after total failure...")
                return self._generate_placeholder(prompt, output_path)
            except Exception as fallback_error:
                raise ImageGenerationError(f"Image generation failed: {e}") from fallback_error

    def _generate_placeholder(self, prompt: ImagePrompt, output_path: Optional[Path]) -> Path:
        """Generate a placeholder image using PIL."""
        from PIL import Image, ImageDraw, ImageFont
        import random

        width, height = 1080, 1920  # 9:16
        
        # Random background color
        color = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
        img = Image.new('RGB', (width, height), color=color)
        d = ImageDraw.Draw(img)
        
        # Add text
        text = f"Scene: {prompt.scene_id}\n(Placeholder)"
        try:
            # Try to load a font, otherwise default
            #font = ImageFont.truetype("Arial.ttf", 60)
            font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
            
        # Draw text in center (approx)
        d.text((width//2, height//2), text, fill=(255, 255, 255), anchor="mm", font=font)
        
        if output_path is None:
            output_path = Path(f"placeholder_{prompt.scene_id}.png")
            
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path)
        logger.info(f"Placeholder image saved to {output_path}")
        return output_path

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
