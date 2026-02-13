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
        # 1. Create a "real" image with EXIF data in memory
        img = Image.new('RGB', (100, 100), color='red')
        exif = img.getexif()
        exif[271] = "TestMake"  # EXIF tag 271 represents the camera/scanner Make

        # Save to bytes to simulate a loaded file
        tmp = io.BytesIO()
        img.save(tmp, 'JPEG', exif=exif.tobytes())
        tmp.seek(0)

        loaded_img = Image.open(tmp)

        # 2. Call process_and_save with strip_metadata=True
        output = ImageProcessor.process_and_save(loaded_img, 'JPEG', strip_metadata=True)
        output.seek(0)

        # 3. Load the output and verify EXIF/metadata is absent
        result_img = Image.open(output)

        # Check getexif
        result_exif = result_img.getexif()
        self.assertIsNone(result_exif.get(271))

        # Check info dictionary for 'exif' key (raw bytes)
        self.assertFalse(result_img.info.get('exif'))

    def test_metadata_preserve(self):
        # 1. Create a "real" image with EXIF data in memory
        img = Image.new('RGB', (100, 100), color='red')
        exif = img.getexif()
        exif[271] = "TestMake"  # EXIF tag 271 represents the camera/scanner Make

        # Save to bytes to simulate a loaded file
        tmp = io.BytesIO()
        img.save(tmp, 'JPEG', exif=exif.tobytes())
        tmp.seek(0)

        loaded_img = Image.open(tmp)

        # 2. Call process_and_save with strip_metadata=False
        output = ImageProcessor.process_and_save(loaded_img, 'JPEG', strip_metadata=False)
        output.seek(0)

        # 3. Load the output and verify EXIF/metadata is preserved
        result_img = Image.open(output)

        # Check getexif
        result_exif = result_img.getexif()
        self.assertEqual(result_exif.get(271), "TestMake")

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

    def test_get_dominant_colors(self):
        # Create an image with clear dominant colors
        img = Image.new('RGB', (100, 100), color='red')
        # Add a blue square
        for x in range(20):
            for y in range(20):
                img.putpixel((x, y), (0, 0, 255))

        colors = ImageProcessor.get_dominant_colors(img, num_colors=2)
        self.assertTrue(len(colors) > 0)
        # Should contain red (#ff0000) and blue (#0000ff)
        # Note: Quantization might alter exact hex values slightly depending on algorithm,
        # but for pure colors it should be exact.
        self.assertIn('#ff0000', colors)
        self.assertIn('#0000ff', colors)

    def test_watermark_length_limit(self):
        """
        Test that add_watermark raises ValueError for excessively long strings.
        """
        img = Image.new('RGB', (100, 100), color='white')
        long_text = "A" * 1001
        with self.assertRaises(ValueError) as cm:
            ImageProcessor.add_watermark(img, long_text)
        self.assertIn("Watermark text exceeds maximum allowed length", str(cm.exception))

    def test_combined_enhancements_logic(self):
        # Create a gray image
        img = Image.new('RGB', (100, 100), color=(100, 100, 100))

        # Apply combined
        combined = ImageProcessor.apply_enhancements(img, brightness=1.2, contrast=1.3)

        # Apply sequential manually
        from PIL import ImageEnhance
        seq = ImageEnhance.Brightness(img).enhance(1.2)
        seq = ImageEnhance.Contrast(seq).enhance(1.3)

        # Check if pixels are close (allow small rounding differences)
        c_pixel = combined.getpixel((50, 50))
        s_pixel = seq.getpixel((50, 50))

        # Differences should be very small (<= 1) due to integer arithmetic order
        diff = abs(c_pixel[0] - s_pixel[0])
        self.assertLessEqual(diff, 1)

if __name__ == '__main__':
    unittest.main()
