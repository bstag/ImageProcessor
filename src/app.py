import streamlit as st
import html
import base64
import pandas as pd
from batch import BatchResult, run_batch
from processor import ImageProcessor
from utils import format_bytes, validate_upload_constraints, sanitize_filename, escape_markdown
from exports import RESPONSIVE_WIDTH_OPTIONS, build_srcset_html

# Default values for settings that presets can change (widgets are keyed by these names)
SETTING_DEFAULTS = {
    'opt_preset': 'Custom',
    'opt_format': 'WEBP',
    'opt_quality': 80,
    'opt_lossless': False,
    'opt_target_size': False,
    'opt_strip_metadata': True,
    'opt_optimize': False,
    'opt_resize_type': 'None',
    'opt_width': 800,
    'opt_height': 600,
    'opt_maintain_aspect': True,
}

PRESETS = {
    "Web": {
        'description': "WebP, 80% quality, max 1920px. Good default for websites.",
        'settings': {'opt_format': 'WEBP', 'opt_quality': 80, 'opt_resize_type': 'Fit Within',
                     'opt_width': 1920, 'opt_height': 1920, 'opt_strip_metadata': True, 'opt_optimize': True},
    },
    "Email": {
        'description': "JPEG, 75% quality, max 1280px. Small attachments that open anywhere.",
        'settings': {'opt_format': 'JPEG', 'opt_quality': 75, 'opt_resize_type': 'Fit Within',
                     'opt_width': 1280, 'opt_height': 1280, 'opt_strip_metadata': True, 'opt_optimize': True},
    },
    "Social Media": {
        'description': "JPEG, 85% quality, max 2048px. Sharp uploads that platforms won't over-compress.",
        'settings': {'opt_format': 'JPEG', 'opt_quality': 85, 'opt_resize_type': 'Fit Within',
                     'opt_width': 2048, 'opt_height': 2048, 'opt_strip_metadata': True, 'opt_optimize': True},
    },
    "Thumbnail": {
        'description': "WebP, 70% quality, max 400px. Previews and galleries.",
        'settings': {'opt_format': 'WEBP', 'opt_quality': 70, 'opt_resize_type': 'Fit Within',
                     'opt_width': 400, 'opt_height': 400, 'opt_strip_metadata': True, 'opt_optimize': True},
    },
}

SOCIAL_SIZES = {
    "Square 1:1 (1080×1080)": (1080, 1080),
    "Portrait 4:5 (1080×1350)": (1080, 1350),
    "Landscape 16:9 (1920×1080)": (1920, 1080),
    "Story 9:16 (1080×1920)": (1080, 1920),
    "Link Preview (1200×630)": (1200, 630),
}

MIME_SUBTYPES = {"svg": "svg+xml", "jpg": "jpeg"}


def _apply_preset():
    preset = PRESETS.get(st.session_state.opt_preset)
    if preset:
        for key, value in preset['settings'].items():
            st.session_state[key] = value
        st.session_state.opt_lossless = False
        st.session_state.opt_target_size = False


def _mark_custom():
    """Any manual change to a preset-controlled setting switches the preset back to Custom."""
    st.session_state.opt_preset = "Custom"


