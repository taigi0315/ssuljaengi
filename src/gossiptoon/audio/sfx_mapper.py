"""Sound effects mapper for audio SFX system.

Maps visual SFX keywords to audio file paths for dramatic sound effects.
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class SFXMapper:
    """Maps visual SFX keywords to audio files."""

    # Base directory for SFX assets
    SFX_BASE_DIR = Path(__file__).parent.parent.parent.parent / "assets" / "sfx"

    # SFX Library mapping (keyword -> relative path)
    SFX_LIBRARY = {
        # Tension/Atmosphere (긴장감, 심각한 분위기)
        "DOOM": "tension/doom.wav",
        "DUN-DUN": "tension/dundun.wav",
        "LOOM": "tension/loom.wav",
        "RUMBLE": "tension/rumble.wav",
        
        # Action/Grip (무언가를 세게 쥘 때)
        "SQUEEZE": "action/squeeze.wav",
        "GRAB": "action/grab.wav",
        "GRIP": "action/grip.wav",
        "CLENCH": "action/clench.wav",
        "CRUSH": "action/crush.wav",
        
        # Impact/Presence (충격, 존재감)
        "BAM!": "impact/bam.wav",
        "WHAM!": "impact/wham.wav",
        "THUD": "impact/thud.wav",
        "TA-DA!": "impact/tada.wav",
    }

    def get_sfx_path(self, keyword: str) -> Optional[Path]:
        """Retrieve audio file path for SFX keyword.

        Args:
            keyword: SFX keyword (e.g., "BAM!", "DOOM")

        Returns:
            Absolute path to audio file, or None if not found or file doesn't exist
        """
        # Normalize keyword (handle case variations)
        keyword = keyword.upper().strip()

        # Look up relative path
        relative_path = self.SFX_LIBRARY.get(keyword)
        if not relative_path:
            logger.warning(f"SFX keyword '{keyword}' not found in library")
            return None

        # Construct absolute path
        sfx_path = self.SFX_BASE_DIR / relative_path

        # Check if file exists
        if not sfx_path.exists():
            logger.warning(f"SFX file not found: {sfx_path}")
            return None

        return sfx_path

    def list_available_sfx(self) -> list[str]:
        """List all available SFX keywords.

        Returns:
            List of valid SFX keywords
        """
        return list(self.SFX_LIBRARY.keys())

    def get_sfx_category(self, keyword: str) -> Optional[str]:
        """Get category for SFX keyword.

        Args:
            keyword: SFX keyword

        Returns:
            Category name ('tension', 'action', 'impact') or None
        """
        keyword = keyword.upper().strip()
        relative_path = self.SFX_LIBRARY.get(keyword)
        
        if relative_path:
            # Extract category from path (e.g., "tension/doom.wav" -> "tension")
            return relative_path.split("/")[0]
        
        return None
