import unittest
from PIL import Image
import io
import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from processor import ImageProcessor

class TestImageProcessor(unittest.TestCase):
    def setUp(self):
        # Create a dummy image
        self.img = Image.new('RGB', (100, 100), color='red')
    
    def test_resize_percentage(self):
        resized = ImageProcessor.resize_image(self.img, percentage=50)
        self.assertEqual(resized.size, (50, 50))

    def test_resize_fixed(self):
        resized = ImageProcessor.resize_image(self.img, width=50, height=20, maintain_aspect_ratio=False)
        self.assertEqual(resized.size, (50, 20))

    def test_resize_aspect_ratio(self):
        resized = ImageProcessor.resize_image(self.img, width=50, maintain_aspect_ratio=True)
        # 100x100 -> width 50 -> height should be 50
        self.assertEqual(resized.size, (50, 50))

    def test_save_webp(self):
        output = ImageProcessor.process_and_save(self.img, 'WEBP')
        output.seek(0)
        img_loaded = Image.open(output)
        self.assertEqual(img_loaded.format, 'WEBP')

    def test_transforms_rotate(self):
        # Create a rectangular image to test rotation dimensions
        img = Image.new('RGB', (100, 50), color='blue')
        rotated = ImageProcessor.apply_transforms(img, rotate=90)
        self.assertEqual(rotated.size, (50, 100))

    def test_transforms_grayscale(self):
        gray = ImageProcessor.apply_transforms(self.img, grayscale=True)
        # We convert back to RGB in the function, but visually it should be gray
        # Check if R=G=B (grayscale property)
        pixel = gray.getpixel((0,0))
        self.assertEqual(pixel[0], pixel[1])
        self.assertEqual(pixel[1], pixel[2])

    def test_enhancements_run(self):
        # Just ensure it runs without error, verifying visual output programmatically is hard
        enhanced = ImageProcessor.apply_enhancements(self.img, brightness=1.5, contrast=0.5)
        self.assertIsInstance(enhanced, Image.Image)

if __name__ == '__main__':
    unittest.main()
