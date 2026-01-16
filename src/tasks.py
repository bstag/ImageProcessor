from processor import ImageProcessor
from PIL import Image
import io

def process_image_task(file_content, config):
    """
    Worker function to process a single image.
    Args:
        file_content (bytes): The raw bytes of the image file.
        config (dict): Configuration dictionary containing processing parameters.
    Returns:
        dict: On success, a dictionary containing:
            - original_size (int): Size of the original file in bytes.
            - original_dimensions (tuple[int, int]): Width and height of the original image.
            - processed_size (int): Size of the processed image in bytes.
            - data (io.BytesIO): In-memory binary stream of the processed image.
            - image (PIL.Image.Image): The processed PIL image.
            - original_image (PIL.Image.Image): A copy of the original PIL image.
            - has_transparency (bool): Whether the original image has transparency.
        On failure, a dictionary containing:
            - success (bool): False.
            - error (str): Error message.
    """
    try:
        # Load Image from bytes
        image = Image.open(io.BytesIO(file_content))

        # Security: Validate Image Format
        # Ensure the detected format is in our allowed list to prevent usage of vulnerable/obscure decoders.
        # This protects against attacks where a malicious file (e.g. SGI, PCX) is uploaded with a safe extension (.png).
        ALLOWED_FORMATS = {'PNG', 'JPEG', 'MPO', 'BMP', 'WEBP', 'HEIC', 'HEIF', 'AVIF'}
        if image.format not in ALLOWED_FORMATS:
             raise ValueError(f"Security violation: Image format '{image.format}' is not allowed.")

        # Security: Check dimensions immediately to prevent DoS (Pixel Flood)
        # Note: image.size is available without loading the full raster data
        if image.width > ImageProcessor.MAX_IMAGE_DIMENSION or image.height > ImageProcessor.MAX_IMAGE_DIMENSION:
            raise ValueError(f"Image dimensions ({image.width}x{image.height}) exceed maximum allowed size ({ImageProcessor.MAX_IMAGE_DIMENSION}px)")

        # Keep a copy of the original image for display in the UI.
        # Note: Returning PIL objects is suitable for threaded use; for process-based workers,
        # consider serializing image data instead.

        original_image = image.copy()
        original_size = len(file_content)  # Size in bytes of the original uploaded file content
        # App uses uploaded_file.size for original_size (bytes); here we derive it from the raw file bytes.
        original_dimensions = image.size

        # Process
        # 0. Enhancements & Transforms
        image = ImageProcessor.apply_enhancements(
            image,
            config.get('brightness', 1.0),
            config.get('contrast', 1.0),
            config.get('sharpness', 1.0),
            config.get('saturation', 1.0)
        )
        
        # Apply Filter
        filter_type = config.get('filter_type', 'None')
        if filter_type != "None":
            image = ImageProcessor.apply_filter(image, filter_type)

        image = ImageProcessor.apply_transforms(
            image,
            config.get('rotate', 0),
            config.get('flip_h', False),
            config.get('flip_v', False),
            config.get('grayscale', False)
        )

        # Crop
        crop_mode = config.get('crop_mode', 'None')
        if crop_mode != "None":
            if crop_mode == "Custom Box":
                iw, ih = image.size
                l = max(0, min(iw, int(config.get('crop_left', 0))))
                t = max(0, min(ih, int(config.get('crop_top', 0))))
                r_in = int(config.get('crop_right', 0))
                b_in = int(config.get('crop_bottom', 0))
                # Logic from app.py: r_in if > 0 else iw
                r_in = r_in if r_in > 0 else iw
                b_in = b_in if b_in > 0 else ih

                r = max(l + 1, min(iw, r_in))
                b = max(t + 1, min(ih, b_in))
                image = ImageProcessor.crop_image(image, l, t, r, b)
            elif crop_mode == "Aspect Center":
                image = ImageProcessor.center_crop_to_aspect(
                    image,
                    int(config.get('crop_aspect_w', 1)),
                    int(config.get('crop_aspect_h', 1))
                )

        # Pixelate
        pixel_size = config.get('pixel_size', 1)
        if pixel_size > 1:
            image = ImageProcessor.pixelate(image, pixel_size)

        # Transparency Replacement
        if config.get('replace_color', False):
            rgb_color = config.get('trans_color_rgb')
            if rgb_color:
                image = ImageProcessor.replace_color_with_transparency(
                    image,
                    rgb_color,
                    config.get('trans_tolerance', 10)
                )

        # Extract Dominant Colors (if requested)
        dominant_colors = []
        if config.get('extract_colors', False):
            dominant_colors = ImageProcessor.get_dominant_colors(original_image, 5)

        # Histogram (if requested) - Calculate on processed image (or original? usually processed result is what matters)
        # Let's calculate on the processed result so users see the effect of their changes
        histogram_data = None
        if config.get('show_histogram', False):
            histogram_data = ImageProcessor.get_histogram_data(image)

        # Watermark
        wm_text = config.get('watermark_text')
        if wm_text:
            image = ImageProcessor.add_watermark(
                image,
                wm_text,
                opacity=config.get('wm_opacity', 128),
                font_size=config.get('wm_size', 30),
                color=config.get('wm_color', (255, 255, 255))
            )

        # 1. Resize
        resize_type = config.get('resize_type', 'None')
        if resize_type != "None":
            image = ImageProcessor.resize_image(
                image,
                width=config.get('width'),
                height=config.get('height'),
                percentage=config.get('percentage'),
                maintain_aspect_ratio=config.get('maintain_aspect', True)
            )

        # Check transparency
        original_has_transparency = ImageProcessor.has_transparency(original_image)

        # 2. Save/Optimize
        output_format = config.get('output_format', 'JPEG')
        
        if output_format == 'SVG':
             # Convert to SVG string then to bytes
             svg_content = ImageProcessor.convert_to_svg(image, **config)
             processed_data = svg_content.encode('utf-8')
             processed_size = len(processed_data)
        else:
             output_io = ImageProcessor.process_and_save(
                image,
                output_format,
                config.get('quality', 80),
                optimize=True,
                strip_metadata=config.get('strip_metadata', True),
                lossless=config.get('lossless', False)
             )
             processed_data = output_io.getvalue()
             processed_size = len(processed_data)

        # Performance Optimization (Bolt):
        # 1. Return raw bytes for 'data' instead of BytesIO to avoid cursor state issues and multiple .getvalue() calls.
        # 2. Do NOT return the processed PIL 'image'. It's large (uncompressed) and we can use 'data' (bytes) for display.
        #    This significantly reduces memory usage in st.session_state and avoids re-encoding overhead in st.image().

        return {
            "success": True,
            "original_size": original_size,
            "original_dimensions": original_dimensions,
            "processed_size": processed_size,
            "data": processed_data,
            "original_image": original_image,
            "has_transparency": original_has_transparency,
            "dominant_colors": dominant_colors,
            "histogram_data": histogram_data
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
