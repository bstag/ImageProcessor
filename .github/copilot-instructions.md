# GitHub Copilot Instructions for ImageProcessor

## Project Overview
ImageProcessor is a powerful, user-friendly web application built with **Streamlit** and **Pillow (PIL)** for batch image processing, editing, and web optimization. The application supports various image formats including WebP, AVIF, JPEG, PNG, BMP, and HEIF.

## Technology Stack
- **Language**: Python 3.x
- **Web Framework**: Streamlit
- **Image Processing**: Pillow (PIL), pillow-avif-plugin, pillow-heif
- **Testing**: Python unittest framework

## Project Structure
```
ImageProcessor/
├── .github/              # GitHub configuration and Copilot instructions
├── src/                  # Source code
│   ├── app.py           # Main Streamlit application UI
│   ├── processor.py     # Core image processing logic (PIL wrapper)
│   ├── utils.py         # Helper functions (formatting, file handling)
│   └── tasks.py         # Additional task utilities
├── tests/               # Unit tests
│   ├── test_processor.py  # Tests for image processing logic
│   ├── test_utils.py      # Tests for utility functions
│   └── test_security.py   # Security-related tests
├── docs/                # Documentation files
├── requirements.txt     # Python dependencies
└── README.md           # Project documentation
```

## Setting Up the Development Environment

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run the Application
```bash
streamlit run src/app.py
```
The app will be available at `http://localhost:8501`.

## Testing

### Run All Tests
```bash
python -m unittest discover tests
```

### Run Specific Test File
```bash
python -m unittest tests.test_processor
python -m unittest tests.test_utils
python -m unittest tests.test_security
```

### Before Running Tests
Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

## Coding Standards and Best Practices

### Python Style
- Follow PEP 8 style guidelines for Python code
- Use clear, descriptive variable and function names
- Add docstrings for classes and functions that explain their purpose
- Keep functions focused and modular

### Image Processing
- Always use Pillow (PIL) for image operations
- Handle transparency detection and preservation carefully
- Use `ImageEnhance` for brightness, contrast, saturation, and sharpness adjustments
- Apply Lanczos resampling for high-quality image resizing
- Strip EXIF metadata when optimizing for web to reduce file size

### File Handling
- Use `io.BytesIO` for in-memory image processing
- Sanitize filenames to prevent security issues
- Use UUIDs for unique filename generation when needed
- Validate file extensions and MIME types

### Error Handling
- Always validate user inputs (dimensions, percentages, quality values)
- Handle edge cases (zero dimensions, invalid formats)
- Provide meaningful error messages to users
- Use try-except blocks for file I/O and image processing operations

### Security Considerations
- Sanitize all user-provided filenames to prevent path traversal attacks
- Validate file types before processing
- Strip potentially harmful metadata from uploaded images
- Be cautious with user-provided dimensions and parameters

## Dependencies Management
- All Python dependencies are listed in `requirements.txt`
- When adding new dependencies, update `requirements.txt`
- Use stable, well-maintained packages
- Specify version constraints when necessary for compatibility

## Streamlit-Specific Guidelines
- Use Streamlit's session state for managing application state
- Organize UI components logically with sections and columns
- Provide clear user feedback for operations (success/error messages)
- Use progress bars for batch operations
- Maintain responsive UI with appropriate widget choices

## Testing Guidelines
- Write unit tests for all core image processing functions
- Test edge cases (empty images, invalid dimensions, unsupported formats)
- Include security tests for filename sanitization and input validation
- Use setUp methods to create test fixtures (sample images)
- Verify both successful operations and error handling

## Common Operations

### Adding a New Image Processing Feature
1. Add the processing logic to `processor.py` as a static method
2. Create corresponding tests in `tests/test_processor.py`
3. Add UI controls in `app.py` if needed
4. Update documentation in README.md

### Adding a New Format Support
1. Install the required Pillow plugin if needed
2. Update `requirements.txt` with the plugin
3. Register the format opener in `processor.py` if required
4. Add format-specific handling in the save/export logic
5. Test with sample images of that format

## Important Notes
- The application processes images in-memory for efficiency
- All edits are applied before resizing to ensure maximum output quality
- The app supports batch processing of multiple images
- Results stay available during downloads (won't disappear on click)
- For web deployment, the main file path should be `src/app.py`

## When Making Changes
- Always run tests after making changes to core functionality
- Test the UI manually by running the Streamlit app locally
- Ensure backward compatibility with existing functionality
- Update documentation if adding new features or changing behavior
- Consider performance implications for batch operations
