## 2024-12-12 - Parallel Processing for Image Uploads
**Learning:** Streamlit apps block the main thread during processing. Sequential processing of multiple uploaded files is a significant bottleneck. ThreadPoolExecutor works well for Pillow operations which release the GIL.
**Action:** Extracted processing logic to a stateless task function and used ThreadPoolExecutor to parallelize image processing, achieving ~40% speedup on bulk uploads. Important to pass raw bytes to workers as Streamlit's UploadedFile objects are not pickleable/thread-safe in the same way.

## 2024-12-12 - Session State Memory Optimization
**Learning:** Storing large `PIL.Image` objects in `st.session_state` causes significant memory bloat (uncompressed bitmaps) and slows down the app due to serialization overhead. Additionally, passing PIL objects to `st.image` forces Streamlit to re-encode them on every render.
**Action:** Modified the processing task to return raw `bytes` (the already-compressed output) instead of `BytesIO` or `PIL.Image` objects. Updated the UI to render directly from these bytes. This reduces memory usage drastically and eliminates redundant CPU encoding cycles.

## 2024-12-12 - Vectorized Image Color Replacement
**Learning:** Iterating over image pixels using Python loops (`for item in image.getdata()`) is extremely slow. Even for a 1000x1000 image, this is 1 million iterations.
**Action:** Replaced pixel iteration with Pillow's `Image.point()` (using lookup tables) and `ImageChops` math operations. This leverages C-level loops inside Pillow, resulting in a ~5x speedup (0.68s -> 0.14s) for color replacement operations.

## 2024-05-22 - Avoid Defensive Image Copies
**Learning:** `image.copy()` is expensive for large images as it duplicates the full pixel buffer. Often it's used defensively before analysis (like color extraction) or destructive edits.
**Action:** Reorder the pipeline: perform non-destructive analysis first on the initial image object, then proceed with destructive edits. This eliminates the need for `image.copy()`. Also, store the original file bytes for UI display instead of the uncompressed PIL object to save memory.

## 2024-12-12 - Pillow Save Optimization
**Learning:** `image.save(..., optimize=True)` in Pillow performs extra passes (e.g. Huffman table optimization for JPEG, filter trials for PNG) which can increase save time by 2-3x while only reducing file size by ~4-6%.
**Action:** Changed the default behavior to `optimize=False` to prioritize speed, and exposed an "Optimize Encoding" checkbox for users who specifically need smaller files. This results in a ~3x speedup for saving operations.

## 2024-12-12 - Histogram Calculation Mode Optimization
**Learning:** Calling `image.convert('RGB')` on large `RGBA` images just to generate a histogram is unnecessary and very slow (~0.27s for a 6000x6000 image) because it allocates a new image buffer and copies pixels. `image.histogram()` on an `RGBA` image already returns a concatenated list of R, G, B, and A histograms, meaning the first 768 elements perfectly match the `RGB` histogram.
**Action:** Updated `get_histogram_data` to skip the `RGB` conversion if the image is already in `RGBA` mode. This yields a ~2.7x speedup for calculating the histogram of large transparent images by avoiding defensive memory allocations and redundant pixel processing.

## 2024-05-19 - Image Rotation Optimization
**Learning:** Using `Image.rotate(angle, expand=True)` triggers a general affine transformation in PIL, which involves expensive interpolation even for exact 90-degree rotations.
**Action:** Replace `rotate()` with `Image.transpose(Image.Transpose.ROTATE_*)` when the angle is exactly 90, 180, or 270 degrees. This uses optimized C-level memory swapping that is significantly faster (~2.5x) and avoids sub-pixel artifacts.

## 2025-01-28 - Watermark Blending Optimization
**Learning:** Converting a large `RGB` image to `RGBA` solely to perform an `alpha_composite` with a small transparent layer, and then converting it back to `RGB`, is exceptionally slow (0.4s for a 6000x6000 image) and memory intensive.
**Action:** Used `image.paste(overlay, box, mask=overlay)` directly on the non-RGBA image, which performs the alpha blending dynamically in C on only the localized pixels. This avoids entire image memory allocations and yields a ~60% speedup. Important edge case: Palette (`P`) and Binary (`1`) modes must still be converted to `RGB` before pasting to avoid destroying the overlay colors.

## 2025-02-19 - Vectorization Disk I/O Optimization
**Learning:** Saving an image to disk via `tempfile` and reading the generated SVG back from disk is an unnecessary and slow performance bottleneck when using `vtracer`.
**Action:** Used `io.BytesIO` to keep image encoding in-memory and passed the raw bytes to `vtracer.convert_raw_image_to_svg(raw_bytes, img_format='png')` instead of `convert_image_to_svg_py`. This completely avoids file system operations and speeds up the vectorization pipeline.

## 2025-02-19 - FASTOCTREE Quantization for Dominant Colors
**Learning:** Extracting dominant colors via `image.quantize()` uses `MEDIANCUT` by default, which can be computationally expensive (taking ~40ms for small images). Using `method=Image.Quantize.FASTOCTREE` is drastically faster (~1ms, ~40x speedup) with practically no visual loss when fetching simple dominant hex colors.
**Action:** Changed the default quantization method in `get_dominant_colors` to `Image.Quantize.FASTOCTREE` to accelerate analysis times for user uploads without noticeable quality degradation.