def _hex_to_rgb(color: str):
    color = color.lstrip('#')
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def render_settings():
    # Re-seed keys for controls that may have been hidden on the previous run.
    for key, value in SETTING_DEFAULTS.items():
        st.session_state.setdefault(key, value)

    # Sidebar Configuration
    st.sidebar.header("Settings")

    preset = st.sidebar.selectbox(
        "Preset",
        ["Custom", *PRESETS],
        key='opt_preset',
        on_change=_apply_preset,
        help="Apply recommended settings in one click. Changing any of those settings afterwards switches back to Custom."
    )
    if preset in PRESETS:
        st.sidebar.caption(PRESETS[preset]['description'])

    # Output Format
    st.sidebar.subheader("Output Format")
    format_descriptions = {
        "WEBP": "WEBP (Web Optimized)",
        "AVIF": "AVIF (Next-Gen Compression)",
        "JPEG": "JPEG (Standard)",
        "PNG": "PNG (Lossless)",
        "BMP": "BMP (Uncompressed)",
        "SVG": "SVG (Vectorize)"
    }
    output_format = st.sidebar.selectbox(
        "Format",
        [*ImageProcessor.RASTER_OUTPUT_FORMATS, "SVG"],
        key='opt_format',
        on_change=_mark_custom,
        format_func=lambda x: format_descriptions.get(x, x),
        help=f"Select the file format for the processed images. WebP and AVIF offer better compression. SVG converts to vector (images larger than {ImageProcessor.MAX_SVG_DIMENSION}px are downscaled before tracing)."
    )

    lossless_disabled = output_format not in ImageProcessor.LOSSLESS_OPTION_FORMATS
    lossless_help_suffix = " (Select WebP above to enable)" if lossless_disabled else ""
    lossless_val = st.sidebar.checkbox(
        "Lossless Compression",
        key='opt_lossless',
        on_change=_mark_custom,
        disabled=lossless_disabled,
        help=f"Retain perfect quality at the cost of larger file size. Available for WebP.{lossless_help_suffix}"
    )
    lossless = lossless_val if not lossless_disabled else False

    quality_disabled = lossless or output_format not in ImageProcessor.LOSSY_FORMATS
    quality_help = "Adjust compression level. Lower values result in smaller files but lower quality."

    if lossless:
        quality_help = "Quality selection is disabled because Lossless Compression is active."
    elif output_format == "SVG":
        quality_help = "Quality slider is not used for SVG conversion. Configure SVG settings below."
    elif quality_disabled:
        quality_help = f"Quality selection is not applicable for {output_format} format."

    quality_val = st.sidebar.slider(
        "Quality",
        0,
        100,
        key='opt_quality',
        on_change=_mark_custom,
        disabled=quality_disabled,
        help=quality_help,
        format="%d%%"
    )

    target_supported = not quality_disabled
    target_help = (
        "Automatically pick the highest quality that keeps each image under a size limit. The Quality slider becomes the maximum."
        if target_supported else
        "Available for JPEG, WebP and AVIF without Lossless Compression."
    )
    use_target_size = st.sidebar.checkbox(
        "Target File Size", key='opt_target_size', on_change=_mark_custom,
        disabled=not target_supported, help=target_help,
    )
    target_size_kb = None
    if use_target_size and target_supported:
        target_size_kb = st.sidebar.number_input(
            "Max size per image (KB)", min_value=5, max_value=50_000, value=200, step=10,
            help="Images that can't reach this size even at the lowest quality are saved at the lowest quality and flagged in the results."
        )

    # SVG Settings
    colormode = 'color'
    hierarchical = 'stacked'
    mode = 'spline'
    filter_speckle = 4
    color_precision = 6
    layer_difference = 16
    corner_threshold = 60

    if output_format == "SVG":
        with st.sidebar.expander("SVG Settings", expanded=True, icon=":material/polyline:"):
            colormode = st.selectbox("Color Mode", ["color", "binary"], index=0, format_func=lambda x: "Color" if x == "color" else "Black & White (Binary)", help="Color vs Black & White.")
            hierarchical = st.selectbox("Layering", ["stacked", "cutout"], index=0, format_func=lambda x: "Stacked" if x == "stacked" else "Cutout", help="Stacked = layers on top of each other. Cutout = no overlapping.")
            mode = st.selectbox("Curve Mode", ["spline", "polygon", "none"], index=0, format_func=lambda x: x.capitalize(), help="Curve smoothing method.")
            filter_speckle = st.slider("Filter Speckle", 0, 128, 4, help="Remove small noise (pixels).", format="%dpx")

            is_binary = colormode == "binary"
            color_precision_help = "Not applicable in Black & White mode." if is_binary else "Number of significant bits to use (lower = fewer colors)."
            color_precision = st.slider("Color Precision", 1, 8, 6, disabled=is_binary, help=color_precision_help, format="%d bits")

            layer_diff_help = "Not applicable in Black & White mode." if is_binary else "Threshold for color difference."
            layer_difference = st.slider("Gradient Threshold", 0, 128, 16, disabled=is_binary, help=layer_diff_help, format="%d")

            corner_threshold = st.slider("Corner Threshold", 0, 180, 60, help="Minimum angle to be considered a corner.", format="%d°")

    quality = 100 if quality_disabled else quality_val

    is_svg = output_format == "SVG"
    strip_metadata_help = "Not applicable for SVG output." if is_svg else "Remove EXIF data (camera settings, location, etc.) to reduce file size and protect privacy."
    strip_metadata = st.sidebar.checkbox(
        "Strip Metadata",
        key='opt_strip_metadata',
        on_change=_mark_custom,
        disabled=is_svg,
        help=strip_metadata_help
    )

    optimize_encoding_help = "Not applicable for SVG output." if is_svg else "Perform extra compression passes to reduce file size. Disabling this speeds up processing significantly (up to 3x)."
    optimize_encoding = st.sidebar.checkbox(
        "Optimize Encoding",
        key='opt_optimize',
        on_change=_mark_custom,
        disabled=is_svg,
        help=optimize_encoding_help
    )

    # Resizing Options
    st.sidebar.subheader("Resizing")
    resize_type = st.sidebar.selectbox(
        "Resize Mode",
        ["None", "Fit Within", "Percentage", "Fixed Dimensions"],
        key='opt_resize_type',
        on_change=_mark_custom,
        format_func=lambda x: {"None": "Do Not Resize", "Fit Within": "Fit Within (shrink only)"}.get(x, x),
        help="Fit Within shrinks images larger than the box and leaves smaller ones untouched. Fixed Dimensions scales up or down to the box."
    )

    width = None
    height = None
    percentage = None
    maintain_aspect = True

    if resize_type == "Percentage":
        percentage = st.sidebar.slider(
            "Percentage",
            1,
            200,
            100,
            help="Scale the image by this percentage.",
            format="%d%%"
        )
    elif resize_type in ("Fixed Dimensions", "Fit Within"):
        is_fit = resize_type == "Fit Within"
        col1, col2 = st.sidebar.columns(2)
        width = col1.number_input("Max width (px)" if is_fit else "Width (px)", min_value=1, max_value=ImageProcessor.MAX_IMAGE_DIMENSION,
                                  key='opt_width', on_change=_mark_custom, help="Target width in pixels.")
        height = col2.number_input("Max height (px)" if is_fit else "Height (px)", min_value=1, max_value=ImageProcessor.MAX_IMAGE_DIMENSION,
                                   key='opt_height', on_change=_mark_custom, help="Target height in pixels.")
        if not is_fit:
            maintain_aspect = st.sidebar.checkbox(
                "Maintain Aspect Ratio",
                key='opt_maintain_aspect',
                on_change=_mark_custom,
                help="Preserve the original width-to-height ratio to prevent distortion."
            )

    # Editor Controls
    st.sidebar.markdown("---")
    st.sidebar.subheader("Editor")

    with st.sidebar.expander("Enhancements", icon=":material/tune:"):
        brightness = st.slider("Brightness", 0.0, 2.0, 1.0, 0.1, help="Adjust the brightness of the image.", format="%.1fx")
        contrast = st.slider("Contrast", 0.0, 2.0, 1.0, 0.1, help="Adjust the contrast of the image.", format="%.1fx")
        saturation = st.slider("Saturation", 0.0, 2.0, 1.0, 0.1, help="Adjust the color intensity.", format="%.1fx")
        sharpness = st.slider("Sharpness", 0.0, 3.0, 1.0, 0.1, help="Adjust the sharpness of edges.", format="%.1fx")
        filter_type = st.selectbox(
            "Filter",
            ["None", "Blur", "Contour", "Detail", "Edge Enhance", "Emboss", "Sharpen", "Smooth"],
            index=0,
            format_func=lambda x: "No Filter" if x == "None" else x,
            help="Apply an image filter."
        )

    with st.sidebar.expander("Transforms", icon=":material/transform:"):
        rotate = st.selectbox("Rotate", [0, 90, 180, 270], format_func=lambda x: f"{x}°", help="Rotate the image clockwise.")
        col1, col2 = st.columns(2)
        with col1:
            flip_h = st.checkbox("Flip Horizontal", help="Mirror the image horizontally.")
        with col2:
            flip_v = st.checkbox("Flip Vertical", help="Mirror the image vertically.")
        grayscale = st.checkbox("Convert to Grayscale", help="Convert the image to black and white.")

    with st.sidebar.expander("Crop", icon=":material/crop:"):
        crop_mode = st.selectbox(
            "Crop Mode",
            ["None", "Custom Box", "Aspect Center", "Social Preset"],
            format_func=lambda x: "Do Not Crop" if x == "None" else x,
            help="Choose a cropping strategy. Social Preset outputs an exact size for social posts and link previews."
        )

        crop_left = 0
        crop_top = 0
        crop_right = 0
        crop_bottom = 0
        crop_aspect_w = 1
        crop_aspect_h = 1

        if crop_mode == "Custom Box":
            c1, c2 = st.columns(2)
            with c1:
                crop_left = st.number_input("Left", min_value=0, value=0, help="Pixels to crop from left.")
                crop_top = st.number_input("Top", min_value=0, value=0, help="Pixels to crop from top.")
            with c2:
                crop_right = st.number_input("Right", min_value=0, value=0, help="Pixels to crop from right.")
                crop_bottom = st.number_input("Bottom", min_value=0, value=0, help="Pixels to crop from bottom.")
        elif crop_mode == "Aspect Center":
            a1, a2 = st.columns(2)
            with a1:
                crop_aspect_w = st.number_input("Aspect Width", min_value=1, value=1, help="Width ratio (e.g., 16 for 16:9).")
            with a2:
                crop_aspect_h = st.number_input("Aspect Height", min_value=1, value=1, help="Height ratio (e.g., 9 for 16:9).")
        elif crop_mode == "Social Preset":
            social_label = st.selectbox("Size", list(SOCIAL_SIZES), help="Common social media and link-preview sizes.")
            social_fit = st.radio(
                "Fit", ["crop", "pad"], horizontal=True,
                format_func=lambda x: "Crop to fill" if x == "crop" else "Pad to fit",
                help="Crop trims the edges to fill the frame. Pad keeps the whole image and fills the empty space."
            )
            social_pad_color = st.color_picker("Pad Color", "#FFFFFF", disabled=social_fit != "pad",
                                               help="Background color for Pad to fit.")

    with st.sidebar.expander("Watermark", icon=":material/branding_watermark:"):
        watermark_text = st.text_input("Watermark Text", max_chars=100, help="Text to overlay on the image.", placeholder="e.g. © 2024 MyBrand")

        wm_disabled = not bool(watermark_text)
        wm_help_suffix = " (Enter text above to enable)" if wm_disabled else ""

        wm_opacity_slider = st.slider("Opacity", 0, 100, 50, disabled=wm_disabled, help=f"Transparency of the watermark.{wm_help_suffix}", format="%d%%")
        # Ensure we always pass an integer to backend logic even if disabled
        wm_opacity = int(round(wm_opacity_slider * 255 / 100)) if watermark_text else 128

        wm_size = st.number_input("Font Size", min_value=10, max_value=200, value=30, disabled=wm_disabled, help=f"Size of the watermark text.{wm_help_suffix}")
        wm_color = st.color_picker("Text Color", "#FFFFFF", disabled=wm_disabled, help=f"Color of the watermark text.{wm_help_suffix}")

    with st.sidebar.expander("Analysis", icon=":material/analytics:"):
        extract_colors = st.checkbox("Extract Dominant Colors", help="Find and display the top 5 colors in the image.")
        show_histogram = st.checkbox("Show Histogram", help="Display RGB color distribution charts.")
        compare_formats = st.checkbox(
            "Compare Formats",
            help="Also encode each result as WebP, AVIF, JPEG and PNG and show which is smallest."
        )

    with st.sidebar.expander("Export Extras", icon=":material/inventory_2:"):
        raster_output = output_format in ImageProcessor.RASTER_OUTPUT_FORMATS
        responsive_widths = st.multiselect(
            "Responsive Widths",
            RESPONSIVE_WIDTH_OPTIONS,
            format_func=lambda w: f"{w}px",
            disabled=not raster_output,
            help=("Not applicable for SVG output." if not raster_output else
                  "Also export smaller copies at these widths (never enlarged) plus a ready-to-paste <img srcset> snippet, added to the ZIP.")
        )
        make_icons = st.checkbox(
            "Favicon & App Icons",
            help="Create a full icon set from each image (made before any watermark): favicon.ico (16-256px), PNG favicons, Apple touch icon, Android/PWA icons including maskable versions, a Windows tile, a 1024px App Store icon, plus the manifest, browserconfig and HTML tags."
        )
        make_pdf = st.checkbox(
            "Combine into PDF",
            disabled=not raster_output,
            help=("Put every processed image on its own page of a single PDF." if raster_output else
                  "Available for raster output formats."),
        )

    with st.sidebar.expander("Effects", icon=":material/blur_on:"):
        pixel_size = st.slider("Pixelate (Retro Effect)", 1, 100, 1, help="Increase to make the image look like 8-bit pixel art.", format="%dpx")

    with st.sidebar.expander("Transparency", icon=":material/opacity:"):
        trans_disabled = output_format in ImageProcessor.OPAQUE_FORMATS
        trans_help = f"Transparency is not supported for {output_format} format." if trans_disabled else "Make a specific color transparent."

        replace_color = st.checkbox("Replace Color with Transparency", help=trans_help, disabled=trans_disabled)

        if trans_disabled:
            st.caption(f"⚠️ Not supported for {output_format} format.")

        color_controls_disabled = not replace_color or trans_disabled
        color_help_suffix = " (Enable 'Replace Color with Transparency' above)" if color_controls_disabled else ""

        trans_color = st.color_picker("Color to Replace", "#FFFFFF", disabled=color_controls_disabled, help=f"Choose the color to make transparent.{color_help_suffix}")
        trans_tolerance = st.slider("Tolerance", 0, 100, 10, disabled=color_controls_disabled, help=f"How much variation in color to accept.{color_help_suffix}", format="%d%%")

    config = {
        'brightness': brightness,
        'contrast': contrast,
        'sharpness': sharpness,
        'saturation': saturation,
        'filter_type': filter_type,
        'rotate': rotate,
        'flip_h': flip_h,
        'flip_v': flip_v,
        'grayscale': grayscale,
        'resize_type': resize_type,
        'width': width,
        'height': height,
        'percentage': percentage,
        'maintain_aspect': maintain_aspect,
        'output_format': output_format,
        'quality': quality,
        'strip_metadata': strip_metadata,
        'optimize_encoding': optimize_encoding,
        'lossless': lossless,
        'crop_mode': crop_mode,
        'make_pdf': make_pdf and raster_output,
    }

    # SVG Params
    if output_format == "SVG":
        config.update({
            'colormode': colormode,
            'hierarchical': hierarchical,
            'mode': mode,
            'filter_speckle': filter_speckle,
            'color_precision': color_precision,
            'layer_difference': layer_difference,
            'corner_threshold': corner_threshold
        })

    # Add conditional config
    if crop_mode == "Custom Box":
        config.update({
            'crop_left': crop_left,
            'crop_top': crop_top,
            'crop_right': crop_right,
            'crop_bottom': crop_bottom
        })
    elif crop_mode == "Aspect Center":
        config.update({
            'crop_aspect_w': crop_aspect_w,
            'crop_aspect_h': crop_aspect_h
        })
    elif crop_mode == "Social Preset":
        config.update({
            'social_size': SOCIAL_SIZES[social_label],
            'social_fit': social_fit,
            'social_pad_color': _hex_to_rgb(social_pad_color)
        })

    if target_size_kb:
        config['target_size_kb'] = target_size_kb
    if compare_formats:
        config['compare_formats'] = True
    if responsive_widths and raster_output:
        config['responsive_widths'] = list(responsive_widths)
    if make_icons:
        config['make_icons'] = True

    if replace_color and not trans_disabled:
        config['replace_color'] = True
        config['trans_color_rgb'] = _hex_to_rgb(trans_color)
        # Slider is 0-100%; the processor compares channel values on a 0-255 scale
        config['trans_tolerance'] = int(round(trans_tolerance * 255 / 100))

    if extract_colors:
        config['extract_colors'] = True

    if show_histogram:
        config['show_histogram'] = True

    if pixel_size > 1:
        config['pixel_size'] = pixel_size

    if watermark_text:
        config['watermark_text'] = watermark_text
        config['wm_opacity'] = wm_opacity
        config['wm_size'] = wm_size
        config['wm_color'] = _hex_to_rgb(wm_color)
    return config


