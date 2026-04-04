import unittest
from unittest.mock import MagicMock, patch
from PIL import UnidentifiedImageError
from src.tasks import process_image_task, SecurityError
from src.processor import ImageProcessor

class TestErrorHandling(unittest.TestCase):

    @patch('src.tasks.Image.open')
    def test_security_error_invalid_format(self, mock_open):
        """Test that SecurityError is raised and handled for invalid formats."""
        # Setup mock image opening to fail with UnidentifiedImageError
        from PIL import UnidentifiedImageError
        mock_open.side_effect = UnidentifiedImageError("cannot identify image file")

        # Call the function
        result = process_image_task(b'fake_content', {})

        # Verify
        self.assertFalse(result['success'])
        self.assertEqual("Invalid or corrupt image file.", result['error'])

    @patch('src.tasks.Image.open')
    def test_security_error_invalid_dimensions(self, mock_open):
        """Test that SecurityError is raised and handled for invalid dimensions."""
        # Setup mock image
        mock_image = MagicMock()
        mock_image.format = 'PNG'
        mock_image.width = ImageProcessor.MAX_IMAGE_DIMENSION + 1
        mock_image.height = 100
        mock_open.return_value = mock_image

        # Call the function
        result = process_image_task(b'fake_content', {})

        # Verify
        self.assertFalse(result['success'])
        self.assertIn("Image dimensions", result['error'])
        self.assertIn("exceed maximum allowed size", result['error'])

    @patch('src.tasks.Image.open')
    def test_unidentified_image_error(self, mock_open):
        """Test that UnidentifiedImageError is handled gracefully."""
        # Setup mock to raise exception
        mock_open.side_effect = UnidentifiedImageError("Cannot identify image file")

        # Call the function
        result = process_image_task(b'invalid_content', {})

        # Verify
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], "Invalid or corrupt image file.")

    @patch('src.tasks.Image.open')
    def test_generic_exception_masking(self, mock_open):
        """Test that generic exceptions are masked."""
        # Setup mock to raise a generic exception
        mock_open.side_effect = ValueError("Some internal library error with path /usr/local/secret")

        # Call the function
        result = process_image_task(b'content', {})

        # Verify
        self.assertFalse(result['success'])
        # The user should NOT see the internal details
        self.assertEqual(result['error'], "An internal error occurred during processing.")
        self.assertNotIn("secret", result['error'])

if __name__ == '__main__':
    unittest.main()
