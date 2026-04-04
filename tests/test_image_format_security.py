import unittest
import io
from PIL import Image
from unittest.mock import patch, MagicMock
from src.tasks import process_image_task

class TestImageFormatSecurity(unittest.TestCase):
    def test_allowed_format(self):
        """Test that an allowed format (PNG) is processed correctly."""
        img = Image.new('RGB', (10, 10), color='red')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        file_content = img_byte_arr.getvalue()

        config = {'output_format': 'PNG'}
        result = process_image_task(file_content, config)

        self.assertTrue(result['success'], f"Valid PNG should be processed. Error: {result.get('error')}")

    def test_blocked_format(self):
        """Test that a blocked format (GIF) is rejected directly by Image.open restricted formats."""
        img = Image.new('RGB', (10, 10), color='red')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='GIF')
        file_content = img_byte_arr.getvalue()

        config = {'output_format': 'PNG'}

        result = process_image_task(file_content, config)

        self.assertFalse(result['success'], "Blocked format (GIF) should fail")
        # Since Image.open catches it, it raises UnidentifiedImageError which returns standard invalid msg
        self.assertEqual("Invalid or corrupt image file.", result['error'])

    def test_blocked_format_renamed(self):
        """
        Simulate a 'polyglot' or renamed file attack.
        User uploads 'image.png' which is actually a TIFF.
        """
        img = Image.new('RGB', (10, 10), color='blue')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='TIFF')
        file_content = img_byte_arr.getvalue()

        config = {'output_format': 'PNG'}
        result = process_image_task(file_content, config)

        self.assertFalse(result['success'], "Renamed blocked format (TIFF) should fail")
        self.assertEqual("Invalid or corrupt image file.", result['error'])

    @patch('src.tasks.Image.open')
    def test_blocked_format_mpo(self, mock_open):
        """
        Test that MPO format is rejected.
        We mock Image.open to raise an exception because Pillow might not support creating/saving MPO files easily.
        """
        # Since we pass formats parameter to Image.open, an invalid format should trigger UnidentifiedImageError
        from PIL import UnidentifiedImageError
        mock_open.side_effect = UnidentifiedImageError("cannot identify image file")

        # Pass dummy content; Image.open is mocked so it won't read it
        file_content = b'dummy content'
        config = {'output_format': 'PNG'}

        result = process_image_task(file_content, config)

        self.assertFalse(result['success'], "MPO format should be blocked")
        self.assertEqual("Invalid or corrupt image file.", result['error'])

if __name__ == '__main__':
    unittest.main()
