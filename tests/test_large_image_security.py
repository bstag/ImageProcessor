import unittest
from unittest.mock import MagicMock, patch
from src.tasks import process_image_task
from src.processor import ImageProcessor

class TestLargeImageSecurity(unittest.TestCase):
    @patch('src.tasks.Image.open')
    def test_large_image_processing_prevention(self, mock_open):
        """
        Test that images exceeding MAX_IMAGE_DIMENSION are rejected immediately.
        """
        # Mock an image with dimensions larger than allowed
        large_width = ImageProcessor.MAX_IMAGE_DIMENSION + 1
        large_height = 100

        mock_image = MagicMock()
        mock_image.size = (large_width, large_height)
        mock_image.width = large_width
        mock_image.height = large_height
        mock_image.format = 'PNG'  # Ensure it passes the format check
        mock_image.copy.return_value = mock_image  # copy() returns the same mock

        # When Image.open is called, return our mock image
        mock_open.return_value = mock_image

        # Setup config
        config = {
            'resize_type': 'None',
            'output_format': 'JPEG'
        }

        # Call process_image_task
        result = process_image_task(b'fake_content', config)

        # We expect failure due to dimension check
        self.assertFalse(result['success'], "Should have failed due to large image dimensions")
        self.assertIn("exceed maximum allowed size", result['error'])

if __name__ == '__main__':
    unittest.main()
