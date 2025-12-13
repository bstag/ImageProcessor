# Test Coverage Expansion Plan

I have analyzed the codebase and identified several gaps in test coverage. The current tests cover basic resizing and saving, but miss edge cases, helper functions, and specific transformations.

## 1. Create `tests/test_utils.py`
Add unit tests for `src/utils.py`:
- `test_format_bytes`: Verify correct formatting for bytes, KB, MB, GB.
- `test_get_unique_filename`: Verify structure of generated filenames (uuid presence, suffix).
- `test_get_file_info`: Verify it extracts name and size correctly (mocking `os.path.getsize`).

## 2. Update `tests/test_processor.py`
Add the following test cases:
- **Cropping**: Test `crop_image` with specific coordinates.
- **Flipping**: Test `apply_transforms` for horizontal and vertical flips.
- **Format Conversion**: Test saving RGBA image as JPEG (verifying automatic conversion to RGB).
- **Metadata**: Test `process_and_save` with `strip_metadata=True` vs `False` (checking if data size differs or if EXIF is gone).
- **Enhancements**: stronger verification for `apply_enhancements` (check that pixel data actually changes).

## 3. Execution
- Create the new test file.
- Update the existing test file.
- Run all tests to ensure 100% pass rate.
