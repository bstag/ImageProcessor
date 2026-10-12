from processor import ImageProcessor, ImageLimitError
from exports import make_icon_pack, make_responsive_variants
from PIL import Image, ImageOps, ImageSequence, UnidentifiedImageError
import io
from typing import Dict, Any, List
from logging_config import setup_logging

# Setup logger
logger = setup_logging()

# Security: limits for animated inputs, which multiply work by their frame count
MAX_ANIMATION_FRAMES = 300
MAX_ANIMATION_PIXELS = 150_000_000  # width * height * frames


class SecurityError(ValueError):
    """Custom exception for security violations."""
    pass


def apply_edits(image: Image.Image, config: Dict[str, Any]) -> Image.Image:
    """
    Apply every per-image edit except the watermark: transforms, crop, resize,
    enhancements, filters, pixelation and color-to-transparency.
    Shared by still images and each frame of an animation.
    """
    # Bolt Optimization: Move Transform, Crop, and Resize BEFORE pixel-wise operations
    # (Enhancements, Filters, Pixelate, Watermark) to reduce the number of pixels
    # processed in those expensive operations, yielding significant speedups.

    # Transforms (fast, might change dimensions e.g. rotate 90)
    image = ImageProcessor.apply_transforms(
        image,
        config.get('rotate', 0),
        config.get('flip_h', False),
        config.get('flip_v', False),
        config.get('grayscale', False)
    )

    # Crop (must apply to original/rotated dimensions, not resized)
    crop_mode = config.get('crop_mode', 'None')
    if crop_mode == "Custom Box":
        # Each value is the number of pixels to trim from that edge (as the UI describes).
        # Clamp so at least a 1x1 region always remains.
        iw, ih = image.size
        l = max(0, min(iw - 1, int(config.get('crop_left', 0))))
        t = max(0, min(ih - 1, int(config.get('crop_top', 0))))
        r = max(l + 1, iw - max(0, int(config.get('crop_right', 0))))
        b = max(t + 1, ih - max(0, int(config.get('crop_bottom', 0))))
        image = ImageProcessor.crop_image(image, l, t, r, b)
    elif crop_mode == "Aspect Center":
        image = ImageProcessor.center_crop_to_aspect(
            image,
            int(config.get('crop_aspect_w', 1)),
            int(config.get('crop_aspect_h', 1))
        )
    elif crop_mode == "Social Preset":
        image = ImageProcessor.fit_to_size(
            image,
            tuple(config.get('social_size', (1080, 1080))),
            config.get('social_fit', 'crop'),
            tuple(config.get('social_pad_color', (255, 255, 255)))
        )

    # Resize (reduce number of pixels for subsequent operations)
    resize_type = config.get('resize_type', 'None')
    if resize_type == "Fit Within":
        # Shrink-only: cap the size to the box, never enlarge
        max_w, max_h = config.get('width'), config.get('height')
        if max_w and max_h and (image.width > max_w or image.height > max_h):
            image = ImageProcessor.resize_image(image, width=max_w, height=max_h, maintain_aspect_ratio=True)
    elif resize_type != "None":
        image = ImageProcessor.resize_image(
            image,
            width=config.get('width'),
            height=config.get('height'),
            percentage=config.get('percentage'),
            maintain_aspect_ratio=config.get('maintain_aspect', True)
        )

    # Enhancements & Filters (now running on potentially much smaller image)
    image = ImageProcessor.apply_enhancements(
        image,
        config.get('brightness', 1.0),
        config.get('contrast', 1.0),
        config.get('sharpness', 1.0),
        config.get('saturation', 1.0)
    )

    filter_type = config.get('filter_type', 'None')
    if filter_type != "None":
        image = ImageProcessor.apply_filter(image, filter_type)

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
    return image


def apply_watermark(image: Image.Image, config: Dict[str, Any]) -> Image.Image:
    wm_text = config.get('watermark_text')
    if not wm_text:
        return image
    return ImageProcessor.add_watermark(
        image,
        wm_text,
        opacity=config.get('wm_opacity', 128),
        font_size=config.get('wm_size', 30),
        color=config.get('wm_color', (255, 255, 255))
    )


def _save_kwargs(config: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'optimize': config.get('optimize_encoding', False),
        'strip_metadata': config.get('strip_metadata', True),
        'lossless': config.get('lossless', False),
    }


