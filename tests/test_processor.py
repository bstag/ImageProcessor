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

    def test_transforms_flip(self):
        # Create an image with distinct quadrants to test flipping
        img = Image.new('RGB', (2, 2))
        img.putpixel((0, 0), (255, 0, 0)) # Top-Left: Red
        img.putpixel((1, 0), (0, 255, 0)) # Top-Right: Green
        
        # Horizontal Flip
        flipped_h = ImageProcessor.apply_transforms(img, flip_horizontal=True)
        self.assertEqual(flipped_h.getpixel((0, 0)), (0, 255, 0)) # Should be Green now
        
        # Vertical Flip
        flipped_v = ImageProcessor.apply_transforms(img, flip_vertical=True)
        # Original (0,0) Red should move to (0,1)
        self.assertEqual(flipped_v.getpixel((0, 1)), (255, 0, 0))

    def test_crop_image(self):
        # 100x100 image
        cropped = ImageProcessor.crop_image(self.img, 10, 10, 90, 90)
        self.assertEqual(cropped.size, (80, 80))

    def test_center_crop_to_aspect(self):
        img = Image.new('RGB', (200, 100), color='red')
        cropped = ImageProcessor.center_crop_to_aspect(img, 1, 1)
        self.assertEqual(cropped.size, (100, 100))

    def test_transforms_grayscale(self):
        gray = ImageProcessor.apply_transforms(self.img, grayscale=True)
        # We convert back to RGB in the function, but visually it should be gray
        # Check if R=G=B (grayscale property)
        pixel = gray.getpixel((0,0))
        self.assertEqual(pixel[0], pixel[1])
        self.assertEqual(pixel[1], pixel[2])

    def test_save_rgba_to_jpeg(self):
        # Create RGBA image
        rgba = Image.new('RGBA', (100, 100), (255, 0, 0, 128))
        # Saving as JPEG should trigger conversion to RGB
        output = ImageProcessor.process_and_save(rgba, 'JPEG')
        output.seek(0)
        img_loaded = Image.open(output)
        self.assertEqual(img_loaded.mode, 'RGB')
        self.assertEqual(img_loaded.format, 'JPEG')

    def test_metadata_strip(self):
        # Create image with dummy info (hard to inject real EXIF without extra libs, 
        # but we can verify the function runs and returns a valid image without error)
        # A more robust test would require loading an image with known EXIF.
        # For now, we verify the output is a clean new image.
        output = ImageProcessor.process_and_save(self.img, 'PNG', strip_metadata=True)
        output.seek(0)
        self.assertTrue(output.getbuffer().nbytes > 0)
        
    def test_enhancements_effect(self):
        # Create a gray image
        img = Image.new('RGB', (100, 100), color=(100, 100, 100))
        
        # Brightness 2.0 should make it lighter
        bright = ImageProcessor.apply_enhancements(img, brightness=2.0)
        pixel = bright.getpixel((50, 50))
        self.assertTrue(pixel[0] > 100)
        
        # Brightness 0.5 should make it darker
        dark = ImageProcessor.apply_enhancements(img, brightness=0.5)
        pixel_dark = dark.getpixel((50, 50))
        self.assertTrue(pixel_dark[0] < 100)

    def test_enhancements_run(self):
        # Just ensure it runs without error, verifying visual output programmatically is hard
        enhanced = ImageProcessor.apply_enhancements(self.img, brightness=1.5, contrast=0.5)
        self.assertIsInstance(enhanced, Image.Image)

if __name__ == '__main__':
    unittest.main()
