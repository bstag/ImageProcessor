import streamlit as st
from PIL import Image
import io
import zipfile
from processor import ImageProcessor
from utils import format_bytes, get_unique_filename

st.set_page_config(page_title="Image Processor", layout="wide")

st.title("Image Processing & Optimization")

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

if not lossless:
    quality = st.sidebar.slider(
        "Quality",
        0,
        100,
        80,
        help="Adjust compression level. Lower values result in smaller files but lower quality."
    )
else:
    quality = 100 # Ignored by some, but good practice
    st.sidebar.info("Quality slider disabled in Lossless mode")

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
        width = st.sidebar.number_input("Width (px)", min_value=1, value=800, help="Target width in pixels.")
    with col2:
        height = st.sidebar.number_input("Height (px)", min_value=1, value=600, help="Target height in pixels.")
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
    rotate = st.selectbox("Rotate", [0, 90, 180, 270], help="Rotate the image counter-clockwise.")
    col1, col2 = st.columns(2)
    with col1:
        flip_h = st.checkbox("Flip Horizontal", help="Mirror the image horizontally.")
    with col2:
        flip_v = st.checkbox("Flip Vertical", help="Mirror the image vertically.")
    grayscale = st.checkbox("Convert to Grayscale", help="Convert the image to black and white.")

with st.sidebar.expander("Crop"):
    crop_mode = st.selectbox("Crop Mode", ["None", "Custom Box", "Aspect Center"], help="Choose a cropping strategy.")
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

# File Uploader
uploaded_files = st.file_uploader(
    "Upload Images",
    type=['png', 'jpg', 'jpeg', 'webp', 'bmp', 'gif'],
    accept_multiple_files=True,
    help="Drag and drop or click to upload images."
)

if 'processed_images' not in st.session_state:
    st.session_state.processed_images = None

if uploaded_files:
    st.subheader(f"Processing {len(uploaded_files)} Images")
    
    if st.button("Process Images", help="Click to start processing all uploaded images with the selected settings."):
        processed_images = []
        
        progress_bar = st.progress(0)
        
        for idx, uploaded_file in enumerate(uploaded_files):
            # Load Image
            try:
                image = Image.open(uploaded_file)
                # Keep a copy of original for display
                original_image = image.copy()
                original_size = uploaded_file.size
                
                # Process
                # 0. Enhancements & Transforms (New)
                image = ImageProcessor.apply_enhancements(image, brightness, contrast, sharpness, saturation)
                image = ImageProcessor.apply_transforms(image, rotate, flip_h, flip_v, grayscale)

                # Crop
                if 'crop_mode' in locals() and crop_mode != "None":
                    if crop_mode == "Custom Box":
                        iw, ih = image.size
                        l = max(0, min(iw, int(crop_left)))
                        t = max(0, min(ih, int(crop_top)))
                        r_in = int(crop_right) if crop_right > 0 else iw
                        b_in = int(crop_bottom) if crop_bottom > 0 else ih
                        r = max(l + 1, min(iw, r_in))
                        b = max(t + 1, min(ih, b_in))
                        image = ImageProcessor.crop_image(image, l, t, r, b)
                    elif crop_mode == "Aspect Center":
                        image = ImageProcessor.center_crop_to_aspect(image, int(crop_aspect_w), int(crop_aspect_h))

                # 1. Resize
                if resize_type != "None":
                    image = ImageProcessor.resize_image(image, width, height, percentage, maintain_aspect)
                
                # 2. Save/Optimize
                output_io = ImageProcessor.process_and_save(image, output_format, quality, optimize=True, strip_metadata=strip_metadata, lossless=lossless)
                processed_size = output_io.getbuffer().nbytes
                
                processed_images.append({
                    "name": uploaded_file.name,
                    "original_size": original_size,
                    "processed_size": processed_size,
                    "data": output_io,
                    "image": image, # The PIL image object for display
                    "original_image": original_image # Store original for comparison
                })
            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {e}")
            
            progress_bar.progress((idx + 1) / len(uploaded_files))
        
        # Store in session state
        st.session_state.processed_images = processed_images
        st.success("Processing Complete!")

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
                file_name = f"processed_{item['name'].rsplit('.', 1)[0]}.{output_format.lower()}"
                zf.writestr(file_name, item['data'].getvalue())
        
        st.download_button(
            label="Download All as ZIP",
            data=zip_buffer.getvalue(),
            file_name="processed_images.zip",
            mime="application/zip",
            help="Download all processed images in a single ZIP file."
        )
        
        # Individual Previews
        st.subheader("Detailed Results")
        for item in st.session_state.processed_images:
            with st.expander(f"{item['name']} -> {format_bytes(item['processed_size'])}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.image(item['original_image'], caption=f"Original ({format_bytes(item['original_size'])})", use_container_width=True)
                with col2:
                    st.image(item['image'], caption=f"Processed ({format_bytes(item['processed_size'])})", use_container_width=True)
                
                st.download_button(
                    label=f"Download {item['name']}",
                    data=item['data'].getvalue(),
                    file_name=f"processed_{item['name'].rsplit('.', 1)[0]}.{output_format.lower()}",
                    mime=f"image/{output_format.lower()}",
                    help=f"Download {item['name']}"
                )

else:
    st.info("Please upload images to begin.")
