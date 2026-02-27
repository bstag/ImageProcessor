
import unittest
from PIL import Image, ImageChops, ImageDraw, ImageFont
import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from processor import ImageProcessor

class TestWatermarkOptimization(unittest.TestCase):
    def setUp(self):
        # Create a base image
        self.width = 500
        self.height = 500
        self.base_image = Image.new('RGB', (self.width, self.height), color='white')
        self.watermark_text = "Bolt Optimized"

    def test_watermark_visual_change(self):
        """Test that watermarking actually modifies the image."""
        # Use a non-white color for watermark to ensure visibility against white bg
        watermarked = ImageProcessor.add_watermark(self.base_image, self.watermark_text, color=(0, 0, 0), opacity=255)

        # Should not be identical to original
        diff = ImageChops.difference(self.base_image, watermarked)
        self.assertTrue(diff.getbbox(), "Watermarked image appears identical to original")

    def test_watermark_position(self):
        """Test that watermark is in the bottom right quadrant."""
        # Create a large white image
        img = Image.new('RGB', (1000, 1000), color='white')

        # Add black watermark
        watermarked = ImageProcessor.add_watermark(img, "Test", color=(0, 0, 0), opacity=255)

        # Check pixels in top left (should be white)
        self.assertEqual(watermarked.getpixel((10, 10)), (255, 255, 255))

        # Check pixels in bottom right area (should have some non-white pixels due to text)
        # We don't know exact coordinates of text, but we know it's padded 20px from bottom right
        # Let's scan a small region in bottom right
        found_pixel = False
        for x in range(900, 1000):
            for y in range(900, 1000):
                if watermarked.getpixel((x, y)) != (255, 255, 255):
                    found_pixel = True
                    break
            if found_pixel:
                break

        self.assertTrue(found_pixel, "No watermark pixels found in bottom-right quadrant")

    def test_watermark_modes(self):
        """Test watermarking on different image modes."""
        modes = ['RGB', 'RGBA', 'L']
        for mode in modes:
            img = Image.new(mode, (200, 200), color=128 if mode == 'L' else (128, 128, 128))

            # Should not raise exception
            watermarked = ImageProcessor.add_watermark(img, self.watermark_text)

            self.assertEqual(watermarked.mode, mode)
            self.assertIsInstance(watermarked, Image.Image)

    def test_empty_watermark(self):
        """Test that empty text returns original image (or copy)."""
        res = ImageProcessor.add_watermark(self.base_image, "")
        # Should be visually identical
        diff = ImageChops.difference(self.base_image, res)
        self.assertIsNone(diff.getbbox())

    def test_long_watermark_error(self):
        """Test constraint for long watermark."""
        long_text = "A" * 1001
        with self.assertRaises(ValueError):
            ImageProcessor.add_watermark(self.base_image, long_text)

    def test_immutability_simulation(self):
        """
        Verify that the original image object passed in is not modified in-place
        if it wasn't RGBA (since we convert).
        If it WAS RGBA, we added a .copy() in the optimization to preserve this behavior.
        """
        # Case 1: RGB (converted inside)
        img_rgb = Image.new('RGB', (100, 100), color='white')
        original_pixel = img_rgb.getpixel((90, 90))

        _ = ImageProcessor.add_watermark(img_rgb, "Test", color=(0,0,0), opacity=255)

        # Original should still be white at potential text location
        self.assertEqual(img_rgb.getpixel((90, 90)), original_pixel)

        # Case 2: RGBA (was modified in place before optimization if not careful)
        img_rgba = Image.new('RGBA', (100, 100), color=(255, 255, 255, 255))
        original_pixel_rgba = img_rgba.getpixel((90, 90))

        _ = ImageProcessor.add_watermark(img_rgba, "Test", color=(0,0,0), opacity=255)

        self.assertEqual(img_rgba.getpixel((90, 90)), original_pixel_rgba)

if __name__ == '__main__':
    unittest.main()
