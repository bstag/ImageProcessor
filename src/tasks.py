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
        dict: A dictionary containing the processed image data and metadata, or error info.
    """
    try:
        # Load Image from bytes
        image = Image.open(io.BytesIO(file_content))

        # Keep a copy of original for display (we need to return it because we can't update UI from here)
        # Note: We can't return the PIL object easily if we want to be process-safe, but for threads it is fine.
        # However, for memory efficiency, maybe we shouldn't duplicate it here if we don't strictly need to.
        # The main app needs: original_size, processed_size, data (bytes), image (PIL), original_image (PIL), has_transparency

        original_image = image.copy()
        original_size = len(file_content) # Approximation or we use image.size (dimensions)?
        # App uses uploaded_file.size for original_size (bytes). We can pass that in or just use len(file_content).
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

        # Transparency Replacement
        if config.get('replace_color', False):
            rgb_color = config.get('trans_color_rgb')
            if rgb_color:
                 image = ImageProcessor.replace_color_with_transparency(
                     image,
                     rgb_color,
                     config.get('trans_tolerance', 10)
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
        output_io = ImageProcessor.process_and_save(
            image,
            config.get('output_format', 'JPEG'),
            config.get('quality', 80),
            optimize=True,
            strip_metadata=config.get('strip_metadata', True),
            lossless=config.get('lossless', False)
        )
        processed_size = output_io.getbuffer().nbytes

        return {
            "success": True,
            "original_size": original_size, # This is bytes
            "original_dimensions": original_dimensions,
            "processed_size": processed_size,
            "data": output_io,
            "image": image,
            "original_image": original_image,
            "has_transparency": original_has_transparency
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