def render_results(batch: BatchResult, *, stale: bool):
    st.subheader("Last processed batch" if stale else "Batch results")
    if stale:
        st.info("Uploads or settings changed. Process the current uploads to update these results.")
    st.caption(f"{len(batch.images)} succeeded, {len(batch.errors)} failed")
    for name, error in batch.errors:
        st.error(f"{escape_markdown(sanitize_filename(name))}: {escape_markdown(error)}")
    for warning in batch.warnings:
        st.warning(escape_markdown(warning))
    if not batch.images:
        return

    # Recalculate totals for display
    total_original_size = sum(item['original_size'] for item in batch.images)
    total_processed_size = sum(item['processed_size'] for item in batch.images)

    # Summary Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Original Size", format_bytes(total_original_size))

    diff = total_processed_size - total_original_size
    col2.metric("Total Processed Size", format_bytes(total_processed_size), delta=format_bytes(diff), delta_color="inverse")

    savings = (1 - total_processed_size / total_original_size) * 100 if total_original_size > 0 else 0
    col3.metric("Space Savings", f"{savings:.1f}%")

    if batch.zip_data:
        st.download_button(
            label="Download All as ZIP",
            data=batch.zip_data,
            file_name="processed_images.zip",
            mime="application/zip",
            on_click="ignore",
            type="primary",
            icon=":material/archive:",
            help="Download all processed images (plus any responsive sizes, icons and PDF) in a single ZIP file."
        )
    if batch.pdf_data:
        st.download_button(
            label="Download PDF",
            data=batch.pdf_data,
            file_name="processed_images.pdf",
            mime="application/pdf",
            on_click="ignore",
            icon=":material/picture_as_pdf:",
            help="All processed images combined into one PDF, one image per page."
        )

    # Individual Previews
    st.subheader("Detailed Results")
    # item_idx keeps widget keys unique when two uploads share a filename stem
    for item_idx, item in enumerate(batch.images):
        # Security: Sanitize filename for display and download
        safe_name = sanitize_filename(item['name'])

        orig_size = item['original_size']
        proc_size = item['processed_size']
        savings = (1 - proc_size / orig_size) * 100 if orig_size > 0 else 0
        rounded_savings = round(savings, 1)

        # Expander and button labels render Markdown, so escape the user-supplied name there
        md_name = escape_markdown(safe_name)
        label_text = f"{md_name} ({format_bytes(orig_size)} → {format_bytes(proc_size)})"
        if rounded_savings != 0:
            icon = "⬇" if rounded_savings > 0 else "⬆"
            label_text += f" {icon} {abs(rounded_savings):.1f}%"

        with st.expander(label_text, icon=":material/image:"):
            if item.get("has_transparency"):
                st.caption("ℹ️ Original image has transparency")

            if item.get("animated"):
                st.caption(f"🎞️ Animation kept: {item['frame_count']} frames")
            elif item.get("frame_count", 1) > 1:
                st.caption(f"🎞️ Original is animated ({item['frame_count']} frames); only the first frame was kept. "
                           "Choose WebP, AVIF or PNG to keep the animation.")

            target = item.get("target_size")
            if target:
                if target['met']:
                    st.caption(f"🎯 Under {format_bytes(target['target_bytes'])} at {target['quality']}% quality")
                else:
                    st.warning(f"Couldn't get under {format_bytes(target['target_bytes'])} even at {target['quality']}% quality. "
                               "Try a smaller size with Resize, or a different format.", icon=":material/warning:")

            metadata = item.get("metadata") or {}
            if metadata.get("fields"):
                if metadata.get("has_gps"):
                    if item.get("strip_metadata", True) and item.get("output_format") != "SVG":
                        st.info("This photo had GPS location data. It was removed from the processed image.", icon=":material/location_off:")
                    else:
                        st.warning("This photo contains GPS location data, and it is still in the processed image because Strip Metadata is off.",
                                   icon=":material/location_on:")
                st.markdown("**Metadata in original:**")
                st.dataframe(
                    pd.DataFrame(list(metadata["fields"].items()), columns=["Field", "Value"]),
                    hide_index=True, width="stretch"
                )

            if item.get("dominant_colors"):
                st.markdown("**Dominant Colors:**")
                cols = st.columns(len(item["dominant_colors"]))
                for idx, color in enumerate(item["dominant_colors"]):
                    with cols[idx]:
                        st.color_picker(f"Color {idx+1}", color, disabled=True, key=f"c_{item_idx}_{idx}", label_visibility="collapsed")
                        st.caption(color)

            if item.get("histogram_data"):
                st.markdown("**RGB Histogram:**")
                st.line_chart(item["histogram_data"], color=["#FF0000", "#00FF00", "#0000FF"])

            format_sizes = item.get("format_sizes")
            if format_sizes:
                st.markdown("**Format Comparison:**")
                smallest = min(format_sizes, key=format_sizes.get)
                comparison = pd.DataFrame({
                    "Format": list(format_sizes),
                    "Size": [format_bytes(size) for size in format_sizes.values()],
                    "vs Original": [f"{(size / orig_size - 1) * 100:+.1f}%" if orig_size else "" for size in format_sizes.values()],
                    "KB": [round(size / 1024, 1) for size in format_sizes.values()],
                })
                st.bar_chart(comparison, x="Format", y="KB", horizontal=True, height=180)
                st.dataframe(comparison.drop(columns="KB"), hide_index=True, width="stretch")
                st.caption(f"Smallest: **{smallest}** at the same quality setting.")

            col1, col2 = st.columns(2)
            with col1:
                st.image(item['original_data'], caption=f"Original ({format_bytes(item['original_size'])})")
            item_format = item['output_format'].lower()
            mime_subtype = MIME_SUBTYPES.get(item_format, item_format)
            with col2:
                caption = f"Processed ({format_bytes(item['processed_size'])})"
                if item.get("animated") or item_format == "svg":
                    b64 = base64.b64encode(item['data']).decode("utf-8")
                    st.markdown(
                        f'<img src="data:image/{mime_subtype};base64,{b64}" width="100%" '
                        f'alt="Processed {html.escape(safe_name)}"/>',
                        unsafe_allow_html=True,
                    )
                    st.caption(caption)
                else:
                    st.image(item['data'], caption=caption)

            if item.get("responsive"):
                st.markdown("**Responsive Sizes** (in the ZIP under `responsive/`):")
                st.caption(" • ".join(f"{v['width']}px: {format_bytes(len(v['data']))}" for v in item['responsive']))
                width_px, height_px = item['processed_dimensions']
                st.code(build_srcset_html([{
                    'full_name': item['file_name'],
                    'full_width': width_px, 'full_height': height_px,
                    'name_stem': item['unique_stem'], 'ext': item['output_format'].lower(),
                    'alt': safe_name, 'variants': item['responsive'],
                }]), language="html")

            download_cols = st.columns(2 if item.get("icon_zip") else 1)
            download_cols[0].download_button(
                label=f"Download {md_name}",
                data=item['data'],
                file_name=item['file_name'],
                mime=f"image/{mime_subtype}",
                on_click="ignore",
                key=f"dl_{item_idx}",
                icon=":material/download:",
                help=f"Download {safe_name}"
            )
            if item.get("icon_zip"):
                download_cols[1].download_button(
                    label="Download Icon Pack",
                    data=item['icon_zip'],
                    file_name=f"icons_{item['unique_stem']}.zip",
                    mime="application/zip",
                    on_click="ignore",
                    key=f"icons_{item_idx}",
                    icon=":material/apps:",
                    help="favicon.ico (16-256px), PNG favicons, Apple touch icon, Android/PWA and maskable icons, Windows tile, 1024px App Store icon, site.webmanifest, browserconfig.xml and an HTML snippet."
                )


