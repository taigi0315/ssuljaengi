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
    # Note: Files are .mp3 format
    SFX_LIBRARY = {
        # Tension/Atmosphere (긴장감, 심각한 분위기)
        "DOOM": "tension/doom.mp3",
        "DUN-DUN": "tension/dundun.mp3",
        "LOOM": "tension/loom.mp3",
        "RUMBLE": "tension/rumble.mp3",
        
        # Action/Grip (무언가를 세게 쥘 때)
        "SQUEEZE": "action/squeeze.mp3",
        "GRAB": "action/grab.mp3",
        "GRIP": "action/grip.mp3",
        "CLENCH": "action/clench.mp3",
        "CRUSH": "action/crush.mp3",
        
        # Impact/Presence (충격, 존재감)
        "BAM!": "impact/bam.mp3",
        "WHAM!": "impact/wham.mp3",
        "THUD": "impact/thud.mp3",
        "TA-DA!": "impact/tadan.mp3",  # Note: file is tadan.mp3
    }
    
    # SFX Descriptions (for AI selection guidance)
    SFX_DESCRIPTIONS = {
        # Tension/Atmosphere (~3s, Sub-bass + Cinematic)
        "DOOM": "Massive orchestral brass hit with heavy sub-bass drop, dark ominous reveal (Hans Zimmer style)",
        "DUN-DUN": "Double orchestral hit, shocking realization, TV drama suspense accent",
        "LOOM": "Dark ambient drone swelling up, menacing low-frequency hum, horror atmosphere",
        "RUMBLE": "Deep earthquake rumble, heavy rocks grinding, disaster atmosphere",
        
        # Action/Grip (~3s, Foley + Close-up texture)
        "SQUEEZE": "Wet rubber/leather twisted hard, high-pitched friction squeak, stress ball",
        "GRAB": "Fast air whoosh + solid fabric slap, aggressive clothing grab",
        "GRIP": "Leather glove tightening, creaking fabric, slow heavy tension",
        "CLENCH": "Fabric fibers tearing, knuckles cracking, intense muscle tension",
        "CRUSH": "Loud crunching, dry wood splintering, destroying hard object",
        
        # Impact/Presence (~3s, Transient + Decay)
        "BAM!": "Powerful superhero punch, explosive snare drum, cartoon combat hit",
        "WHAM!": "Heavy metallic collision, concrete wall impact, industrial crash",
        "THUD": "Heavy dead weight falling on wood, body fall, dull muted impact",
        "TA-DA!": "Magical success fanfare, bright brass, rising harp, victory reveal",
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
            # Extract category from path (e.g., "tension/doom.mp3" -> "tension")
            return relative_path.split("/")[0]
        
        return None
    
    def get_sfx_description(self, keyword: str) -> Optional[str]:
        """Get detailed description for SFX keyword.

        Args:
            keyword: SFX keyword

        Returns:
            Description string or None
        """
        keyword = keyword.upper().strip()
        return self.SFX_DESCRIPTIONS.get(keyword)
