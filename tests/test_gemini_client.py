import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from gemini_client import process_audio

class TestGeminiClient(unittest.TestCase):

    @patch('gemini_client.genai')
    @patch('gemini_client.os.getenv')
    def test_process_audio_success(self, mock_getenv, mock_genai):
        # Mock API Key
        mock_getenv.return_value = "fake_key"

        # Mock File Upload
        mock_file = MagicMock()
        mock_file.state.name = "ACTIVE"
        mock_file.name = "files/123"
        mock_genai.upload_file.return_value = mock_file
        mock_genai.get_file.return_value = mock_file

        # Mock Model Generation
        mock_model = MagicMock()
        mock_result = MagicMock()
        mock_result.text = '{"titular": "Test Title", "resumen": "Test Summary", "puntos_clave": "- Point 1"}'
        mock_model.generate_content.return_value = mock_result
        mock_genai.GenerativeModel.return_value = mock_model

        # Run function
        result = process_audio("dummy.mp3")

        # Assertions
        self.assertEqual(result["titular"], "Test Title")
        mock_genai.configure.assert_called_with(api_key="fake_key")
        mock_genai.upload_file.assert_called_with("dummy.mp3")
        mock_model.generate_content.assert_called()
        mock_file.delete.assert_called()

    @patch('gemini_client.genai')
    @patch('gemini_client.os.getenv')
    def test_process_audio_processing_wait(self, mock_getenv, mock_genai):
        # Mock API Key
        mock_getenv.return_value = "fake_key"

        # Mock File Upload with state transition
        mock_file_processing = MagicMock()
        mock_file_processing.state.name = "PROCESSING"
        mock_file_processing.name = "files/123"

        mock_file_active = MagicMock()
        mock_file_active.state.name = "ACTIVE"
        mock_file_active.name = "files/123"

        mock_genai.upload_file.return_value = mock_file_processing
        # First call returns processing, second returns active
        mock_genai.get_file.side_effect = [mock_file_active]

        # Mock Model
        mock_model = MagicMock()
        mock_result = MagicMock()
        mock_result.text = '{}'
        mock_model.generate_content.return_value = mock_result
        mock_genai.GenerativeModel.return_value = mock_model

        # Patch sleep to speed up test
        with patch('time.sleep'):
             process_audio("dummy.mp3")

        # Check that get_file was called to check status
        mock_genai.get_file.assert_called_with("files/123")

if __name__ == '__main__':
    unittest.main()