def render_welcome():
    st.markdown("### 👋 Welcome to Image Processor!")
    st.markdown("Start by uploading your images above. This tool helps you:")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **🚀 Convert & Compress**
        Save space with WebP and AVIF formats.

        **🔒 Protect Privacy**
        Automatically strip metadata (EXIF).
        """)

    with col2:
        st.markdown("""
        **✨ Batch Edit**
        Resize, filter, and watermark up to 50 images.

        **📐 Vectorize**
        Convert raster images to SVG.
        """)

    st.info("👆 Drag and drop files to the uploader to get started.")


def main():
    st.set_page_config(page_title="Image Processor", layout="wide")
    st.title("Image Processing & Optimization")
    uploaded_files = st.file_uploader(
        "Upload Images",
        type=['png', 'jpg', 'jpeg', 'bmp', 'webp', 'heic', 'heif', 'avif', 'gif'],
        accept_multiple_files=True,
        help="Supported: PNG, JPG, WEBP, HEIC, AVIF, BMP, GIF (including animated). Limit: 50 files, 200MB total.",
    )
    st.caption("Supported formats: PNG, JPG, WEBP, HEIC, AVIF, BMP, GIF • Limit: 50 files, 200MB")
    settings = render_settings()
    request = (tuple(upload.file_id for upload in uploaded_files), settings)

    if uploaded_files:
        valid, error = validate_upload_constraints(uploaded_files)
        if not valid:
            st.error(f"Upload limit exceeded: {error}")
        elif st.button(
            f"Process {len(uploaded_files)} Image{'s' if len(uploaded_files) != 1 else ''}",
            type="primary", icon=":material/auto_fix_high:",
        ):
            progress = st.progress(0, text=f"Processing 0 of {len(uploaded_files)} images...")

            def update_progress(completed, total):
                text = "Preparing downloads..." if completed == total else f"Processed {completed} of {total} images..."
                progress.progress(completed / total, text=text)

            with st.spinner("Processing images..."):
                uploads = [(upload.name, upload.getvalue()) for upload in uploaded_files]
                result = run_batch(uploads, settings, update_progress)
            st.session_state.batch = (request, result)
            progress.empty()

    stored = st.session_state.get("batch")
    if stored and st.button("Clear Results", icon=":material/delete:", help="Clear the last batch and its downloads."):
        del st.session_state.batch
        stored = None
        st.toast("Results cleared", icon=":material/delete:")

    if stored:
        processed_request, result = stored
        render_results(result, stale=processed_request != request)
    elif not uploaded_files:
        render_welcome()


if __name__ == "__main__":
    main()