def _process_animation(image: Image.Image, config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply the edit pipeline to every frame and re-encode as an animation."""
    frame_count = image.n_frames
    if frame_count > MAX_ANIMATION_FRAMES or frame_count * image.width * image.height > MAX_ANIMATION_PIXELS:
        raise SecurityError(
            f"Animation is too large to process ({frame_count} frames at {image.width}x{image.height}). "
            f"Limit is {MAX_ANIMATION_FRAMES} frames and {MAX_ANIMATION_PIXELS // 1_000_000} megapixels in total."
        )

    frames: List[Image.Image] = []
    durations: List[int] = []
    for frame in ImageSequence.Iterator(image):
        durations.append(int(frame.info.get('duration', 100)) or 100)
        edited = apply_edits(ImageProcessor.normalize_mode(frame.convert('RGBA')), config)
        frames.append(apply_watermark(edited, config))

    output = ImageProcessor.save_animation(
        frames, durations, config.get('output_format', 'WEBP'),
        quality=config.get('quality', 80), lossless=config.get('lossless', False),
        loop=int(image.info.get('loop', 0))
    )
    return {'data': output.getvalue(), 'first_frame': frames[0], 'frame_count': frame_count}


def process_image_task(file_content: bytes, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Worker function to process a single image.
    Args:
        file_content (bytes): The raw bytes of the image file.
        config (dict): Configuration dictionary containing processing parameters.
    Returns:
        dict: On success, a dictionary containing:
            - success (bool): True.
            - original_size (int): Size of the original file in bytes.
            - original_dimensions (tuple[int, int]): Width and height of the original image.
            - processed_size (int): Size of the processed image in bytes.
            - processed_dimensions (tuple[int, int]): Width and height of the processed image.
            - data (bytes): The encoded processed image.
            - has_transparency (bool): Whether the original image has transparency.
            - dominant_colors, histogram_data: Analysis results (if requested).
            - metadata (dict): Privacy-relevant metadata found in the original.
            - animated (bool) / frame_count (int): Whether the output is an animation.
            - target_size (dict|None): Result of "target file size" encoding.
            - format_sizes (dict|None): Bytes per format, if format comparison was requested.
            - responsive (list): Downscaled variants, if requested.
            - icons (dict|None): Icon pack files, if requested.
        On failure, a dictionary containing:
            - success (bool): False.
            - error (str): Error message.
    """
    try:
        # Security: Validate Image Format BEFORE full processing
        # Pass explicitly allowed formats to Image.open to prevent Pillow from attempting to
        # use vulnerable/obscure decoders (like PCX, SGI, TIFF) on maliciously crafted files.
        # Note: HEIC is technically not in Pillow's OPEN dict, pillow_heif uses HEIF for both.
        ALLOWED_FORMATS = ['PNG', 'JPEG', 'BMP', 'WEBP', 'HEIF', 'AVIF', 'GIF']

        # Load Image from bytes with format restrictions
        image = Image.open(io.BytesIO(file_content), formats=ALLOWED_FORMATS)

        # Security: Check dimensions immediately to prevent DoS (Pixel Flood)
        # Note: image.size is available without loading the full raster data
        if image.width > ImageProcessor.MAX_IMAGE_DIMENSION or image.height > ImageProcessor.MAX_IMAGE_DIMENSION:
            error_msg = f"Image dimensions ({image.width}x{image.height}) exceed maximum allowed size ({ImageProcessor.MAX_IMAGE_DIMENSION}px)"
            logger.warning(error_msg)
            raise SecurityError(error_msg)

        original_size = len(file_content)  # Size in bytes of the original uploaded file content
        original_dimensions = image.size

        logger.info(f"Processing image: Size={original_size} bytes, Dimensions={original_dimensions}")

        # Read metadata before anything changes it, so the user can see what stripping removes
        metadata = ImageProcessor.extract_metadata(image)

        output_format = config.get('output_format', 'JPEG')
        is_animated = getattr(image, 'is_animated', False) and getattr(image, 'n_frames', 1) > 1
        animate = is_animated and output_format in ImageProcessor.ANIMATED_FORMATS

        # Check transparency - Check on original image
        original_has_transparency = ImageProcessor.has_transparency(image)

        result: Dict[str, Any] = {
            "success": True,
            "original_size": original_size,
            "original_dimensions": original_dimensions,
            "has_transparency": original_has_transparency,
            "metadata": metadata,
            "animated": False,
            "frame_count": getattr(image, 'n_frames', 1) if is_animated else 1,
            "dominant_colors": [],
            "histogram_data": None,
            "target_size": None,
            "format_sizes": None,
            "responsive": [],
            "icons": None,
        }

        if animate:
            animation = _process_animation(image, config)
            processed_data = animation['data']
            final_image = animation['first_frame']
            result['animated'] = True
            if config.get('extract_colors', False):
                result['dominant_colors'] = ImageProcessor.get_dominant_colors(final_image, 5)
            if config.get('show_histogram', False):
                result['histogram_data'] = ImageProcessor.get_histogram_data(final_image)
            if config.get('make_icons', False):
                result['icons'] = make_icon_pack(final_image)
        else:
            # Apply the camera's EXIF orientation so phone photos aren't sideways
            # (especially once metadata stripping removes the orientation tag).
            ImageOps.exif_transpose(image, in_place=True)

            # Convert palette/16-bit/CMYK/etc. to a mode every later step supports
            image = ImageProcessor.normalize_mode(image)

            # Extract Dominant Colors (if requested) - Calculate on original image
            if config.get('extract_colors', False):
                result['dominant_colors'] = ImageProcessor.get_dominant_colors(image, 5)

            image = apply_edits(image, config)

            # Histogram (if requested)
            if config.get('show_histogram', False):
                result['histogram_data'] = ImageProcessor.get_histogram_data(image)

            # Icons are made before the watermark: text is unreadable at favicon sizes
            if config.get('make_icons', False):
                result['icons'] = make_icon_pack(image)

            final_image = apply_watermark(image, config)
            save_kwargs = _save_kwargs(config)
            quality = config.get('quality', 80)

            # Save/Optimize
            if output_format == 'SVG':
                # Convert to SVG string then to bytes
                processed_data = ImageProcessor.convert_to_svg(final_image, **config).encode('utf-8')
            elif (config.get('target_size_kb') and output_format in ImageProcessor.LOSSY_FORMATS
                  and not save_kwargs['lossless']):
                target_bytes = int(config['target_size_kb'] * 1024)
                output_io, used_quality, met = ImageProcessor.encode_to_target_size(
                    final_image, output_format, target_bytes, max_quality=quality, **save_kwargs
                )
                processed_data = output_io.getvalue()
                result['target_size'] = {'target_bytes': target_bytes, 'quality': used_quality, 'met': met}
            else:
                processed_data = ImageProcessor.process_and_save(final_image, output_format, quality, **save_kwargs).getvalue()

            if config.get('compare_formats', False):
                result['format_sizes'] = ImageProcessor.compare_formats(final_image, quality, **save_kwargs)

            if config.get('responsive_widths') and output_format != 'SVG':
                result['responsive'] = make_responsive_variants(
                    final_image, config['responsive_widths'], output_format, quality=quality, **save_kwargs
                )

        # Performance Optimization (Bolt): return raw bytes, not the processed PIL image,
        # to keep st.session_state small and avoid re-encoding in st.image().
        result['data'] = processed_data
        result['processed_size'] = len(processed_data)
        result['processed_dimensions'] = final_image.size

        logger.info(f"Successfully processed image. Output size: {result['processed_size']} bytes")
        return result
    except (SecurityError, ImageLimitError) as e:
        logger.warning(f"Security error processing image: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
    except UnidentifiedImageError as e:
        logger.warning(f"Unidentified image error: {str(e)}")
        return {
            "success": False,
            "error": "Invalid or corrupt image file."
        }
    except Image.DecompressionBombError as e:
        # Security: Catch decompression bomb errors explicitly to prevent massive stack traces (DoS)
        logger.warning(f"Decompression bomb prevented: {str(e)}")
        return {
            "success": False,
            "error": "Image is too large or highly compressed."
        }
    except Exception as e:
        # Catch-all for unexpected errors to prevent information leakage
        # Log the full details for debugging
        logger.error(f"Error processing image: {str(e)}", exc_info=True)
        # Return a generic message to the user
        return {
            "success": False,
            "error": "An internal error occurred during processing."
        }
