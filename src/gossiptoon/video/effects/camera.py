"""Camera movement effects factory.

Translates high-level camera directions (Zoom In, Pan Left, Shake)
into specific FFmpeg filter configurations.
"""

from typing import Any, Optional

from gossiptoon.core.constants import CameraEffectType
from gossiptoon.video.effects.base import Effect, EffectConfig
from gossiptoon.video.effects.ken_burns import KenBurnsConfig, KenBurnsEffect


class CameraEffectConfig(EffectConfig):
    """Configuration for camera effect."""
    
    effect_type: CameraEffectType
    intensity: float = 0.3  # Generic intensity multiplier


class CameraEffect(Effect):
    """Effect that applies specific camera movements."""

    def __init__(self, config: CameraEffectConfig) -> None:
        super().__init__(config)
        self.config: CameraEffectConfig = config
        self._delegate: Optional[Effect] = self._create_delegate()

    def _create_delegate(self) -> Optional[Effect]:
        """Create the specific underlying effect implementation."""
        eff_type = self.config.effect_type
        intensity = self.config.intensity

        # Static shot
        if eff_type == CameraEffectType.STATIC:
            return None

        # Zoom In (1.0 -> 1.0 + intensity)
        if eff_type == CameraEffectType.ZOOM_IN:
            return KenBurnsEffect(KenBurnsConfig(
                zoom_start=1.0,
                zoom_end=1.0 + intensity,
                pan_direction="none",
                ease_function="ease-in-out"
            ))

        # Zoom Out (1.0 + intensity -> 1.0)
        if eff_type == CameraEffectType.ZOOM_OUT:
            return KenBurnsEffect(KenBurnsConfig(
                zoom_start=1.0 + intensity,
                zoom_end=1.0,
                pan_direction="none",
                ease_function="ease-in-out"
            ))

        # Pans (require slight zoom to allow movement)
        pan_zoom = 1.1 + (intensity * 0.5)  # Zoom needed for panning space
        
        if eff_type == CameraEffectType.PAN_LEFT:
            return KenBurnsEffect(KenBurnsConfig(
                zoom_start=pan_zoom,
                zoom_end=pan_zoom,
                pan_direction="left",
                pan_intensity=intensity
            ))

        if eff_type == CameraEffectType.PAN_RIGHT:
            return KenBurnsEffect(KenBurnsConfig(
                zoom_start=pan_zoom,
                zoom_end=pan_zoom,
                pan_direction="right",
                pan_intensity=intensity
            ))
            
        if eff_type == CameraEffectType.PAN_UP:
            return KenBurnsEffect(KenBurnsConfig(
                zoom_start=pan_zoom,
                zoom_end=pan_zoom,
                pan_direction="up",
                pan_intensity=intensity
            ))

        if eff_type == CameraEffectType.PAN_DOWN:
            return KenBurnsEffect(KenBurnsConfig(
                zoom_start=pan_zoom,
                zoom_end=pan_zoom,
                pan_direction="down",
                pan_intensity=intensity
            ))

        # SHAKE requires different logic
        if eff_type == CameraEffectType.SHAKE:
            return ShakeEffect(intensity=intensity)

        return None

    def get_filter_string(
        self,
        input_label: str,
        output_label: str,
        **context: Any,
    ) -> str:
        if self._delegate:
            return self._delegate.get_filter_string(
                input_label, 
                output_label, 
                **context
            )
        
        # Static fallback (just copy)
        return f"{input_label}copy{output_label}"

    def get_effect_name(self) -> str:
        return f"Camera({self.config.effect_type.value})"


class ShakeEffect(Effect):
    """Intense shaking effect for dramatic moments."""
    
    def __init__(self, intensity: float = 0.3) -> None:
        super().__init__(EffectConfig())
        self.intensity = intensity

    def get_filter_string(
        self,
        input_label: str,
        output_label: str,
        **context: Any,
    ) -> str:
        # Use crop filter with random x/y variations
        # Requires input to be slightly larger or we crop in
        # We'll zoom in 10% to give room for shake
        
        # Note: This is an efficient "jitter" effect
        # x = (random(1)-0.5) * intensity * pixel_range
        
        # Simplified for robustness:
        # crop=w=iw*0.9:h=ih*0.9:x='(iw-ow)/2+((random(1)-0.5)*const)':y='...'
        
        shake_px = int(50 * self.intensity * 2)  # Shake amplitude in pixels
        
        return (
            f"{input_label}"
            f"crop=w=iw*0.9:h=ih*0.9:"
            f"x='(iw-ow)/2+((random(1)-0.5)*{shake_px})':"
            f"y='(ih-oh)/2+((random(1)-0.5)*{shake_px})':"
            f"exact=1"
            f",scale=1080:1920"  # Resize back to full res
            f"{output_label}"
        )

    def get_effect_name(self) -> str:
        return "ShockShake"
