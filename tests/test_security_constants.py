import unittest
from src.processor import ImageProcessor

class TestSecurityConstants(unittest.TestCase):
    def test_max_image_dimension(self):
        """
        Verify that the MAX_IMAGE_DIMENSION constant is set to a safe limit (6000)
        to prevent Denial of Service (DoS) attacks via memory exhaustion.
        """
        self.assertEqual(ImageProcessor.MAX_IMAGE_DIMENSION, 6000, "MAX_IMAGE_DIMENSION should be 6000 to prevent DoS")

if __name__ == '__main__':
    unittest.main()
