import pytest
from PIL import Image
from src.processor import ImageProcessor

def test_get_histogram_data_large_image():
    # Create an image larger than 1MP (1000x1000)
    # Using 1200x1200 = 1,440,000 pixels
    img = Image.new('RGB', (1200, 1200), color='red')

    # Get histogram
    hist = ImageProcessor.get_histogram_data(img)

    # Should still have standard channels
    assert "Red" in hist
    assert "Green" in hist
    assert "Blue" in hist

    # The image is scaled down to max width/height ~1000, which means 1000x1000 = 1,000,000 pixels
    # Since we use min(1000/1200, 1000/1200) = 0.8333, new dims are 1000x1000
    # Expected pixel count for the downsampled image is ~1,000,000
    assert sum(hist["Red"]) == 1000 * 1000
