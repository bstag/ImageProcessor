import io
import json
import os
import sys

import pytest
from PIL import Image, ExifTags

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import tasks
from exports import build_pdf, build_srcset_html, make_icon_pack, make_responsive_variants
from processor import ImageProcessor
from tasks import process_image_task


def encode(img, fmt='PNG', **kwargs):
    buf = io.BytesIO()
    img.save(buf, fmt, **kwargs)
    return buf.getvalue()


def decode(data):
    return Image.open(io.BytesIO(data))


def noisy(size=(400, 300)):
    return Image.effect_noise(size, 80).convert('RGB')


def animated_gif(frames=4, size=(40, 30)):
    images = [Image.new('RGB', size, (i * 60, 50, 200 - i * 40)) for i in range(frames)]
    buf = io.BytesIO()
    images[0].save(buf, 'GIF', save_all=True, append_images=images[1:], duration=[50, 100, 150, 200][:frames], loop=0)
    return buf.getvalue()


# --- Target file size -------------------------------------------------------

def photo_like(size=(400, 300)):
    """A smooth gradient with light grain: compresses like a real photo, unlike pure noise."""
    gradient = Image.linear_gradient('L').resize(size).convert('RGB')
    return Image.blend(gradient, Image.effect_noise(size, 30).convert('RGB'), 0.2)


@pytest.mark.parametrize("fmt", ['JPEG', 'WEBP', 'AVIF'])
def test_target_size_picks_highest_quality_that_fits(fmt):
    img = photo_like()
    target = ImageProcessor.process_and_save(img, fmt, quality=60).getbuffer().nbytes
    output, quality, met = ImageProcessor.encode_to_target_size(img, fmt, target, max_quality=95)
    assert met
    assert output.getbuffer().nbytes <= target
    assert quality >= 60
    if quality < 95:
        # One step higher must not fit, otherwise quality was left on the table
        assert ImageProcessor.process_and_save(img, fmt, quality=quality + 1).getbuffer().nbytes > target


def test_target_size_through_task():
    result = process_image_task(encode(photo_like()), {'output_format': 'JPEG', 'quality': 90, 'target_size_kb': 8})
    assert result['success'], result.get('error')
    assert result['target_size']['met']
    assert result['processed_size'] <= 8 * 1024
    assert result['target_size']['quality'] <= 90


def test_unreachable_target_reports_not_met():
    result = process_image_task(encode(noisy((800, 800))), {'output_format': 'JPEG', 'target_size_kb': 5})
    assert result['success']
    assert result['target_size'] == {'target_bytes': 5 * 1024, 'quality': 5, 'met': False}


def test_target_size_ignored_for_lossless_formats():
    result = process_image_task(encode(noisy()), {'output_format': 'PNG', 'target_size_kb': 5})
    assert result['target_size'] is None


# --- Format comparison ------------------------------------------------------

def test_compare_formats_reports_every_format():
    result = process_image_task(encode(noisy()), {'output_format': 'WEBP', 'compare_formats': True})
    assert set(result['format_sizes']) == {'WEBP', 'AVIF', 'JPEG', 'PNG'}
    assert all(size > 0 for size in result['format_sizes'].values())


# --- Presets: Fit Within resize ----------------------------------------------

def test_fit_within_shrinks_large_images_only():
    big = process_image_task(encode(noisy((3000, 1500))), {'output_format': 'PNG', 'resize_type': 'Fit Within', 'width': 1920, 'height': 1920})
    small = process_image_task(encode(noisy((400, 300))), {'output_format': 'PNG', 'resize_type': 'Fit Within', 'width': 1920, 'height': 1920})
    assert big['processed_dimensions'] == (1920, 960)
    assert small['processed_dimensions'] == (400, 300)


# --- Metadata viewer ----------------------------------------------------------

