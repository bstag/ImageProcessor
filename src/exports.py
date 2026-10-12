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

# Favicon / touch icon / PWA / tile / store icon set: filename -> (size, style)
#   'transparent': keeps transparency
#   'opaque':      flattened onto white (iOS shows transparency as black; the App Store rejects it)
#   'maskable':    opaque, with the image shrunk into the Android adaptive-icon safe zone
ICON_PNG_SPECS = {
    'favicon-16x16.png': (16, 'transparent'),
    'favicon-32x32.png': (32, 'transparent'),
    'mstile-150x150.png': (150, 'transparent'),
    'apple-touch-icon.png': (180, 'opaque'),
    'android-chrome-192x192.png': (192, 'transparent'),
    'android-chrome-512x512.png': (512, 'transparent'),
    'maskable-icon-192x192.png': (192, 'maskable'),
    'maskable-icon-512x512.png': (512, 'maskable'),
    'app-store-icon-1024x1024.png': (1024, 'opaque'),
}
ICO_SIZES = [(16, 16), (32, 32), (48, 48), (64, 64), (256, 256)]

# Maskable icons may be cropped to any shape containing a centred circle of radius 40%
# of the icon, so the image's corners must fit inside that circle.
MASKABLE_SAFE_ZONE_RADIUS = 0.40

ICON_BACKGROUND = (255, 255, 255, 255)
TRANSPARENT = (0, 0, 0, 0)

RESPONSIVE_WIDTH_OPTIONS = [320, 640, 1024, 1280, 1920]


def _square(image: Image.Image, size: int, background: Tuple[int, int, int, int],
            content_size: Optional[Tuple[int, int]] = None) -> Image.Image:
    """
    Scale the whole image (up or down) to fit `content_size` (default: the full square),
    centred on a size x size `background`. Non-square images are padded, never cropped.
    """
    icon = image.convert('RGBA')
    box = content_size or (size, size)
    scale = min(box[0] / icon.width, box[1] / icon.height)
    icon = icon.resize((max(1, round(icon.width * scale)), max(1, round(icon.height * scale))),
                       Image.Resampling.LANCZOS)
    canvas = Image.new('RGBA', (size, size), background)
    canvas.alpha_composite(icon, ((size - icon.width) // 2, (size - icon.height) // 2))
    return canvas


def _maskable(image: Image.Image, size: int) -> Image.Image:
    """Shrink the image so its corners fall inside the maskable safe-zone circle."""
    diagonal = (image.width ** 2 + image.height ** 2) ** 0.5
    scale = (2 * MASKABLE_SAFE_ZONE_RADIUS * size) / diagonal
    content = (max(1, int(image.width * scale)), max(1, int(image.height * scale)))
    return _square(image, size, ICON_BACKGROUND, content_size=content)


def _icon(image: Image.Image, size: int, style: str) -> Image.Image:
    if style == 'maskable':
        return _maskable(image, size).convert('RGB')
    if style == 'opaque':
        return _square(image, size, ICON_BACKGROUND).convert('RGB')
    return _square(image, size, TRANSPARENT)


def make_icon_pack(image: Image.Image) -> Dict[str, bytes]:
    """
    Build a favicon / app icon set from an image: a multi-size favicon.ico, PNG favicons,
    Apple touch icon, Android/PWA icons (regular and maskable), a Windows tile, a 1024px
    App Store icon, plus site.webmanifest, browserconfig.xml and the HTML tags to use them.
    """
    files: Dict[str, bytes] = {}

    buf = io.BytesIO()
    _square(image, 256, TRANSPARENT).save(buf, 'ICO', sizes=ICO_SIZES)
    files['favicon.ico'] = buf.getvalue()

    for name, (size, style) in ICON_PNG_SPECS.items():
        buf = io.BytesIO()
        _icon(image, size, style).save(buf, 'PNG', optimize=True)
        files[name] = buf.getvalue()

    files['site.webmanifest'] = json.dumps({
        'icons': [
            {'src': '/android-chrome-192x192.png', 'sizes': '192x192', 'type': 'image/png'},
            {'src': '/android-chrome-512x512.png', 'sizes': '512x512', 'type': 'image/png'},
            {'src': '/maskable-icon-192x192.png', 'sizes': '192x192', 'type': 'image/png', 'purpose': 'maskable'},
            {'src': '/maskable-icon-512x512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'},
        ],
        'display': 'standalone',
    }, indent=2).encode('utf-8')
    files['browserconfig.xml'] = BROWSERCONFIG_XML.encode('utf-8')
    files['icons.html'] = ICON_HTML_SNIPPET.encode('utf-8')
    return files


BROWSERCONFIG_XML = """<?xml version="1.0" encoding="utf-8"?>
<browserconfig>
  <msapplication>
    <tile>
      <square150x150logo src="/mstile-150x150.png"/>
      <TileColor>#ffffff</TileColor>
    </tile>
  </msapplication>
</browserconfig>
"""

ICON_HTML_SNIPPET = """<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta name="msapplication-TileColor" content="#ffffff">
<meta name="msapplication-config" content="/browserconfig.xml">
<!-- app-store-icon-1024x1024.png is for App Store / Play Store listings, not for the page -->
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
