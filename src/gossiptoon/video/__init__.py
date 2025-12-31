"""Video assembly module for GossipToon.

Handles FFmpeg-based video rendering with modular effects.
"""

from gossiptoon.video.assembler import VideoAssembler
from gossiptoon.video.ffmpeg_builder import FFmpegBuilder, FFmpegCommand, VideoSegment

__all__ = [
    "VideoAssembler",
    "FFmpegBuilder",
    "FFmpegCommand",
    "VideoSegment",
]
