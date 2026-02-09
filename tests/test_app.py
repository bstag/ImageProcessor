import pytest
from unittest.mock import MagicMock, patch, ANY
import sys
import os

# Need to set up sys.modules for streamlit before importing app
mock_st = MagicMock()
sys.modules["streamlit"] = mock_st

class MockSessionState(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)
    def __setattr__(self, key, value):
        self[key] = value

# Mock streamlit attributes that are accessed directly
mock_st.sidebar = MagicMock()
mock_st.session_state = MockSessionState()
mock_st.columns.side_effect = lambda n: [MagicMock() for _ in range(n)]
mock_st.sidebar.columns.side_effect = lambda n: [MagicMock() for _ in range(n)]
mock_st.sidebar.expander.return_value.__enter__.return_value = MagicMock()
mock_st.expander.return_value.__enter__.return_value = MagicMock()
mock_st.spinner.return_value.__enter__.return_value = MagicMock()

# Now we can import app
from src.app import main

@pytest.fixture(autouse=True)
def reset_st():
    # Reset mocks before each test
    mock_st.reset_mock()
    mock_st.sidebar.reset_mock()
    mock_st.button.side_effect = None  # Clear any side effects
    mock_st.session_state = MockSessionState()
    
    # Setup default return values
    mock_st.file_uploader.return_value = []
    mock_st.sidebar.selectbox.return_value = "JPEG"
    mock_st.sidebar.slider.return_value = 80
    mock_st.sidebar.checkbox.return_value = False
    mock_st.checkbox.return_value = False
    mock_st.sidebar.radio.return_value = "Rescaling"
    mock_st.sidebar.number_input.return_value = 100
    mock_st.sidebar.text_input.return_value = ""
    mock_st.sidebar.color_picker.return_value = "#FFFFFF"
    mock_st.color_picker.return_value = "#FFFFFF"
    mock_st.slider.return_value = 1
    mock_st.button.return_value = False
  
def test_app_initial_render():
    """Test that the app renders the initial state correctly."""
    main()
    
    mock_st.set_page_config.assert_called_once()
    mock_st.title.assert_called_once()
    mock_st.file_uploader.assert_called_once()
    
    # Verify sidebar elements
    mock_st.sidebar.header.assert_called_with("Settings")
    mock_st.sidebar.subheader.assert_any_call("Output Format")
    
    # Verify welcome message when no files uploaded
    mock_st.markdown.assert_any_call("### 👋 Welcome to Image Processor!")

@patch("src.app.validate_upload_constraints")
@patch("src.app.ThreadPoolExecutor")
def test_app_process_flow(mock_executor, mock_validate):
    """Test the image processing flow."""
    # Setup inputs
    mock_file = MagicMock()
    mock_file.name = "test.jpg"
    mock_file.size = 1024
    mock_file.getvalue.return_value = b"fake_image_data"
    
    mock_st.file_uploader.return_value = [mock_file]
    mock_validate.return_value = (True, "")
    
    # Mock the process button
    def button_side_effect(label, **kwargs):
        if "Process" in label:
            return True
        return False
    mock_st.button.side_effect = button_side_effect

    # Mock executor
    mock_future = MagicMock()
    mock_future.result.return_value = {
        "success": True,
        "processed_size": 500,
        "data": b"processed_data",
        "has_transparency": False,
        "dominant_colors": ["#FFFFFF"],
        "histogram_data": {"Red": [0]*256},
        "error": None
    }
    
    # Mock context manager for executor
    mock_executor_instance = mock_executor.return_value.__enter__.return_value
    mock_executor_instance.submit.return_value = mock_future
    
    # We need to mock as_completed to yield our future
    with patch("src.app.as_completed", return_value=[mock_future]):
        main()
    
    # Validation should be called
    mock_validate.assert_called_once()
    
    # Success message (toast)
    mock_st.toast.assert_called_with("Processing Complete!", icon='🎉')
    
    # Results should be stored in session state
    assert mock_st.session_state["processed_images"] is not None
    assert len(mock_st.session_state["processed_images"]) == 1
    assert mock_st.session_state["processed_images"][0]["name"] == "test.jpg"

@patch("src.app.validate_upload_constraints")
def test_app_validation_failure(mock_validate):
    """Test that validation failure prevents processing."""
    mock_file = MagicMock()
    mock_st.file_uploader.return_value = [mock_file]
    
    mock_validate.return_value = (False, "Too many files")
    
    main()
    
    mock_st.error.assert_called_with("Upload limit exceeded: Too many files")
    # Button should not be clicked (or if it is, processing shouldn't start, but here the button isn't even shown if valid is false? 
    # Logic in app.py: if not is_valid: st.error ... elif st.button ...
    # So st.button is NOT called if invalid.
    mock_st.button.assert_not_called()

def test_app_sidebar_logic():
    """Test dynamic sidebar logic."""
    # Test WEBP + Lossless
    mock_st.sidebar.selectbox.return_value = "WEBP"
    mock_st.sidebar.checkbox.side_effect = lambda label, **kwargs: True if "Lossless" in label else False
    
    main()
    
    # Check if quality slider is disabled (it is when lossless is True)
    # We can inspect the calls to slider
    # quality_val = st.sidebar.slider("Quality", ..., disabled=True, ...)
    slider_calls = mock_st.sidebar.slider.call_args_list
    quality_call = next((call for call in slider_calls if call[0][0] == "Quality"), None)
    assert quality_call is not None
    assert quality_call.kwargs.get("disabled") is True

def test_svg_settings():
    """Test SVG specific settings appear."""
    mock_st.sidebar.selectbox.return_value = "SVG"
    
    main()
    
    mock_st.sidebar.expander.assert_any_call("SVG Settings", expanded=True)

def test_results_display():
    """Test the results display logic."""
    # Ensure we enter the main block
    mock_file = MagicMock()
    mock_file.size = 1000
    mock_st.file_uploader.return_value = [mock_file]
    
    # Populate session state directly
    mock_st.session_state["processed_images"] = [{
        "name": "test.jpg",
        "original_size": 1000,
        "processed_size": 500,
        "data": b"processed",
        "original_data": b"orig",
        "has_transparency": False,
        "dominant_colors": ["#FFFFFF"]
    }]
    mock_st.session_state["zip_data"] = b"zipdata"
    
    # Ensure st.columns returns iterable to avoid unpacking error
    mock_st.columns.side_effect = lambda n: [MagicMock() for _ in range(n)]

    main()
    
    # Should show metrics
    mock_st.columns.assert_any_call(3)

    # Should show detailed results
    mock_st.subheader.assert_any_call("Detailed Results")
    
    # Should show download button
    mock_st.download_button.assert_called()

