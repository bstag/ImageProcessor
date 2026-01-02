import streamlit as st
from PIL import Image
import io
import zipfile
import os
from processor import ImageProcessor
from utils import format_bytes, get_unique_filename, get_safe_filename_stem, validate_upload_constraints
from tasks import process_image_task
from concurrent.futures import ThreadPoolExecutor, as_completed


st.set_page_config(page_title="Image Processor", layout="wide")

st.title("Image Processing & Optimization")

uploaded_files = st.file_uploader(
    "Upload Images",
    type=['png', 'jpg', 'jpeg', 'bmp', 'webp', 'heic', 'heif', 'avif'],
    accept_multiple_files=True,
    help="Drag and drop images here or click to browse."
)

# Sidebar Configuration
st.sidebar.header("Settings")

# Mode Selection
mode = st.sidebar.radio(
    "Mode",
    ["Rescaling", "Web Optimization"],
    help="Choose between general resizing or optimizing images for the web."
)

# Output Format
st.sidebar.subheader("Output Format")
output_format = st.sidebar.selectbox(
    "Format",
    ["WEBP", "AVIF", "JPEG", "PNG", "BMP"],
    index=0,
    help="Select the file format for the processed images. WebP and AVIF offer better compression."
)

lossless = False
if output_format in ["WEBP", "AVIF"]:
    lossless = st.sidebar.checkbox(
        "Lossless Compression",
        value=False,
        help="Retain perfect quality at the cost of larger file size. Available for WebP and AVIF."
    )

quality_disabled = False
quality_help = "Adjust compression level. Lower values result in smaller files but lower quality."

if lossless:
    quality_disabled = True
    quality_help = "Quality selection is disabled because Lossless Compression is active."
elif output_format in ['PNG', 'BMP']:
    quality_disabled = True
    quality_help = f"Quality selection is not applicable for {output_format} format."

quality_val = st.sidebar.slider(
    "Quality",
    0,
    100,
    80,
    disabled=quality_disabled,
    help=quality_help
)

if quality_disabled:
    quality = 100
else:
    quality = quality_val

strip_metadata = st.sidebar.checkbox(
    "Strip Metadata",
    value=True,
    help="Remove EXIF data (camera settings, location, etc.) to reduce file size and protect privacy."
)

# Resizing Options
st.sidebar.subheader("Resizing")
resize_type = st.sidebar.selectbox(
    "Resize Mode",
    ["None", "Percentage", "Fixed Dimensions"],
    help="Choose how to resize the image."
)

width = None
height = None
percentage = None
maintain_aspect = True

if resize_type == "Percentage":
    percentage = st.sidebar.slider(
        "Percentage",
        1,
        200,
        100,
        help="Scale the image by this percentage."
    )
elif resize_type == "Fixed Dimensions":
    col1, col2 = st.sidebar.columns(2)
    with col1:
        width = st.sidebar.number_input("Width (px)", min_value=1, max_value=10000, value=800, help="Target width in pixels.")
    with col2:
        height = st.sidebar.number_input("Height (px)", min_value=1, max_value=10000, value=600, help="Target height in pixels.")
    maintain_aspect = st.sidebar.checkbox(
        "Maintain Aspect Ratio",
        value=True,
        help="Preserve the original width-to-height ratio to prevent distortion."
    )

# Editor Controls
st.sidebar.markdown("---")
st.sidebar.subheader("Editor")

with st.sidebar.expander("Enhancements"):
    brightness = st.slider("Brightness", 0.0, 2.0, 1.0, 0.1, help="Adjust the brightness of the image.")
    contrast = st.slider("Contrast", 0.0, 2.0, 1.0, 0.1, help="Adjust the contrast of the image.")
    saturation = st.slider("Saturation", 0.0, 2.0, 1.0, 0.1, help="Adjust the color intensity.")
    sharpness = st.slider("Sharpness", 0.0, 3.0, 1.0, 0.1, help="Adjust the sharpness of edges.")