def photo_with_metadata(gps=True):
    exif = Image.new('RGB', (1, 1)).getexif()
    exif[ExifTags.Base.Make] = "Canon"
    exif[ExifTags.Base.Model] = "EOS R5"
    exif[ExifTags.Base.Software] = "Firmware 1.0"
    if gps:
        exif.get_ifd(ExifTags.IFD.GPSInfo).update({
            ExifTags.GPS.GPSLatitudeRef: 'N', ExifTags.GPS.GPSLatitude: (47.0, 36.0, 0.0),
            ExifTags.GPS.GPSLongitudeRef: 'W', ExifTags.GPS.GPSLongitude: (122.0, 20.0, 0.0),
        })
    return encode(Image.new('RGB', (40, 30)), 'JPEG', exif=exif)


def test_metadata_reports_camera_and_gps():
    result = process_image_task(photo_with_metadata(), {'output_format': 'JPEG'})
    assert result['metadata']['has_gps']
    assert result['metadata']['fields']['Camera'] == "Canon EOS R5"
    assert result['metadata']['fields']['Software'] == "Firmware 1.0"
    # Stripping removes the GPS data from the output
    assert not decode(result['data']).getexif().get_ifd(ExifTags.IFD.GPSInfo)


def test_metadata_without_gps():
    result = process_image_task(photo_with_metadata(gps=False), {'output_format': 'JPEG'})
    assert not result['metadata']['has_gps']
    assert 'GPS location' not in result['metadata']['fields']


def test_metadata_values_are_cleaned_and_truncated():
    exif = Image.new('RGB', (1, 1)).getexif()
    exif[ExifTags.Base.Artist] = "A" * 300 + "\x07"
    meta = ImageProcessor.extract_metadata(decode(encode(Image.new('RGB', (4, 4)), 'JPEG', exif=exif)))
    assert meta['fields']['Artist'] == "A" * 100


# --- Social presets -----------------------------------------------------------

@pytest.mark.parametrize("fit", ['crop', 'pad'])
def test_social_preset_outputs_exact_size(fit):
    config = {'output_format': 'PNG', 'crop_mode': 'Social Preset', 'social_size': (1200, 630),
              'social_fit': fit, 'social_pad_color': (0, 0, 0)}
    result = process_image_task(encode(noisy((500, 500))), config)
    assert decode(result['data']).size == (1200, 630)
    if fit == 'pad':
        assert decode(result['data']).getpixel((5, 315)) == (0, 0, 0)


def test_social_pad_works_for_grayscale_and_alpha():
    for mode in ('L', 'LA', 'RGBA'):
        out = ImageProcessor.fit_to_size(Image.new(mode, (50, 100)), (100, 100), 'pad', (255, 255, 255))
        assert out.size == (100, 100) and out.mode == mode


# --- Animated GIF -------------------------------------------------------------

@pytest.mark.parametrize("fmt", ['WEBP', 'AVIF', 'PNG'])
def test_animated_gif_keeps_animation_and_edits(fmt):
    config = {'output_format': fmt, 'rotate': 90, 'watermark_text': 'hi', 'wm_size': 10}
    result = process_image_task(animated_gif(), config)
    assert result['success'], result.get('error')
    assert result['animated'] and result['frame_count'] == 4
    out = decode(result['data'])
    assert getattr(out, 'n_frames', 1) == 4
    assert out.size == (30, 40)  # rotated


def test_animated_gif_to_still_format_keeps_first_frame():
    result = process_image_task(animated_gif(), {'output_format': 'JPEG'})
    assert result['success']
    assert not result['animated'] and result['frame_count'] == 4


def test_animation_frame_limit(monkeypatch):
    monkeypatch.setattr(tasks, 'MAX_ANIMATION_FRAMES', 3)
    result = process_image_task(animated_gif(frames=4), {'output_format': 'WEBP'})
    assert not result['success']
    assert "Animation is too large" in result['error']


# --- Icon pack ----------------------------------------------------------------

