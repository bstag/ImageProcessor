# Image Processor & Optimizer

A powerful, user-friendly web application built with **Streamlit** and **Pillow (PIL)** for batch image processing, editing, and web optimization.

## 🌟 Features

### 1. Image Rescaling
*   **Modes**:
    *   **Percentage**: Scale images by a percentage (1% - 200%).
    *   **Fixed Dimensions**: Resize to specific width/height pixels.
*   **Smart Resizing**: Option to lock aspect ratio to prevent distortion.
    *   **Auto-Detection**: Automatically calculates aspect ratio from the first uploaded image.
    *   **Bi-directional Updates**: Changing width updates height (and vice-versa) to maintain the ratio.
*   **High Quality**: Uses Lanczos resampling for the best possible quality.

### 2. Advanced Web Optimization
*   **Input Support**: Seamlessly handles **HEIC/HEIF** files (common on iOS) in addition to standard formats.
*   **Modern Output Formats**: Convert images to **WebP**, **AVIF**, JPEG, PNG, and BMP.
*   **Compression Control**:
    *   Adjustable **Quality Slider** (0-100).
    *   **Lossless Mode** for WebP and AVIF.
*   **Metadata Stripping**: Automatically removes EXIF data to reduce file size.

### 3. Built-in Image Editor
*   **Enhancements**: Adjust Brightness, Contrast, Saturation, and Sharpness.
*   **Transforms**: Rotate (90° steps), Flip Horizontal/Vertical.
*   **Cropping**: Custom box crop or aspect-ratio based center crop.
*   **Transparency**:
    *   **Detection**: Automatically detects if uploaded images contain transparency.
    *   **Color Replacement**: Replace a specific solid color (e.g., white background) with transparency using adjustable tolerance.
*   **Filters**: Apply creative presets including **Blur**, **Contour**, **Detail**, **Edge Enhance**, **Emboss**, **Sharpen**, and **Smooth**, plus Grayscale conversion.
*   *Note: All edits are applied before resizing to ensure maximum output quality.*

### 4. Workflow & Interface
*   **Batch Processing**: Drag & drop multiple images at once.
*   **High Performance**:
    *   **Parallel Processing**: Uses multi-threaded parallel processing for fast batch conversions.
    *   **Vectorized Operations**: Utilizes `Pillow.ImageChops` for high-speed color replacement and masking.
*   **Visual Comparison**: Side-by-side "Original vs. Processed" preview.
*   **Real-time Metrics**: See file size reduction savings instantly.
*   **Persistence**: Processed results stay available during downloads (won't disappear on click).
*   **Notifications**: Non-intrusive toast notifications for status updates.
*   **Security & Safety**:
    *   **Input Validation**: Enforces limits on file count (50), total size (200MB), and image dimensions (10k px) to prevent resource exhaustion.
    *   **Sanitization**: Automatically sanitizes filenames to prevent path traversal issues during export.
*   **Export**: Download individual files or get everything in a single **ZIP archive**.

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
    *   Streamlit will automatically detect `requirements.txt` and install the necessary libraries (`pillow`, `pillow-avif-plugin`, etc.).

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
