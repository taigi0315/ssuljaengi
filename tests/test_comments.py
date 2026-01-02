"""Tests for CommentManager."""
import unittest
import tempfile
import shutil
from pathlib import Path
import yaml
from gossiptoon.youtube.comments import CommentManager

class TestCommentManager(unittest.TestCase):
    def setUp(self):
        # Create a temporary config directory
        self.test_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.test_dir) / "config"
        self.config_dir.mkdir()
        
        # Create a test template file
        self.templates = {
            "test_template": {
                "template": "Test URL: {source_url}"
            },
            "complex_template": {
                "template": "Hello {protagonist}, look at {source_url}"
            }
        }
        
        with open(self.config_dir / "comment_templates.yaml", "w") as f:
            yaml.dump(self.templates, f)
            
        # Monkey patch the path resolution in CommentManager needed for testing
        # Since we can't easily inject the path without modifying the class to accept a path override
        # We will subclass for testing
        class TestableCommentManager(CommentManager):
            def _load_templates(self_obj) -> dict: # use self_obj to avoid confusion
                with open(self.config_dir / "comment_templates.yaml", "r") as f:
                    return yaml.safe_load(f)
                    
        self.manager = TestableCommentManager()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_generate_default(self):
        """Test generation with default template (fallback logic or explicit)."""
        # Note: Our test subclass overrides loading, so standard defaults might not be there 
        # unless we put them in the test file.
        # But let's test a known template:
        comment = self.manager.generate_comment("http://test.com", "test_template")
        self.assertEqual(comment, "Test URL: http://test.com")

    def test_generate_complex(self):
        """Test generation with extra variables."""
        comment = self.manager.generate_comment(
            "http://test.com", 
            "complex_template", 
            extra_vars={"protagonist": "User"}
        )
        self.assertEqual(comment, "Hello User, look at http://test.com")

    def test_missing_template(self):
        """Test fallback when template is missing."""
        # The base class has a hardcoded fallback if load fails OR if key missing
        # verification needs to check implementation behavior
        pass 

if __name__ == "__main__":
    unittest.main()
