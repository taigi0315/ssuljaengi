"""Base effect interface for modular FFmpeg effects.

Strategy pattern for composable video effects.
Each effect is independent, tunable, and readable.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel, Field


class EffectConfig(BaseModel):
    """Base configuration for effects.

    Makes effects easy to tune via config files.
    """

    enabled: bool = Field(default=True, description="Whether effect is enabled")

    class Config:
        """Pydantic config."""

        extra = "allow"  # Allow effect-specific parameters


class Effect(ABC):
    """Base class for FFmpeg video effects.

    Strategy pattern: each effect is independent and composable.
    Effects generate FFmpeg filter strings that can be chained.
    """

    def __init__(self, config: EffectConfig) -> None:
        """Initialize effect.

        Args:
            config: Effect configuration
        """
        self.config = config

    @abstractmethod
    def get_filter_string(
        self,
        input_label: str,
        output_label: str,
        **context: Any,
    ) -> str:
        """Generate FFmpeg filter string for this effect.

        Args:
            input_label: Input stream label (e.g., "[0:v]")
            output_label: Output stream label (e.g., "[v0]")
            **context: Additional context (duration, timestamps, etc.)

        Returns:
            FFmpeg filter string

        Example:
            "[0:v]scale=1920:1080[v0]"
        """
        pass

    @abstractmethod
    def get_effect_name(self) -> str:
        """Get human-readable effect name.

        Returns:
            Effect name
        """
        pass

    def is_enabled(self) -> bool:
        """Check if effect is enabled.

        Returns:
            True if enabled
        """
        return self.config.enabled

    def get_description(self) -> str:
        """Get effect description for logging.

        Returns:
            Human-readable description
        """
        return f"{self.get_effect_name()} (enabled={self.is_enabled()})"


class CompositeEffect(Effect):
    """Composite effect that chains multiple effects.

    Allows building complex effects from simple ones.
    """

    def __init__(self, effects: list[Effect], config: Optional[EffectConfig] = None) -> None:
        """Initialize composite effect.

        Args:
            effects: List of effects to chain
            config: Optional config (defaults to enabled)
        """
        super().__init__(config or EffectConfig())
        self.effects = effects

    def get_filter_string(
        self,
        input_label: str,
        output_label: str,
        **context: Any,
    ) -> str:
        """Chain multiple effects together.

        Args:
            input_label: Input stream label
            output_label: Output stream label
            **context: Context for effects

        Returns:
            Chained filter string
        """
        if not self.effects:
            return f"{input_label}copy{output_label}"

        # Chain effects with intermediate labels
        filter_parts = []
        current_input = input_label

        for i, effect in enumerate(self.effects):
            if not effect.is_enabled():
                continue

            # Last effect uses final output label
            if i == len(self.effects) - 1:
                current_output = output_label
            else:
                current_output = f"[tmp{i}]"

            filter_str = effect.get_filter_string(
                current_input,
                current_output,
                **context,
            )
            filter_parts.append(filter_str)
            current_input = current_output

        return ";".join(filter_parts)

    def get_effect_name(self) -> str:
        """Get composite effect name.

        Returns:
            Composite name
        """
        names = [e.get_effect_name() for e in self.effects if e.is_enabled()]
        return f"Composite({', '.join(names)})"
