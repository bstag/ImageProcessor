import unittest
from src.processor import ImageProcessor

class TestSecurityConstants(unittest.TestCase):
    def test_max_image_dimension(self):
        """
        Verify that the MAX_IMAGE_DIMENSION constant is set to a safe limit:
        it must be greater than 0 and no more than 6000 pixels on any side
        to prevent Denial of Service (DoS) attacks via memory exhaustion.
        """
        self.assertGreater(
            ImageProcessor.MAX_IMAGE_DIMENSION,
            0,
            "MAX_IMAGE_DIMENSION should be greater than 0 to prevent DoS",
        )
        self.assertLessEqual(
            ImageProcessor.MAX_IMAGE_DIMENSION,
            6000,
            "MAX_IMAGE_DIMENSION should not exceed 6000 to prevent DoS",
        )

if __name__ == '__main__':
    unittest.main()
