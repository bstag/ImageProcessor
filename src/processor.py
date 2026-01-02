from PIL import Image, ImageOps, ImageEnhance
import io
import pillow_avif
import pillow_heif

# Register HEIF opener
pillow_heif.register_heif_opener()

class ImageProcessor:
    MAX_IMAGE_DIMENSION = 10000

    @staticmethod
    def center_crop_to_aspect(image, target_w, target_h):
        w, h = image.size
        if target_w <= 0 or target_h <= 0:
            return image
        target_ratio = target_w / target_h
        current_ratio = w / h
        if current_ratio > target_ratio:
            new_w = int(h * target_ratio)
            left = (w - new_w) // 2
            right = left + new_w
            top = 0
            bottom = h
        else:
            new_h = int(w / target_ratio)
            top = (h - new_h) // 2
            bottom = top + new_h
            left = 0
            right = w
        return image.crop((left, top, right, bottom))
    @staticmethod
    def apply_enhancements(image, brightness=1.0, contrast=1.0, sharpness=1.0, saturation=1.0):
        """
        Applies color and sharpness enhancements to the image.
        """
        if brightness != 1.0:
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(brightness)
        
        if contrast != 1.0:
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(contrast)

        if saturation != 1.0:
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(saturation)
            
        if sharpness != 1.0:
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(sharpness)
            
        return image

    @staticmethod
    def apply_transforms(image, rotate=0, flip_horizontal=False, flip_vertical=False, grayscale=False):
        """
        Applies geometric transformations and filters.
        """
        if grayscale:
            image = image.convert('L').convert('RGB') # Convert back to RGB to maintain compatibility

        if rotate != 0:
            # Expand=True ensures the image is not cropped if rotated by non-90 degrees,
            # though here we expect 90 degree steps usually.
            image = image.rotate(-rotate, expand=True) 

        if flip_horizontal:
            image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            
        if flip_vertical:
            image = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            
        return image

    @staticmethod
    def resize_image(image, width=None, height=None, percentage=None, maintain_aspect_ratio=True):
        """
        Resizes the image based on provided parameters.
        """
        original_width, original_height = image.size
        new_width, new_height = original_width, original_height

        if percentage:
            scale = percentage / 100
            new_width = int(original_width * scale)
            new_height = int(original_height * scale)
        elif width and height:
            if maintain_aspect_ratio:
                # thumbnail modifies the image in-place to fit within the box, preserving aspect ratio.
                # We need to verify that the target box itself isn't too large, though thumbnail won't exceed it.
                if width > ImageProcessor.MAX_IMAGE_DIMENSION or height > ImageProcessor.MAX_IMAGE_DIMENSION:
                     raise ValueError(f"Target dimensions exceed maximum allowed size ({ImageProcessor.MAX_IMAGE_DIMENSION}px)")

                image.thumbnail((width, height), Image.Resampling.LANCZOS)
                return image
            else:
                new_width = width
                new_height = height
        elif width:
            new_width = width
            if maintain_aspect_ratio:
                ratio = width / original_width
                new_height = int(original_height * ratio)
        elif height:
            new_height = height
            if maintain_aspect_ratio:
                ratio = height / original_height
                new_width = int(original_width * ratio)

        # Validate dimensions before resizing
        if new_width > ImageProcessor.MAX_IMAGE_DIMENSION or new_height > ImageProcessor.MAX_IMAGE_DIMENSION:
            raise ValueError(f"Resulting image dimensions ({new_width}x{new_height}) exceed maximum allowed size ({ImageProcessor.MAX_IMAGE_DIMENSION}px)")

        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    @staticmethod
    def crop_image(image, left, top, right, bottom):
        """
        Crops the image using the provided coordinates.
        """
        return image.crop((left, top, right, bottom))

    @staticmethod
    def has_transparency(image):
        """
        Checks if the image has transparency (alpha channel or transparency info).
        """
        if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
            return True
        return False

    @staticmethod
    def replace_color_with_transparency(image, target_color, tolerance=0):
        """
        Replaces a target color with transparency.
        target_color: tuple (R, G, B)
        tolerance: int (0-255)
        """
        image = image.convert("RGBA")
        datas = image.getdata()
        
        new_data = []
        r_target, g_target, b_target = target_color[:3]
        
        for item in datas:
            # item is (R, G, B, A)
            if (abs(item[0] - r_target) <= tolerance and
                abs(item[1] - g_target) <= tolerance and
                abs(item[2] - b_target) <= tolerance):
                new_data.append((item[0], item[1], item[2], 0))
            else:
                new_data.append(item)
        
        image.putdata(new_data)
        return image

    @staticmethod
    def process_and_save(image, output_format, quality=85, optimize=True, strip_metadata=True, lossless=False):
        """
        Process the image (conversion, compression) and return the bytes.
        """
        # Convert to RGB if saving to formats that don't support RGBA (like JPEG)
        if output_format.upper() in ['JPEG', 'JPG', 'BMP'] and image.mode == 'RGBA':
            image = image.convert('RGB')
        
        output = io.BytesIO()
        
        save_args = {
            "format": output_format,
            "quality": quality,
            "optimize": optimize
        }

        # Add lossless param if supported (WebP, AVIF)
        if output_format.upper() in ['WEBP', 'AVIF']:
             save_args['lossless'] = lossless
        
        # Metadata stripping is implicit if we don't copy exif, but we can be explicit
        if strip_metadata:
             # Create a new image data without metadata
             # Optimized: Efficiently copy pixel data to new image without metadata
             # Previous implementation using list(getdata()) was O(N) in Python space
             image_without_exif = Image.new(image.mode, image.size)
             image_without_exif.paste(image)
             image = image_without_exif

        image.save(output, **save_args)
        output.seek(0)
        return output
