"""Video effects module for GossipToon.

Provides modular, composable FFmpeg effects.
"""

from gossiptoon.video.effects.base import CompositeEffect, Effect, EffectConfig
from gossiptoon.video.effects.captions import CaptionConfig, CaptionEffect
from gossiptoon.video.effects.ken_burns import KenBurnsConfig, KenBurnsEffect

__all__ = [
    "Effect",
    "EffectConfig",
    "CompositeEffect",
    "KenBurnsEffect",
    "KenBurnsConfig",
    "CaptionEffect",
    "CaptionConfig",
]
