import unittest
import os
import sys
from unittest.mock import patch

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from utils import format_bytes, get_unique_filename, get_file_info

class TestUtils(unittest.TestCase):
    
    def test_format_bytes(self):
        self.assertEqual(format_bytes(500), "500.00 B")
        self.assertEqual(format_bytes(1024), "1.00 KB")
        self.assertEqual(format_bytes(1024 * 1024), "1.00 MB")
        self.assertEqual(format_bytes(1024 * 1024 * 1024), "1.00 GB")
        self.assertEqual(format_bytes(1536), "1.50 KB")
        # Test negative values
        self.assertEqual(format_bytes(-500), "-500.00 B")
        self.assertEqual(format_bytes(-1024), "-1.00 KB")
        self.assertEqual(format_bytes(-1536), "-1.50 KB")

    def test_get_unique_filename(self):
        output_dir = "output"
        original = "image.png"
        result = get_unique_filename(original, output_dir, suffix="test")
        
        # Check basic structure
        self.assertTrue(result.startswith(os.path.join(output_dir, "image_test_")))
        self.assertTrue(result.endswith(".png"))
        
        # Check that it contains a UUID-like part (8 chars)
        # format: output/image_test_XXXXXXXX.png
        filename = os.path.basename(result)
        parts = filename.split('_')
        self.assertEqual(len(parts), 3) # image, test, uuid.png
        self.assertEqual(len(parts[2].split('.')[0]), 8)

    @patch('os.path.getsize')
    def test_get_file_info(self, mock_getsize):
        mock_getsize.return_value = 2048 # 2 KB
        
        info = get_file_info("/path/to/test_image.jpg")
        
        self.assertEqual(info['name'], "test_image.jpg")
        self.assertEqual(info['size_bytes'], 2048)
        self.assertEqual(info['size_formatted'], "2.00 KB")

if __name__ == '__main__':
    unittest.main()
