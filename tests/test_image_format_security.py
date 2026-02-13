import unittest
from unittest.mock import patch, MagicMock
import io
from tasks import process_image_task

class TestImageFormatSecurity(unittest.TestCase):
    @patch('tasks.Image.open')
    def test_mpo_format_rejection(self, mock_open):
        """
        Verify that MPO format is rejected for security reasons.
        """
        # Setup mock image to look like an MPO file
        mock_image = MagicMock()
        mock_image.format = 'MPO'
        mock_image.width = 100
        mock_image.height = 100
        mock_image.size = (100, 100)
        mock_open.return_value = mock_image

        # Test processing with dummy bytes and config
        result = process_image_task(b'fake_mpo_bytes', {})

        # Verify it fails with specific security error
        self.assertFalse(result['success'])
        self.assertIn("Security violation: Image format 'MPO' is not allowed", result['error'])

    @patch('tasks.Image.open')
    @patch('tasks.ImageProcessor.process_and_save')
    def test_valid_formats_allowed(self, mock_save, mock_open):
        """
        Verify that standard formats like PNG are allowed.
        """
        # Setup mock image to look like a PNG file
        mock_image = MagicMock()
        mock_image.format = 'PNG'
        mock_image.width = 100
        mock_image.height = 100
        mock_image.size = (100, 100)
        mock_image.mode = 'RGB'
        mock_open.return_value = mock_image

        # Mock process_and_save to return dummy data
        mock_save.return_value = io.BytesIO(b'processed_png')

        # Test processing
        result = process_image_task(b'fake_png_bytes', {'output_format': 'PNG'})

        # Verify it succeeds
        self.assertTrue(result['success'])

if __name__ == '__main__':
    unittest.main()
