import pytest
from PIL import Image, ImageChops
from src.processor import ImageProcessor
from unittest.mock import patch, MagicMock

@pytest.fixture
def base_image():
    # Create a simple 100x100 RGB image
    img = Image.new('RGB', (100, 100), color='red')
    return img

def test_pixelate(base_image):
    # Pixel size 1 should return original
    assert ImageProcessor.pixelate(base_image, 1) == base_image
    
    # Pixel size 10 should modify image
    pixelated = ImageProcessor.pixelate(base_image, 10)
    assert pixelated.size == (100, 100)
    # The content might be same because it's a solid color, so let's use a gradient or pattern for better test
    # But for coverage, checking execution is enough.
    
    # Let's try with a gradient for logic check
    gradient = Image.linear_gradient('L')
    pixelated_grad = ImageProcessor.pixelate(gradient, 10)
    assert pixelated_grad.size == (256, 256)
    assert pixelated_grad != gradient

def test_apply_filter(base_image):
    # Test a few filters to ensure branches are hit
    blurred = ImageProcessor.apply_filter(base_image, "BLUR")
    assert blurred is not None
    
    contour = ImageProcessor.apply_filter(base_image, "CONTOUR")
    assert contour is not None
    
    # Default case
    none_filter = ImageProcessor.apply_filter(base_image, "UNKNOWN")
    assert none_filter == base_image

def test_apply_enhancements(base_image):
    # Change brightness
    bright = ImageProcessor.apply_enhancements(base_image, brightness=1.5)
    assert bright is not None
    
    # Change all
    enhanced = ImageProcessor.apply_enhancements(base_image, brightness=1.2, contrast=1.2, sharpness=1.2, saturation=1.2)
    assert enhanced is not None

def test_add_watermark(base_image):
    # Empty text
    assert ImageProcessor.add_watermark(base_image, "") == base_image
    
    # With text
    watermarked = ImageProcessor.add_watermark(base_image, "Test", opacity=100)
    assert watermarked is not None
    assert watermarked.size == base_image.size

def test_get_histogram_data(base_image):
    hist = ImageProcessor.get_histogram_data(base_image)
    assert "Red" in hist
    assert "Green" in hist
    assert "Blue" in hist
    assert len(hist["Red"]) == 256
    # Since image is red, Red channel should have high count at 254/255
    assert sum(hist["Red"]) == 100 * 100

def test_replace_color_with_transparency():
    # Create an image with a specific color to replace
    img = Image.new('RGB', (10, 10), color=(255, 0, 0)) # Red
    
    # Replace Red with transparency
    result = ImageProcessor.replace_color_with_transparency(img, (255, 0, 0), tolerance=10)
    
    # Check if alpha channel exists and is 0 (transparent)
    assert result.mode == 'RGBA'
    r, g, b, a = result.split()
    assert a.getextrema() == (0, 0) # All pixels should be fully transparent

    # Test tolerance - Replace "almost red"
    img2 = Image.new('RGB', (10, 10), color=(250, 0, 0))
    result2 = ImageProcessor.replace_color_with_transparency(img2, (255, 0, 0), tolerance=10)
    _, _, _, a2 = result2.split()
    assert a2.getextrema() == (0, 0)

def test_convert_to_svg(base_image):
    with patch('vtracer.convert_image_to_svg_py') as mock_vtracer, \
         patch('builtins.open', new_callable=MagicMock) as mock_open:
        
        # Mock file read
        mock_open.return_value.__enter__.return_value.read.return_value = "<svg>...</svg>"
        
        svg = ImageProcessor.convert_to_svg(base_image)
        
        assert svg == "<svg>...</svg>"
        assert mock_vtracer.called

def test_center_crop_to_aspect(base_image):
    # Image is 100x100 (1:1)
    
    # Crop to 2:1 (wider) -> Should become 100x50
    # Wait, target_w=2, target_h=1. target_ratio = 2.
    # current_ratio = 1.
    # current < target: else block.
    # new_h = w / target_ratio = 100 / 2 = 50.
    # Result size: 100x50.
    cropped_wide = ImageProcessor.center_crop_to_aspect(base_image, 2, 1)
    assert cropped_wide.size == (100, 50)
    
    # Crop to 1:2 (taller) -> Should become 50x100
    # target_ratio = 0.5. current > target.
    # new_w = h * target_ratio = 100 * 0.5 = 50.
    # Result size: 50x100.
    cropped_tall = ImageProcessor.center_crop_to_aspect(base_image, 1, 2)
    assert cropped_tall.size == (50, 100)
    
    # Invalid
    assert ImageProcessor.center_crop_to_aspect(base_image, 0, 100) == base_image
