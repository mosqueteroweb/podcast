import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from ivoox_uploader import upload_episode

class TestIvooxUploader(unittest.TestCase):

    @patch('ivoox_uploader.sync_playwright')
    @patch('ivoox_uploader.os.getenv')
    def test_upload_episode(self, mock_getenv, mock_playwright):
        # Setup Env
        def getenv_side_effect(key, default=None):
            if key == "WEB_USER": return "user"
            if key == "WEB_PASSWORD": return "pass"
            if key == "WEB_URL": return "http://login"
            return default
        mock_getenv.side_effect = getenv_side_effect

        # Mock Playwright
        mock_p = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()

        mock_playwright.return_value.__enter__.return_value = mock_p
        mock_p.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        # Mock Elements
        mock_page.locator.return_value.is_visible.return_value = True
        mock_page.is_visible.return_value = True

        # Run
        metadata = {
            "titular": "Title",
            "resumen": "Summary",
            "puntos_clave": "- Point 1"
        }
        upload_episode("test.mp3", metadata)

        # Asserts
        mock_page.goto.assert_called_with("http://login")
        mock_page.fill.assert_any_call("input#email-field", "user")
        mock_page.fill.assert_any_call("input[type='password']", "pass")
        mock_page.click.assert_called()

        # Check upload flow calls
        # We can't be too specific because of the "try/except" blocks and logic branches,
        # but we can check if it tried to find the upload button.

if __name__ == '__main__':
    unittest.main()
