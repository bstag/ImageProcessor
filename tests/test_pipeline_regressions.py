import io
import os
import sys

import pytest
from PIL import Image

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from processor import ImageProcessor
from tasks import process_image_task


def encode(img, fmt='PNG', **kwargs):
    buf = io.BytesIO()
    img.save(buf, fmt, **kwargs)
    return buf.getvalue()


def decode(data):
    return Image.open(io.BytesIO(data))


@pytest.fixture
def noisy_png():
    return encode(Image.effect_noise((100, 80), 60).convert('RGB'))


def test_ui_filter_names_are_applied(noisy_png):
    plain = process_image_task(noisy_png, {'output_format': 'PNG'})['data']
    for ui_name in ["Blur", "Edge Enhance", "Smooth"]:
        filtered = process_image_task(noisy_png, {'output_format': 'PNG', 'filter_type': ui_name})['data']
        assert filtered != plain, f"{ui_name} filter had no effect"


def test_custom_crop_trims_pixels_from_each_edge(noisy_png):
    config = {'output_format': 'PNG', 'crop_mode': 'Custom Box',
              'crop_left': 5, 'crop_top': 0, 'crop_right': 10, 'crop_bottom': 20}
    result = process_image_task(noisy_png, config)
    assert decode(result['data']).size == (85, 60)


def test_custom_crop_never_produces_empty_image(noisy_png):
    config = {'output_format': 'PNG', 'crop_mode': 'Custom Box',
              'crop_left': 500, 'crop_top': 500, 'crop_right': 500, 'crop_bottom': 500}
    result = process_image_task(noisy_png, config)
    assert result['success']
    assert decode(result['data']).size == (1, 1)


def test_exif_orientation_is_applied():
    exif = Image.new('RGB', (1, 1)).getexif()
    exif[0x0112] = 6  # Rotated 90 CW
    photo = encode(Image.new('RGB', (100, 50)), 'JPEG', exif=exif)
    result = process_image_task(photo, {'output_format': 'JPEG'})
    assert decode(result['data']).size == (50, 100)


@pytest.mark.parametrize("mode", ['LA', 'P', 'PA', '1', 'CMYK', 'I;16', 'I', 'F'])
@pytest.mark.parametrize("fmt", ['JPEG', 'BMP', 'PNG', 'WEBP'])
def test_every_input_mode_can_be_saved(mode, fmt):
    base = Image.effect_noise((16, 16), 60)
    img = base.convert('I').convert('I;16') if mode == 'I;16' else base.convert(mode)
    out = ImageProcessor.process_and_save(img, fmt)
    assert decode(out.getvalue()).size == (16, 16)


def test_16bit_grayscale_is_scaled_not_clipped():
    img = Image.new('I;16', (4, 4), 32768)  # mid-grey in 16-bit
    assert ImageProcessor.normalize_mode(img).getpixel((0, 0)) == 128


def test_palette_png_supports_enhancements():
    palette_png = encode(Image.effect_noise((32, 32), 60).convert('RGB').convert('P'))
    result = process_image_task(palette_png, {'output_format': 'JPEG', 'brightness': 1.5, 'filter_type': 'Blur'})
    assert result['success'], result.get('error')


def test_transparency_flattens_to_white_for_jpeg():
    transparent = encode(Image.new('RGBA', (20, 20), (255, 0, 0, 0)))
    result = process_image_task(transparent, {'output_format': 'JPEG'})
    r, g, b = decode(result['data']).getpixel((5, 5))
    assert min(r, g, b) > 245
