import unittest
import os
from src.utils import get_unique_filename, get_safe_filename_stem

class TestSecurity(unittest.TestCase):
    def test_filename_sanitization_logic(self):
        """
        Verify the logic used in app.py for filename sanitization by testing the utility function directly.
        """

        # Simulate the inputs
        malicious_filename = "../../../etc/passwd.jpg"

        # Test the utility function
        name_stem = get_safe_filename_stem(malicious_filename)

        # Assertions
        self.assertNotIn("..", name_stem)
        self.assertNotIn("/", name_stem)
        self.assertEqual(name_stem, "passwd")

    def test_filename_sanitization_edge_cases(self):
        """
        Test edge cases for filename sanitization.
        """
        self.assertEqual(get_safe_filename_stem("image"), "image")
        self.assertEqual(get_safe_filename_stem("image.png"), "image")
        self.assertEqual(get_safe_filename_stem("path/to/image.png"), "image")
        self.assertEqual(get_safe_filename_stem(""), "image")
        self.assertEqual(get_safe_filename_stem(".hidden"), "") # .hidden -> split('.') -> ['', 'hidden'] -> [0] = ''

if __name__ == '__main__':
    unittest.main()
