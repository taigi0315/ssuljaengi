"""Base interfaces for image generation (modular image providers).

This allows easy swapping between:
- Gemini Flash 2.0 / 2.5
- DALL-E 3
- Stable Diffusion (local)
- Imagen
- etc.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from gossiptoon.models.visual import ImagePrompt


class ImageClient(ABC):
    """Abstract base class for image generation clients.

    This allows easy swapping between Gemini, DALL-E, Stable Diffusion, etc.
    Same pattern as TTSClient for audio.
    """

    @abstractmethod
    async def generate_image(
        self,
        prompt: ImagePrompt,
        reference_image: Optional[Path] = None,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate image from prompt.

        Args:
            prompt: Image prompt with all parameters
            reference_image: Optional reference image for I2I (character consistency)
            output_path: Optional path to save image

        Returns:
            Path to generated image file

        Raises:
            ImageGenerationError: If generation fails
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get model name for logging.

        Returns:
            Model identifier string
        """
        pass

    @abstractmethod
    def supports_i2i(self) -> bool:
        """Check if model supports image-to-image generation.

        Returns:
            True if I2I is supported
        """
        pass

    @abstractmethod
    def get_recommended_params(self) -> dict[str, any]:
        """Get recommended generation parameters.

        Returns:
            Dict of recommended parameters for this model
        """
        pass
