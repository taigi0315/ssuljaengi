"""DALL-E 3 image generation client implementation (alternative to Gemini)."""

import logging
from pathlib import Path
from typing import Optional

import httpx

from gossiptoon.core.exceptions import ImageGenerationError, OpenAIAPIError
from gossiptoon.models.visual import ImagePrompt
from gossiptoon.utils.retry import retry_with_backoff
from gossiptoon.visual.base import ImageClient

logger = logging.getLogger(__name__)


class DALLEImageClient(ImageClient):
    """OpenAI DALL-E 3 image generation client.

    Alternative to Gemini for image generation.
    Easy to swap: just change image_client parameter.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "dall-e-3",
        quality: str = "standard",
    ) -> None:
        """Initialize DALL-E client.

        Args:
            api_key: OpenAI API key
            model: Model name (dall-e-3)
            quality: Image quality (standard or hd)
        """
        self.api_key = api_key
        self.model = model
        self.quality = quality
        self._client: Optional[any] = None

    def _init_client(self) -> any:
        """Initialize OpenAI client (lazy loading).

        Returns:
            OpenAI client instance

        Raises:
            OpenAIAPIError: If initialization fails
        """
        if self._client is not None:
            return self._client

        try:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(api_key=self.api_key)
            logger.info(f"DALL-E client initialized: {self.model}")
            return self._client
        except ImportError:
            raise OpenAIAPIError(
                "OpenAI package not installed. Install with: pip install openai"
            )
        except Exception as e:
            raise OpenAIAPIError(f"Failed to initialize DALL-E client: {e}") from e

    @retry_with_backoff(max_retries=3, exceptions=(OpenAIAPIError, ImageGenerationError))
    async def generate_image(
        self,
        prompt: ImagePrompt,
        reference_image: Optional[Path] = None,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate image using DALL-E 3.

        Args:
            prompt: Image prompt with parameters
            reference_image: Not supported by DALL-E 3 (ignored)
            output_path: Optional output path

        Returns:
            Path to generated image

        Raises:
            ImageGenerationError: If generation fails
        """
        try:
            client = self._init_client()

            logger.info(f"Generating image with DALL-E: {self.model}")

            if reference_image:
                logger.warning(
                    "DALL-E 3 does not support I2I. Reference image will be ignored. "
                    "Consider using Gemini for character consistency."
                )

            # Build full prompt
            full_prompt = prompt.build_full_prompt()

            # DALL-E 3 only supports 1024x1024 and 1024x1792 (portrait)
            size = "1024x1792"  # Portrait for 9:16

            # Generate image
            response = await client.images.generate(
                model=self.model,
                prompt=full_prompt,
                size=size,
                quality=self.quality,
                n=1,
            )

            # Get image URL
            image_url = response.data[0].url

            # Download image
            if output_path is None:
                output_path = Path(f"image_{hash(full_prompt)}.png")

            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Download and save
            async with httpx.AsyncClient() as http_client:
                response = await http_client.get(image_url)
                response.raise_for_status()

                with open(output_path, "wb") as f:
                    f.write(response.content)

            logger.info(f"Image saved to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"DALL-E image generation failed: {e}")
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
            False for DALL-E 3 (use Gemini for I2I)
        """
        return False

    def get_recommended_params(self) -> dict[str, any]:
        """Get recommended parameters for DALL-E.

        Returns:
            Recommended parameters
        """
        return {
            "quality": "hd",
            "size": "1024x1792",
            "style": "vivid, cinematic, dramatic",
        }
