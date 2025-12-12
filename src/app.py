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
mode = st.sidebar.radio("Mode", ["Rescaling", "Web Optimization"])

# Output Format
st.sidebar.subheader("Output Format")
output_format = st.sidebar.selectbox("Format", ["WEBP", "AVIF", "JPEG", "PNG", "BMP"], index=0)

lossless = False
if output_format in ["WEBP", "AVIF"]:
    lossless = st.sidebar.checkbox("Lossless Compression", value=False)

if not lossless:
    quality = st.sidebar.slider("Quality", 0, 100, 80)
else:
    quality = 100 # Ignored by some, but good practice
    st.sidebar.info("Quality slider disabled in Lossless mode")

strip_metadata = st.sidebar.checkbox("Strip Metadata", value=True)

# Resizing Options
st.sidebar.subheader("Resizing")
resize_type = st.sidebar.selectbox("Resize Mode", ["None", "Percentage", "Fixed Dimensions"])

width = None
height = None
percentage = None
maintain_aspect = True

if resize_type == "Percentage":
    percentage = st.sidebar.slider("Percentage", 1, 200, 100)
elif resize_type == "Fixed Dimensions":
    col1, col2 = st.sidebar.columns(2)
    with col1:
        width = st.sidebar.number_input("Width (px)", min_value=1, value=800)
    with col2:
        height = st.sidebar.number_input("Height (px)", min_value=1, value=600)
    maintain_aspect = st.sidebar.checkbox("Maintain Aspect Ratio", value=True)

# Editor Controls
st.sidebar.markdown("---")
st.sidebar.subheader("Editor")

with st.sidebar.expander("Enhancements"):
    brightness = st.slider("Brightness", 0.0, 2.0, 1.0, 0.1)
    contrast = st.slider("Contrast", 0.0, 2.0, 1.0, 0.1)
    saturation = st.slider("Saturation", 0.0, 2.0, 1.0, 0.1)
    sharpness = st.slider("Sharpness", 0.0, 3.0, 1.0, 0.1)

with st.sidebar.expander("Transforms"):
    rotate = st.selectbox("Rotate", [0, 90, 180, 270])
    col1, col2 = st.columns(2)
    with col1:
        flip_h = st.checkbox("Flip Horizontal")
    with col2:
        flip_v = st.checkbox("Flip Vertical")
    grayscale = st.checkbox("Convert to Grayscale")

# File Uploader
uploaded_files = st.file_uploader("Upload Images", type=['png', 'jpg', 'jpeg', 'webp', 'bmp', 'gif'], accept_multiple_files=True)

if 'processed_images' not in st.session_state:
    st.session_state.processed_images = None

if uploaded_files:
    st.subheader(f"Processing {len(uploaded_files)} Images")
    
    if st.button("Process Images"):
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
        if st.button("Clear Results"):
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
            mime="application/zip"
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
                    mime=f"image/{output_format.lower()}"
                )

else:
    st.info("Please upload images to begin.")

