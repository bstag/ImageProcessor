import unittest
import os
from src.utils import get_unique_filename, get_safe_filename_stem, validate_upload_constraints

class MockFile:
    def __init__(self, size):
        self.size = size

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
        self.assertEqual(get_safe_filename_stem(".hidden"), "image")
        self.assertEqual(get_safe_filename_stem("..\\..\\etc\\passwd.jpg"), "passwd")
        self.assertEqual(get_safe_filename_stem("/etc/passwd.jpg"), "passwd")
        self.assertEqual(get_safe_filename_stem("malicious\0.jpg"), "malicious")
        self.assertEqual(get_safe_filename_stem(".."), "image")

    def test_validate_upload_constraints(self):
        """
        Test the upload constraints validation.
        """
        # Test Case 1: Valid uploads
        # 2 files, 1MB each (2MB total) -> Should pass
        files = [MockFile(1024*1024), MockFile(1024*1024)]
        valid, error = validate_upload_constraints(files, max_count=5, max_total_size_mb=10)
        self.assertTrue(valid)
        self.assertIsNone(error)

        # Test Case 2: Too many files
        # 6 files, limit 5 -> Should fail
        files = [MockFile(1) for _ in range(6)]
        valid, error = validate_upload_constraints(files, max_count=5, max_total_size_mb=10)
        self.assertFalse(valid)
        self.assertIn("Too many files", error)

        # Test Case 3: Total size too large
        # 1 file, 11MB -> Should fail
        files = [MockFile(11 * 1024 * 1024)]
        valid, error = validate_upload_constraints(files, max_count=5, max_total_size_mb=10)
        self.assertFalse(valid)
        self.assertIn("Total upload size", error)
        self.assertIn("exceeds limit", error)

        # Test Case 4: Boundary condition (Exact size)
        # 10MB -> Should pass
        files = [MockFile(10 * 1024 * 1024)]
        valid, error = validate_upload_constraints(files, max_count=5, max_total_size_mb=10)
        self.assertTrue(valid)
        self.assertIsNone(error)

if __name__ == '__main__':
    unittest.main()
