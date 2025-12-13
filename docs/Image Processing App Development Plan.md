# Image Processing Application Development Plan

I propose building a Python-based application using **Streamlit** for the web interface and **Pillow (PIL)** for image processing. This stack ensures a clean, interactive UI with powerful processing capabilities.

## 1. Project Structure & Setup
- Initialize project with a virtual environment.
- Create `requirements.txt` with dependencies:
  - `streamlit`: For the web interface.
  - `Pillow`: Core image processing library.
  - `pillow-avif-plugin`: For AVIF support.
  - `rembg` (Optional): For background removal if needed, though not explicitly requested, good for "web optimization". (Will stick to core requirements first).
- Directory structure:
  ```
  /src
    ├── app.py          # Main Streamlit application
    ├── processor.py    # Core logic for image manipulation
    └── utils.py        # Helper functions (file naming, logging)
  /tests                # Unit tests
  ```

## 2. Core Image Processing Module (`src/processor.py`)
- **Rescaling Logic**:
  - Implement `resize_image()` with parameters for:
    - Fixed dimensions (Width/Height).
    - Percentage scaling.
    - Aspect ratio preservation (using `Image.thumbnail` or math).
    - Crop functionality (Center crop or custom coordinates).
- **Web Optimization**:
  - Implement format conversion:
    - **WebP**: Native Pillow support.
    - **AVIF**: Via plugin.
    - **JPEG-XR**: Note: This is a legacy format with limited Python support; we will prioritize WebP/AVIF but investigate `imageio` or `wand` if strictly required.
  - **Compression**: Control `quality` and `optimize` flags in `save()`.
  - **Metadata**: Option to strip EXIF data.

## 3. User Interface (`src/app.py`)
- **Upload Section**: Support for batch uploading (Drag & drop).
- **Configuration Sidebar**:
  - Resize Mode (Pixel, Percentage).
  - Target Format (WebP, AVIF, JPEG, PNG).
  - Quality Slider (0-100).
  - "Web Friendly" Preset (Auto-settings for <500KB).
- **Preview & Compare**:
  - Side-by-side comparison of Original vs. Processed image.
  - Real-time file size reporting.
- **Output Generation**:
  - "Process All" button.
  - Download link (Individual files or ZIP archive for batch).

## 4. Implementation Steps
1.  **Environment**: Set up Python venv and install dependencies.
2.  **Backend**: Develop `ImageProcessor` class in `processor.py` covering all resizing and saving logic.
3.  **Frontend**: Build the Streamlit UI in `app.py` to wire up inputs to the backend.
4.  **Integration**: Implement the batch processing loop and comparison view.
5.  **Verification**: Test with various image formats and ensure file sizes meet targets.

## 5. Quality Control & Validation
- **Visuals**: Use Streamlit's `st.image` to show before/after.
- **Metrics**: Display reduction percentage (e.g., "Reduced by 70%: 2MB -> 600KB").
- **Error Handling**: Try/Except blocks for corrupt images or unsupported formats.
