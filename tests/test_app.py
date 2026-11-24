import io
from pathlib import Path

import pytest
from PIL import Image
from streamlit.testing.v1 import AppTest

import batch


APP = Path(__file__).resolve().parents[1] / "src" / "app.py"


@pytest.fixture
def app():
    return AppTest.from_file(str(APP), default_timeout=15).run()


def png(name, color="red"):
    buffer = io.BytesIO()
    Image.new("RGB", (32, 32), color).save(buffer, "PNG")
    return name, buffer.getvalue(), "image/png"


def upload(app, *files):
    app.file_uploader[0].set_value(files).run()


def click(app, label):
    next(button for button in app.button if button.label.startswith(label)).click().run()


def download_labels(app):
    return [button.proto.label.replace("\\.", ".") for button in app.get("download_button")]


def test_app_initial_render(app):
    assert not app.exception
    assert app.title[0].value == "Image Processing & Optimization"
    assert app.file_uploader[0].accept_multiple_files
    assert not download_labels(app)


def test_preset_resets_conflicting_settings(app):
    app.checkbox(key="opt_lossless").check().run()
    assert app.slider(key="opt_quality").proto.disabled

    app.selectbox(key="opt_preset").select("Web").run()
    assert not app.checkbox(key="opt_lossless").value
    assert not app.slider(key="opt_quality").proto.disabled
    assert app.slider(key="opt_quality").value == 80

    app.checkbox(key="opt_target_size").check().run()
    assert app.selectbox(key="opt_preset").value == "Custom"
    app.selectbox(key="opt_preset").select("Email").run()
    assert not app.checkbox(key="opt_target_size").value
    assert app.selectbox(key="opt_format").value == "JPEG"


@pytest.mark.parametrize(("format_name", "lossless", "pdf"), [
    ("AVIF", False, True),
    ("SVG", False, False),
    ("WEBP", True, True),
])
def test_format_capabilities(app, format_name, lossless, pdf):
    app.selectbox(key="opt_format").select(format_name).run()
    pdf_box = next(box for box in app.checkbox if box.label == "Combine into PDF")
    assert app.checkbox(key="opt_lossless").proto.disabled == (not lossless)
    assert pdf_box.proto.disabled == (not pdf)


def test_results_identify_previous_batch_and_can_be_cleared(app):
    upload(app, png("first.png"))
    click(app, "Process ")
    assert not app.exception
    assert "Download first.png" in download_labels(app)

    app.slider(key="opt_quality").set_value(65).run()
    assert any(title.value == "Last processed batch" for title in app.subheader)

    upload(app, png("second.png", "blue"))
    assert "Download first.png" in download_labels(app)
    assert any("Uploads or settings changed" in info.value for info in app.info)

    click(app, "Clear Results")
    assert not download_labels(app)


@pytest.mark.parametrize("include_valid", [True, False])
def test_processing_reports_successes_and_failures(app, include_valid):
    files = [("invalid.png", b"not an image", "image/png")]
    if include_valid:
        files.append(png("valid.png"))
    upload(app, *files)
    click(app, "Process ")

    assert not app.exception
    assert any("Invalid or corrupt image file" in error.value for error in app.error)
    assert f"{int(include_valid)} succeeded, 1 failed" in [caption.value for caption in app.caption]
    assert ("Download valid.png" in download_labels(app)) == include_valid


def test_app_validation_failure(app):
    upload(app, *(png(f"{index}.png") for index in range(51)))
    assert any("Maximum allowed is 50" in error.value for error in app.error)
    assert not any(button.label.startswith("Process ") for button in app.button)


@pytest.mark.parametrize("failed_export", ["zip", "pdf"])
def test_export_failure_preserves_current_batch_downloads(app, monkeypatch, failed_export):
    next(box for box in app.checkbox if box.label == "Combine into PDF").check().run()
    upload(app, png("first.png"))
    click(app, "Process ")
    assert set(download_labels(app)) == {"Download first.png", "Download PDF", "Download All as ZIP"}

    def fail(*args, **kwargs):
        raise OSError("simulated export failure")

    monkeypatch.setattr(batch, "build_results_zip" if failed_export == "zip" else "build_pdf", fail)
    upload(app, png("second.png", "blue"))
    click(app, "Process ")

    assert not app.exception
    assert any("Individual images are still available" in warning.value for warning in app.warning)
    available_export = "Download PDF" if failed_export == "zip" else "Download All as ZIP"
    assert set(download_labels(app)) == {"Download second.png", available_export}
