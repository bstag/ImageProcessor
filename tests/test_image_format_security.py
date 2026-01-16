import unittest
import io
from PIL import Image
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
        """Test that a blocked format (GIF) is rejected, even if it could be opened by Pillow."""
        img = Image.new('RGB', (10, 10), color='red')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='GIF')
        file_content = img_byte_arr.getvalue()

        config = {'output_format': 'PNG'}

        result = process_image_task(file_content, config)

        self.assertFalse(result['success'], "Blocked format (GIF) should fail")
        self.assertIn("Security violation", result['error'])
        self.assertIn("GIF", result['error'])

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
        self.assertIn("Security violation", result['error'])
        self.assertIn("TIFF", result['error'])

if __name__ == '__main__':
    unittest.main()
