"""
Extra export bundles built from processed images: favicon/app icon packs,
responsive image sets with a srcset snippet, and multi-page PDFs.
"""
import html
import io
import json
import zipfile
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

from processor import ImageProcessor
from utils import get_safe_filename_stem  # Security: strips paths to prevent zip slip

# Standard favicon / touch icon / PWA icon set
ICON_PNG_SIZES = {
    'favicon-16x16.png': 16,
    'favicon-32x32.png': 32,
    'apple-touch-icon.png': 180,
    'android-chrome-192x192.png': 192,
    'android-chrome-512x512.png': 512,
}
ICO_SIZES = [(16, 16), (32, 32), (48, 48)]

RESPONSIVE_WIDTH_OPTIONS = [320, 640, 1024, 1280, 1920]


def _square(image: Image.Image, size: int, background: Tuple[int, int, int, int]) -> Image.Image:
    """Fit the whole image into a size x size square, centred on `background`."""
    icon = image.convert('RGBA')
    icon.thumbnail((size, size), Image.Resampling.LANCZOS)
    canvas = Image.new('RGBA', (size, size), background)
    canvas.alpha_composite(icon, ((size - icon.width) // 2, (size - icon.height) // 2))
    return canvas


def make_icon_pack(image: Image.Image) -> Dict[str, bytes]:
    """
    Build a favicon/app icon set from an image. Non-square images are padded (not cropped)
    so logos keep their edges. The Apple touch icon gets a white background because iOS
    renders transparency as black.
    """
    transparent = (0, 0, 0, 0)
    files: Dict[str, bytes] = {}

    buf = io.BytesIO()
    _square(image, 256, transparent).save(buf, 'ICO', sizes=ICO_SIZES)
    files['favicon.ico'] = buf.getvalue()

    for name, size in ICON_PNG_SIZES.items():
        background = (255, 255, 255, 255) if name == 'apple-touch-icon.png' else transparent
        icon = _square(image, size, background)
        if name == 'apple-touch-icon.png':
            icon = icon.convert('RGB')
        buf = io.BytesIO()
        icon.save(buf, 'PNG', optimize=True)
        files[name] = buf.getvalue()

    files['site.webmanifest'] = json.dumps({
        'icons': [
            {'src': '/android-chrome-192x192.png', 'sizes': '192x192', 'type': 'image/png'},
            {'src': '/android-chrome-512x512.png', 'sizes': '512x512', 'type': 'image/png'},
        ],
        'display': 'standalone',
    }, indent=2).encode('utf-8')
    files['icons.html'] = ICON_HTML_SNIPPET.encode('utf-8')
    return files


ICON_HTML_SNIPPET = """<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
"""


def make_responsive_variants(image: Image.Image, widths: List[int], output_format: str,
                             **save_kwargs: Any) -> List[Dict[str, Any]]:
    """
    Encode downscaled copies of `image` at each requested width narrower than the image.
    Never upscales. Returns [{'width', 'height', 'data'}] sorted by width.
    """
    variants = []
    for width in sorted(set(widths)):
        if width >= image.width:
            continue
        resized = ImageProcessor.resize_image(image, width=width, maintain_aspect_ratio=True)
        data = ImageProcessor.process_and_save(resized, output_format, **save_kwargs).getvalue()
        variants.append({'width': resized.width, 'height': resized.height, 'data': data})
    return variants


def responsive_filename(name_stem: str, width: int, ext: str) -> str:
    return f"responsive/{name_stem}-{width}w.{ext}"


def build_srcset_html(entries: List[Dict[str, Any]]) -> str:
    """
    Build <img srcset> tags. Each entry needs: full_name, full_width, full_height,
    name_stem, ext, alt and variants (from make_responsive_variants).
    """
    tags = []
    for entry in entries:
        sources = [f"{responsive_filename(entry['name_stem'], v['width'], entry['ext'])} {v['width']}w"
                   for v in entry['variants']]
        sources.append(f"{entry['full_name']} {entry['full_width']}w")
        tags.append(
            f'<img src="{html.escape(entry["full_name"])}"\n'
            f'     srcset="{html.escape(", ".join(sources))}"\n'
            f'     sizes="100vw" width="{entry["full_width"]}" height="{entry["full_height"]}"\n'
            f'     alt="{html.escape(entry["alt"])}" loading="lazy" decoding="async">'
        )
    return "\n\n".join(tags) + "\n"


def assign_output_names(items: List[Dict[str, Any]], ext: str) -> None:
    """
    Give each processed item a unique, sanitized 'unique_stem' and 'file_name' so the ZIP,
    individual downloads and srcset snippets all agree (and duplicate uploads don't collide).
    """
    seen = set()
    for item in items:
        base_stem = get_safe_filename_stem(item['name'])
        stem, counter = base_stem, 1
        while stem in seen:
            stem = f"{base_stem}_{counter}"
            counter += 1
        seen.add(stem)
        item['unique_stem'] = stem
        item['file_name'] = f"processed_{stem}.{ext}"


def zip_files(files: Dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    return buf.getvalue()


def build_results_zip(items: List[Dict[str, Any]], ext: str, pdf_data: Optional[bytes] = None) -> bytes:
    """
    ZIP every processed image plus any responsive variants (responsive/), icon packs
    (icons/<name>/), a combined srcset.html and the PDF. Call assign_output_names first.
    """
    buf = io.BytesIO()
    srcset_entries = []
    with zipfile.ZipFile(buf, "w") as zf:
        for item in items:
            zf.writestr(item['file_name'], item['data'])
            for variant in item.get('responsive') or []:
                zf.writestr(responsive_filename(item['unique_stem'], variant['width'], ext), variant['data'])
            if item.get('responsive'):
                width, height = item['processed_dimensions']
                srcset_entries.append({
                    'full_name': item['file_name'], 'full_width': width, 'full_height': height,
                    'name_stem': item['unique_stem'], 'ext': ext,
                    'alt': item.get('alt', item['unique_stem']), 'variants': item['responsive'],
                })
            for icon_name, icon_data in (item.get('icons') or {}).items():
                zf.writestr(f"icons/{item['unique_stem']}/{icon_name}", icon_data)
        if srcset_entries:
            zf.writestr("srcset.html", build_srcset_html(srcset_entries))
        if pdf_data:
            zf.writestr("processed_images.pdf", pdf_data)
    return buf.getvalue()


def build_pdf(images_data: List[bytes], resolution: float = 96.0) -> bytes:
    """
    Combine encoded images (any format Pillow can read; first frame of animations)
    into one PDF with a page per image, sized to the image at `resolution` DPI.
    """
    pages = []
    for data in images_data:
        page = Image.open(io.BytesIO(data))
        page.seek(0)
        if ImageProcessor.has_transparency(page):
            flat = Image.new('RGB', page.size, (255, 255, 255))
            rgba = page.convert('RGBA')
            flat.paste(rgba, mask=rgba.getchannel('A'))
            page = flat
        else:
            page = page.convert('RGB')
        pages.append(page)
    if not pages:
        raise ValueError("No images to combine into a PDF")
    buf = io.BytesIO()
    pages[0].save(buf, 'PDF', save_all=True, append_images=pages[1:], resolution=resolution)
    return buf.getvalue()