with st.sidebar.expander("Transforms"):
    rotate = st.selectbox("Rotate", [0, 90, 180, 270], help="Rotate the image clockwise.")
    col1, col2 = st.columns(2)
    with col1:
        flip_h = st.checkbox("Flip Horizontal", help="Mirror the image horizontally.")
    with col2:
        flip_v = st.checkbox("Flip Vertical", help="Mirror the image vertically.")
    grayscale = st.checkbox("Convert to Grayscale", help="Convert the image to black and white.")

with st.sidebar.expander("Crop"):
    crop_mode = st.selectbox("Crop Mode", ["None", "Custom Box", "Aspect Center"], help="Choose a cropping strategy.")
    
    # Initialize crop variables with defaults (similar pattern to resize variables at lines 69-72)
    crop_left = 0
    crop_top = 0
    crop_right = 0
    crop_bottom = 0
    crop_aspect_w = 1
    crop_aspect_h = 1
    
    if crop_mode == "Custom Box":
        c1, c2 = st.columns(2)
        with c1:
            crop_left = st.number_input("Left", min_value=0, value=0, help="Pixels to crop from left.")
            crop_top = st.number_input("Top", min_value=0, value=0, help="Pixels to crop from top.")
        with c2:
            crop_right = st.number_input("Right", min_value=0, value=0, help="Pixels to crop from right.")
            crop_bottom = st.number_input("Bottom", min_value=0, value=0, help="Pixels to crop from bottom.")
    elif crop_mode == "Aspect Center":
        a1, a2 = st.columns(2)
        with a1:
            crop_aspect_w = st.number_input("Aspect Width", min_value=1, value=1, help="Width ratio (e.g., 16 for 16:9).")
        with a2:
            crop_aspect_h = st.number_input("Aspect Height", min_value=1, value=1, help="Height ratio (e.g., 9 for 16:9).")

with st.sidebar.expander("Transparency"):
    replace_color = st.checkbox("Replace Color with Transparency", help="Make a specific color transparent.")
    if replace_color:
        trans_color = st.color_picker("Color to Replace", "#FFFFFF", help="Choose the color to make transparent.")
        trans_tolerance = st.slider("Tolerance", 0, 100, 10, help="How much variation in color to accept.")
        if output_format in ['JPEG', 'BMP']:
            st.warning("Selected output format does not support transparency!")

if 'processed_images' not in st.session_state:
    st.session_state.processed_images = None

