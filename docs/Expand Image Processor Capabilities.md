# Application Expansion Plan

To expand the application's capabilities with the **least amount of code**, I recommend leveraging the existing `Pillow` library's built-in enhancement and transformation modules. This avoids new dependencies while significantly increasing functionality.

## 1. Fix Configuration
- Correct the detected typo in `requirements.txt` (`2streamlit` -> `streamlit`).

## 2. Core Enhancements (`src/processor.py`)
Add a new `enhance_image` method to handle:
- **Image Adjustments**:
  - **Brightness**: Lighten/Darken images.
  - **Contrast**: Enhance tonal difference.
  - **Sharpness**: Refine edges (crucial for resized web images).
  - **Saturation**: Color intensity control.
- **Geometric Transforms**:
  - **Rotation**: 90° steps.
  - **Flipping**: Horizontal/Vertical mirroring.
- **Filters**:
  - **Grayscale**: Simple conversion for aesthetic or file-size reduction.

## 3. UI Updates (`src/app.py`)
- Add an **"Editor"** tab or expander in the sidebar.
- Implement sliders for `Brightness`, `Contrast`, `Sharpness` (Default: 1.0).
- Add simple buttons/selects for `Rotation` and `Grayscale`.
- Ensure these operations occur **before** resizing to maintain maximum quality.

## Why this approach?
- **Zero new dependencies**: Uses standard `PIL.ImageEnhance` and `PIL.ImageOps`.
- **High Impact**: Transforms the tool from a "converter" to a "photo editor".
- **Minimal Code**: Approximately 30-40 lines of code total.
