from PIL import Image, ImageOps, ImageEnhance
import io
import pillow_avif
import pillow_heif

# Register HEIF opener
pillow_heif.register_heif_opener()

class ImageProcessor:
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

        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    @staticmethod
    def crop_image(image, left, top, right, bottom):
        """
        Crops the image using the provided coordinates.
        """
        return image.crop((left, top, right, bottom))

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
             data = list(image.getdata())
             image_without_exif = Image.new(image.mode, image.size)
             image_without_exif.putdata(data)
             image = image_without_exif

        image.save(output, **save_args)
        output.seek(0)
        return output
