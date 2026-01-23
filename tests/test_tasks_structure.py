import unittest
from PIL import Image
import io
import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from tasks import process_image_task

class TestTasksStructure(unittest.TestCase):
    def test_process_image_task_structure(self):
        # Create a dummy image
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        content = img_bytes.getvalue()

        config = {
            'output_format': 'JPEG',
            'extract_colors': True
        }

        result = process_image_task(content, config)

        self.assertTrue(result['success'])

        # Verify keys
        self.assertIn('original_size', result)
        self.assertIn('original_dimensions', result)
        self.assertIn('processed_size', result)
        self.assertIn('data', result)
        self.assertIn('has_transparency', result)
        self.assertIn('dominant_colors', result)

        # Verify original_image is NOT present
        self.assertNotIn('original_image', result, "original_image should not be returned to save memory")

        # Verify content types
        self.assertIsInstance(result['data'], bytes)
        self.assertIsInstance(result['dominant_colors'], list)
        self.assertTrue(len(result['dominant_colors']) > 0)

if __name__ == '__main__':
    unittest.main()
