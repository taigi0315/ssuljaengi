"""Ken Burns effect for cinematic image movement.

Smooth zoom and pan effect to add visual interest to static images.
Highly tunable parameters for easy customization.
"""

from typing import Any, Literal

from pydantic import Field

from gossiptoon.video.effects.base import Effect, EffectConfig


class KenBurnsConfig(EffectConfig):
    """Configuration for Ken Burns effect.

    All parameters are tunable for easy customization.
    """

    # Zoom parameters
    zoom_start: float = Field(
        default=1.0,
        ge=1.0,
        le=2.0,
        description="Starting zoom level (1.0 = no zoom)",
    )
    zoom_end: float = Field(
        default=1.2,
        ge=1.0,
        le=2.0,
        description="Ending zoom level (1.2 = 20% zoom in)",
    )

    # Pan parameters
    pan_direction: Literal["left", "right", "up", "down", "none"] = Field(
        default="none",
        description="Pan direction (none = center zoom only)",
    )
    pan_intensity: float = Field(
        default=0.1,
        ge=0.0,
        le=0.5,
        description="Pan intensity (0.1 = subtle, 0.5 = dramatic)",
    )

    # Timing
    ease_function: Literal["linear", "ease-in", "ease-out", "ease-in-out"] = Field(
        default="ease-in-out",
        description="Easing function for smooth motion",
    )

    # Output dimensions
    output_width: int = Field(default=1080, ge=720, description="Output width")
    output_height: int = Field(default=1920, ge=1280, description="Output height")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "enabled": True,
                "zoom_start": 1.0,
                "zoom_end": 1.2,
                "pan_direction": "up",
                "pan_intensity": 0.15,
                "ease_function": "ease-in-out",
                "output_width": 1080,
                "output_height": 1920,
            }
        }


class KenBurnsEffect(Effect):
    """Ken Burns effect implementation.

    Creates smooth zoom and pan animations on static images.

    Technical approach:
    - Uses FFmpeg's zoompan filter
    - Calculates zoom and position over time
    - Applies easing for smooth motion
    """

    def __init__(self, config: KenBurnsConfig) -> None:
        """Initialize Ken Burns effect.

        Args:
            config: Ken Burns configuration
        """
        super().__init__(config)
        self.config: KenBurnsConfig = config

    def get_filter_string(
        self,
        input_label: str,
        output_label: str,
        **context: Any,
    ) -> str:
        """Generate zoompan filter string.

        Args:
            input_label: Input stream label
            output_label: Output stream label
            **context: Must contain 'duration' (scene duration in seconds)

        Returns:
            FFmpeg zoompan filter string

        Example:
            "[0:v]zoompan=z='zoom(1.0,1.2)':x='pan_x':y='pan_y':d=150:s=1080x1920[v0]"
        """
        duration = context.get("duration", 5.0)
        fps = context.get("fps", 30)

        # Calculate total frames
        total_frames = int(duration * fps)

        # Build zoom expression
        zoom_expr = self._build_zoom_expression(total_frames)

        # Build pan expressions
        x_expr, y_expr = self._build_pan_expressions(total_frames)

        # Build zoompan filter
        filter_str = (
            f"{input_label}zoompan="
            f"z='{zoom_expr}':"
            f"x='{x_expr}':"
            f"y='{y_expr}':"
            f"d=1:"  # d=1 because input is already a video stream of correct length
            f"s={self.config.output_width}x{self.config.output_height}:"
            f"fps={fps}"
            f"{output_label}"
        )

        return filter_str

    def _build_zoom_expression(self, total_frames: int) -> str:
        """Build zoom expression with easing.

        Args:
            total_frames: Total number of frames

        Returns:
            FFmpeg expression for zoom over time
        """
        z_start = self.config.zoom_start
        z_end = self.config.zoom_end

        if z_start == z_end:
            # No zoom - constant
            return str(z_start)

        # Progress from 0 to 1 over duration
        progress = f"(on/{total_frames})"

        # Apply easing function
        if self.config.ease_function == "linear":
            eased = progress
        elif self.config.ease_function == "ease-in":
            # Quadratic ease-in
            eased = f"({progress}*{progress})"
        elif self.config.ease_function == "ease-out":
            # Quadratic ease-out
            eased = f"(1-(1-{progress})*(1-{progress}))"
        elif self.config.ease_function == "ease-in-out":
            # Cubic ease-in-out
            eased = (
                f"(if(lt({progress},0.5),"
                f"4*{progress}*{progress}*{progress},"
                f"1-pow(-2*{progress}+2,3)/2))"
            )
        else:
            eased = progress

        # Interpolate between start and end zoom
        zoom_expr = f"({z_start}+({z_end}-{z_start})*{eased})"

        return zoom_expr

    def _build_pan_expressions(self, total_frames: int) -> tuple[str, str]:
        """Build pan expressions for x and y coordinates.

        Args:
            total_frames: Total number of frames

        Returns:
            Tuple of (x_expression, y_expression)
        """
        if self.config.pan_direction == "none":
            # Center crop - no pan
            return ("iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)")

        intensity = self.config.pan_intensity
        progress = f"(on/{total_frames})"

        # Base centered position
        x_center = "iw/2-(iw/zoom/2)"
        y_center = "ih/2-(ih/zoom/2)"

        # Apply pan based on direction
        if self.config.pan_direction == "right":
            # Pan from left to right
            x_expr = f"({x_center}-iw*{intensity}*(1-{progress}))"
            y_expr = y_center

        elif self.config.pan_direction == "left":
            # Pan from right to left
            x_expr = f"({x_center}+iw*{intensity}*(1-{progress}))"
            y_expr = y_center

        elif self.config.pan_direction == "down":
            # Pan from top to bottom
            x_expr = x_center
            y_expr = f"({y_center}-ih*{intensity}*(1-{progress}))"

        elif self.config.pan_direction == "up":
            # Pan from bottom to top
            x_expr = x_center
            y_expr = f"({y_center}+ih*{intensity}*(1-{progress}))"

        else:
            x_expr = x_center
            y_expr = y_center

        return (x_expr, y_expr)

    def get_effect_name(self) -> str:
        """Get effect name.

        Returns:
            Effect name
        """
        return f"KenBurns(zoom:{self.config.zoom_start}->{self.config.zoom_end}, pan:{self.config.pan_direction})"

    def get_tunable_params(self) -> dict[str, Any]:
        """Get tunable parameters for easy adjustment.

        Returns:
            Dictionary of tunable parameters
        """
        return {
            "zoom_start": self.config.zoom_start,
            "zoom_end": self.config.zoom_end,
            "pan_direction": self.config.pan_direction,
            "pan_intensity": self.config.pan_intensity,
            "ease_function": self.config.ease_function,
        }
