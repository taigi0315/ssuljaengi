
import unittest
from pathlib import Path
from unittest.mock import MagicMock
from PIL import Image

from gossiptoon.visual.director import VisualDirector
from gossiptoon.core.config import ConfigManager

class TestPanelLayout(unittest.TestCase):
    def setUp(self):
        self.output_dir = Path("tests/output/panels")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create dummy panel images
        self.panel_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
        self.panel_paths = []
        for i, color in enumerate(self.panel_colors):
            img = Image.new('RGB', (1080, 1920), color)
            path = self.output_dir / f"panel_{i}.png"
            img.save(path)
            self.panel_paths.append(path)
            
        self.config = MagicMock(spec=ConfigManager)
        self.config.api = MagicMock()
        self.config.api.google_api_key = "dummy_key"
        self.config.images_dir = self.output_dir
        
        # Mock ImageClient to avoid API calls
        self.image_client = MagicMock()
        self.image_client.get_model_name.return_value = "mock-model"
        
        self.director = VisualDirector(self.config, image_client=self.image_client)

    def test_stitch_3_panels(self):
        output_path = self.output_dir / "stitched_3.png"
        panels = self.panel_paths[:3]
        
        result_path = self.director._stitch_panels(panels, "template_a_3panel", output_path)
        
        self.assertTrue(result_path.exists())
        img = Image.open(result_path)
        self.assertEqual(img.size, (1080, 1920))
        
        # Check if colors are roughly present at expected positions
        # Top panel (Red)
        self.assertEqual(img.getpixel((540, 100)), (255, 0, 0))
        # Middle panel (Green) - approx center
        self.assertEqual(img.getpixel((540, 960)), (0, 255, 0))
        # Bottom panel (Blue)
        self.assertEqual(img.getpixel((540, 1800)), (0, 0, 255))
        
    def test_stitch_4_panels(self):
        output_path = self.output_dir / "stitched_4.png"
        panels = self.panel_paths[:4]
        
        result_path = self.director._stitch_panels(panels, "template_b_4panel", output_path)
        
        self.assertTrue(result_path.exists())
        img = Image.open(result_path)
        self.assertEqual(img.size, (1080, 1920))

if __name__ == '__main__':
    unittest.main()