def test_icon_pack_contents_and_sizes():
    files = make_icon_pack(Image.new('RGBA', (300, 120), (0, 120, 255, 255)))
    assert set(files) == {'favicon.ico', 'favicon-16x16.png', 'favicon-32x32.png', 'apple-touch-icon.png',
                          'android-chrome-192x192.png', 'android-chrome-512x512.png', 'site.webmanifest', 'icons.html'}
    assert sorted(decode(files['favicon.ico']).info['sizes']) == [(16, 16), (32, 32), (48, 48)]
    for name, size in (('favicon-32x32.png', 32), ('apple-touch-icon.png', 180), ('android-chrome-512x512.png', 512)):
        assert decode(files[name]).size == (size, size)
    # Non-square input is padded, not cropped; the Apple icon has no transparency
    assert decode(files['android-chrome-512x512.png']).getpixel((256, 5))[3] == 0
    assert decode(files['apple-touch-icon.png']).mode == 'RGB'
    assert json.loads(files['site.webmanifest'])['icons'][1]['sizes'] == '512x512'


def test_icons_are_made_before_watermark():
    config = {'output_format': 'PNG', 'make_icons': True, 'watermark_text': 'WATERMARK', 'wm_size': 200, 'wm_opacity': 255}
    result = process_image_task(encode(Image.new('RGB', (600, 600), (0, 0, 0))), config)
    icon = decode(result['icons']['android-chrome-512x512.png']).convert('RGB')
    assert icon.getextrema() == ((0, 0), (0, 0), (0, 0))  # no white watermark pixels


# --- Responsive sets ----------------------------------------------------------

def test_responsive_variants_never_upscale():
    variants = make_responsive_variants(noisy((1000, 500)), [320, 640, 1280], 'WEBP', quality=80)
    assert [(v['width'], v['height']) for v in variants] == [(320, 160), (640, 320)]
    assert decode(variants[0]['data']).size == (320, 160)


def test_responsive_through_task_and_srcset():
    result = process_image_task(encode(noisy((1000, 500))), {'output_format': 'WEBP', 'responsive_widths': [320, 640]})
    assert [v['width'] for v in result['responsive']] == [320, 640]
    snippet = build_srcset_html([{
        'full_name': 'processed_a.webp', 'full_width': 1000, 'full_height': 500, 'name_stem': 'a', 'ext': 'webp',
        'alt': 'a <b>', 'variants': result['responsive'],
    }])
    assert 'srcset="responsive/a-320w.webp 320w, responsive/a-640w.webp 640w, processed_a.webp 1000w"' in snippet
    assert 'alt="a &lt;b&gt;"' in snippet


# --- PDF ----------------------------------------------------------------------

def test_pdf_has_one_page_per_image():
    pdf = build_pdf([encode(noisy((100, 50))), encode(Image.new('RGBA', (30, 30), (0, 0, 0, 0))), encode(noisy(), 'JPEG')])
    import re
    assert pdf.startswith(b'%PDF')
    assert len(re.findall(rb'/Type\s*/Page(?!s)', pdf)) == 3


def test_pdf_requires_images():
    with pytest.raises(ValueError):
        build_pdf([])


# --- Results ZIP --------------------------------------------------------------

def test_results_zip_layout_and_unique_names():
    import zipfile
    from exports import assign_output_names, build_results_zip

    variants = make_responsive_variants(noisy((800, 400)), [320], 'WEBP')
    items = [
        {'name': '../../evil/photo.png', 'data': b'one', 'responsive': variants, 'processed_dimensions': (800, 400),
         'icons': {'favicon.ico': b'ico'}, 'alt': 'photo.png'},
        {'name': 'photo.jpg', 'data': b'two', 'responsive': [], 'icons': None},
    ]
    assign_output_names(items, 'webp')
    assert [item['file_name'] for item in items] == ['processed_photo.webp', 'processed_photo_1.webp']

    archive = zipfile.ZipFile(io.BytesIO(build_results_zip(items, 'webp', pdf_data=b'%PDF')))
    assert sorted(archive.namelist()) == sorted([
        'processed_photo.webp', 'processed_photo_1.webp', 'responsive/photo-320w.webp',
        'icons/photo/favicon.ico', 'srcset.html', 'processed_images.pdf',
    ])
    assert 'responsive/photo-320w.webp 320w, processed_photo.webp 800w' in archive.read('srcset.html').decode()
    assert all('..' not in name for name in archive.namelist())
