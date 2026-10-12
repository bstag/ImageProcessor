# Image Processor & Optimizer

A powerful, user-friendly web application built with **Streamlit** and **Pillow (PIL)** for batch image processing, editing, and web optimization.

## 🌟 Features

### 1. One-Click Presets
*   **Web**, **Email**, **Social Media** and **Thumbnail** presets set format, quality, maximum size and metadata stripping in one click.
*   Change any of those settings afterwards and the preset switches back to **Custom**.

### 2. Resizing
*   **Fit Within (shrink only)**: Cap images to a maximum width/height without ever enlarging small ones.
*   **Percentage**: Scale images by a percentage (1% - 200%).
*   **Fixed Dimensions**: Resize to a specific width/height, scaling up or down, with an option to keep the aspect ratio.
*   **High Quality**: Uses Lanczos resampling for the best possible quality.

### 3. Advanced Web Optimization
*   **Input Support**: PNG, JPEG, WebP, AVIF, BMP, **HEIC/HEIF** (common on iOS) and **GIF**.
*   **Modern Output Formats**: Convert images to **WebP**, **AVIF**, **SVG** (Vector), JPEG, PNG, and BMP.
*   **Animated GIFs**: Converted to animated **WebP**, **AVIF** or **PNG (APNG)** with every edit applied to each frame, usually at a fraction of the GIF's size.
*   **Target File Size**: Set a maximum size per image (e.g. 200 KB) and the highest quality that fits is chosen automatically (JPEG, WebP, AVIF).
*   **Format Comparison**: See each result's size as WebP, AVIF, JPEG and PNG side by side.
*   **Compression Control**:
    *   Adjustable **Quality Slider** (0-100).
    *   **Lossless Mode** for WebP and AVIF.
    *   **Vectorization Settings** for SVG (Color Mode, Layering, Smoothing, etc.).
*   **Metadata Stripping**: Removes EXIF data (camera, location, etc.) while keeping the color profile so colors stay accurate.
*   **Metadata Viewer**: Shows what each photo contained (camera, lens, date, software, author) and warns when it has GPS location data.

### 4. Built-in Image Editor
*   **Enhancements**: Adjust Brightness, Contrast, Saturation, and Sharpness.
*   **Transforms**: Rotate (90° steps), Flip Horizontal/Vertical. Phone photos are automatically rotated upright using their EXIF orientation.
*   **Cropping**: Trim pixels from each edge, center crop to an aspect ratio, or use a **Social Preset** (1:1, 4:5, 16:9, 9:16 stories, 1200×630 link previews) that crops to fill or pads to fit.
*   **Transparency**:
    *   **Detection**: Automatically detects if uploaded images contain transparency.
    *   **Color Replacement**: Replace a specific solid color (e.g., white background) with transparency using adjustable tolerance.
*   **Filters**: Apply creative presets including **Blur**, **Contour**, **Detail**, **Edge Enhance**, **Emboss**, **Sharpen**, and **Smooth**, plus Grayscale conversion.
*   **Watermarking**: Add custom text watermarks with adjustable size, opacity, color, and automatic bottom-right positioning.
*   **Color Analysis**: Extracts the top 5 dominant colors (ignoring transparent areas), plus an optional RGB histogram.
*   *Note: Crop and resize run before the pixel-level edits so those edits process fewer pixels.*

### 5. Export Extras
*   **Responsive Image Sets**: Export smaller copies at 320–1920px widths plus a ready-to-paste `<img srcset>` snippet (`srcset.html`).
*   **Favicon & App Icons**: `favicon.ico` (16/32/48), PNG favicons, Apple touch icon, Android/PWA icons, `site.webmanifest` and the HTML `<link>` tags.
*   **Combine into PDF**: Every processed image on its own page of one PDF.

### 6. Workflow & Interface
*   **Batch Processing**: Drag & drop multiple images at once.
*   **High Performance**:
    *   **Parallel Processing**: Uses multi-threaded parallel processing for fast batch conversions.
    *   **Vectorized Operations**: Utilizes `Pillow.ImageChops` for high-speed color replacement and masking.
*   **Visual Comparison**: Side-by-side "Original vs. Processed" preview.
*   **Real-time Metrics**: See file size reduction savings instantly.
*   **Persistence**: Processed results stay available during downloads (won't disappear on click).
*   **Notifications**: Non-intrusive toast notifications for status updates.
*   **Security & Safety**:
    *   **Input Validation**: Enforces limits on file count (50), total size (200MB), image dimensions (6000px), animation size (300 frames) and SVG tracing size to prevent resource exhaustion.
    *   **Sanitization**: Automatically sanitizes filenames to prevent path traversal issues during export.
*   **Export**: Download individual files or get everything (including responsive sizes, icons and the PDF) in a single **ZIP archive**.

---

## 🚀 Local Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd ImageProcessor
    ```

2.  **Set up a virtual environment** (Optional but recommended):
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # Mac/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application**:
    ```bash
    streamlit run src/app.py
    ```
    The app will open in your browser at `http://localhost:8501`.

---

## ☁️ Deployment on Streamlit Cloud

This application is ready to be deployed on [Streamlit Cloud](https://streamlit.io/cloud) for free.
[My Image Processor](https://imageproceappr-ykgxshj7qrhnlznbgtae2y.streamlit.app/)

### Prerequisites
*   A GitHub account.
*   The project code pushed to a GitHub repository.

### Steps
1.  **Push to GitHub**:
    Ensure your project structure looks like this:
    ```
    /
    ├── requirements.txt
    ├── src/
    │   ├── app.py
    │   ├── processor.py
    │   └── utils.py
    └── tests/
    ```

2.  **Log in to Streamlit Cloud**:
    Go to [share.streamlit.io](https://share.streamlit.io/) and sign in with GitHub.

3.  **Create a New App**:
    *   Click **"New app"**.
    *   Select your **Repository**, **Branch** (e.g., `main`), and **Main file path**.
    *   **Main file path**: Enter `src/app.py`.

4.  **Deploy**:
    *   Click **"Deploy!"**.
    *   Streamlit will automatically detect `requirements.txt` and install the necessary libraries (`pillow`, `pillow-heif`, etc.).

5.  **Done!**:
    Your app is now live on a public URL.

---

## 🛠️ Project Structure

```text
C:\Source\ImageProcessor\
│
├── requirements.txt      # Python dependencies
├── README.md             # Documentation
│
├── src/
│   ├── app.py            # Main Streamlit application UI
│   ├── processor.py      # Core image processing logic (PIL wrapper)
│   ├── tasks.py          # Parallel processing tasks
│   └── utils.py          # Helper functions (formatting, file handling)
│
└── tests/
    ├── test_processor.py # Unit tests for processing logic
    └── test_security.py  # Security and validation tests
```