if uploaded_files:
    st.subheader(f"Processing {len(uploaded_files)} Images")
    
    # Security Check: Validate upload constraints to prevent DoS
    MAX_FILE_COUNT = 50
    MAX_TOTAL_SIZE_MB = 200
    is_valid, error_msg = validate_upload_constraints(uploaded_files, MAX_FILE_COUNT, MAX_TOTAL_SIZE_MB)

    if not is_valid:
        st.error(f"Upload limit exceeded: {error_msg}")
    elif st.button("Process Images", type="primary", help="Click to start processing all uploaded images with the selected settings."):
        processed_images = []
        progress_bar = st.progress(0)
        
        # Prepare configuration dictionary
        config = {
            'brightness': brightness,
            'contrast': contrast,
            'sharpness': sharpness,
            'saturation': saturation,
            'rotate': rotate,
            'flip_h': flip_h,
            'flip_v': flip_v,
            'grayscale': grayscale,
            'resize_type': resize_type,
            'width': width,
            'height': height,
            'percentage': percentage,
            'maintain_aspect': maintain_aspect,
            'output_format': output_format,
            'quality': quality,
            'strip_metadata': strip_metadata,
            'lossless': lossless,
            'crop_mode': crop_mode
        }

        # Add conditional config
        if crop_mode == "Custom Box":
            config.update({
                'crop_left': crop_left,
                'crop_top': crop_top,
                'crop_right': crop_right,
                'crop_bottom': crop_bottom
            })
        elif crop_mode == "Aspect Center":
            config.update({
                'crop_aspect_w': crop_aspect_w,
                'crop_aspect_h': crop_aspect_h
            })

        if replace_color:
            tc = trans_color.lstrip('#')
            rgb_color = tuple(int(tc[i:i+2], 16) for i in (0, 2, 4))
            config['replace_color'] = True
            config['trans_color_rgb'] = rgb_color
            config['trans_tolerance'] = trans_tolerance

        # Parallel Processing
        # Bolt Optimization: Parallelize image processing to improve performance for multiple uploads
        # Limit the number of worker threads to avoid excessive memory usage when processing many images
        max_workers = 1
        if uploaded_files:
            cpu_count = os.cpu_count() or 1
            # Cap workers by CPU count, number of files, and a small upper bound to control memory usage
            max_workers = min(8, cpu_count, len(uploaded_files))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # We must read file content here because Streamlit's UploadedFile isn't thread-safe for reading across threads
            # (or rather, we want to ensure we have the data ready)
            files_data = [(f.name, f.size, f.getvalue()) for f in uploaded_files]

            # Submit tasks
            future_to_file = {
                executor.submit(process_image_task, content, config): (name, size)
                for name, size, content in files_data
            }

            completed_count = 0
            for future in as_completed(future_to_file):
                name, original_bytes_size = future_to_file[future]
                result = future.result()
                
                if result['success']:
                    processed_images.append({
                        "name": name,
                        "original_size": original_bytes_size,
                        "processed_size": result['processed_size'],
                        "data": result['data'],
                        "original_image": result['original_image'],
                        "has_transparency": result['has_transparency']
                    })
                else:
                    st.error(
                        f"Error processing file '{name}' "
                        f"(size: {format_bytes(original_bytes_size)}, "
                        f"output format: {config.get('output_format', 'original')}): "
                        f"{result['error']}"
                    )
                
                completed_count += 1
                progress_bar.progress(completed_count / len(uploaded_files))

        # Store in session state
        st.session_state.processed_images = processed_images
        st.toast("Processing Complete!", icon='🎉')

    # Display Results if available in session state
    if st.session_state.processed_images:
        if st.button("Clear Results", help="Clear all processed images and start over."):
            st.session_state.processed_images = None
            st.rerun()

        # Recalculate totals for display
        total_original_size = sum(item['original_size'] for item in st.session_state.processed_images)
        total_processed_size = sum(item['processed_size'] for item in st.session_state.processed_images)

        # Summary Metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Original Size", format_bytes(total_original_size))
        col2.metric("Total Processed Size", format_bytes(total_processed_size))
        savings = (1 - total_processed_size / total_original_size) * 100 if total_original_size > 0 else 0
        col3.metric("Space Savings", f"{savings:.1f}%")
        
        # Zip Download
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for item in st.session_state.processed_images:
                # Security: Sanitize filename to prevent zip slip/path traversal
                name_stem = get_safe_filename_stem(item['name'])
                file_name = f"processed_{name_stem}.{output_format.lower()}"
                zf.writestr(file_name, item['data'])
        
        st.download_button(
            label="Download All as ZIP",
            data=zip_buffer.getvalue(),
            file_name="processed_images.zip",
            mime="application/zip",
            type="primary",
            help="Download all processed images in a single ZIP file."
        )
        
        # Individual Previews
        st.subheader("Detailed Results")
        for item in st.session_state.processed_images:
            # Security: Sanitize filename for display and download
            safe_name = os.path.basename(item['name'])
            name_stem = get_safe_filename_stem(item['name'])

            with st.expander(f"{safe_name} -> {format_bytes(item['processed_size'])}"):
                if item.get("has_transparency"):
                    st.caption("ℹ️ Original image has transparency")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.image(item['original_image'], caption=f"Original ({format_bytes(item['original_size'])})", use_container_width=True)
                with col2:
                    # Bolt: Use raw bytes ('data') instead of PIL object ('image') to avoid re-encoding overhead.
                    st.image(item['data'], caption=f"Processed ({format_bytes(item['processed_size'])})", use_container_width=True)
                
                st.download_button(
                    label=f"Download {safe_name}",
                    data=item['data'],
                    file_name=f"processed_{name_stem}.{output_format.lower()}",
                    mime=f"image/{output_format.lower()}",
                    help=f"Download {safe_name}"
                )

else:
    st.info("👋 Upload images above to begin processing.")
