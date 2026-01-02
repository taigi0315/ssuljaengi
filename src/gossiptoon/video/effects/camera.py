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

        # SHAKE variants
        if eff_type == CameraEffectType.SHAKE:
            return ShakeEffect(intensity=0.3, speed="normal")
            
        if eff_type == CameraEffectType.SHAKE_SLOW:
            return ShakeEffect(intensity=0.15, speed="slow")
            
        if eff_type == CameraEffectType.SHAKE_FAST:
            return ShakeEffect(intensity=0.5, speed="fast")

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
    """Intense shaking effect for dramatic moments.
    
    Supports variable speeds:
    - slow: wider, slower movement (tension)
    - normal: standard drama shake
    - fast: rapid, jittery movement (impact/shock)
    """
    
    def __init__(self, intensity: float = 0.3, speed: str = "normal") -> None:
        super().__init__(EffectConfig())
        self.intensity = intensity
        self.speed = speed

    def get_filter_string(
        self,
        input_label: str,
        output_label: str,
        **context: Any,
    ) -> str:
        # Use crop filter with random x/y variations
        # Requires input to be slightly larger or we crop in
        # We'll zoom in 10% to give room for shake
        
        # Shake parameters
        # Frequency (hz): How fast it shakes
        if self.speed == "slow":
            freq = 2  # Hz
            ampl_mult = 1.5  # Wider movement
        elif self.speed == "fast":
            freq = 15 # Hz
            ampl_mult = 0.8  # Tighter movement
        else: # normal
            freq = 5  # Hz
            ampl_mult = 1.0
            
        shake_px = int(50 * self.intensity * ampl_mult)
        
        # Uses sine wave for smoother movement (slow) or random for jitter (fast)
        if self.speed == "slow":
            # Smooth tension shake
            x_expr = f"(iw-ow)/2+sin(t*{freq})*{shake_px}"
            y_expr = f"(ih-oh)/2+cos(t*{freq}*0.8)*{shake_px}"
        else:
            # Random jitter shake
            x_expr = f"(iw-ow)/2+((random(1)-0.5)*{shake_px})"
            y_expr = f"(ih-oh)/2+((random(1)-0.5)*{shake_px})"
        
        return (
            f"{input_label}"
            f"crop=w=iw*0.9:h=ih*0.9:"
            f"x='{x_expr}':"
            f"y='{y_expr}':"
            f"exact=1"
            f",scale=1080:1920"  # Resize back to full res
            f"{output_label}"
        )

    def get_effect_name(self) -> str:
        return f"ShockShake({self.speed})"
