"""Tests for MSS capture provider."""

import pytest
import os
from PIL import Image
from modules.capture.providers.mss_provider import MSSCaptureProvider
from core.interfaces.capture import CaptureError


# Check if display is available and screen capture actually works
def can_capture_screen():
    """Test if screen capture actually works."""
    try:
        import mss
        with mss.mss() as sct:
            sct.grab(sct.monitors[1])
        return True
    except Exception:
        return False

has_display = can_capture_screen()
skip_if_no_display = pytest.mark.skipif(
    not has_display,
    reason="No display available or screen capture not working"
)


class TestMSSProvider:
    """Test cases for MSSCaptureProvider."""

    @pytest.fixture
    def provider(self):
        """Create a provider instance for testing."""
        provider = MSSCaptureProvider()
        yield provider
        provider.cleanup()

    def test_initialization(self, provider):
        """Test that provider initializes correctly."""
        config = {
            "monitor_id": 1,
            "quality": 90,
            "format": "png"
        }
        result = provider.initialize(config)
        assert result is True
        assert provider.name == "mss"

    def test_name_property(self, provider):
        """Test that name property returns correct value."""
        assert provider.name == "mss"

    def test_supported_platforms(self, provider):
        """Test that supported platforms are listed."""
        platforms = provider.supported_platforms
        assert "linux" in platforms
        assert "darwin" in platforms
        assert "win32" in platforms

    def test_list_monitors(self, provider):
        """Test that monitors are listed correctly."""
        provider.initialize({})
        monitors = provider.list_monitors()

        assert len(monitors) > 0
        assert "id" in monitors[0]
        assert "x" in monitors[0]
        assert "y" in monitors[0]
        assert "width" in monitors[0]
        assert "height" in monitors[0]
        assert monitors[0]["width"] > 0
        assert monitors[0]["height"] > 0

    def test_list_monitors_without_init(self, provider):
        """Test that listing monitors without init raises error."""
        with pytest.raises(CaptureError):
            provider.list_monitors()

    @skip_if_no_display
    def test_capture(self, provider):
        """Test that capture returns valid data."""
        provider.initialize({"monitor_id": 1})
        capture = provider.capture()

        assert capture is not None
        assert capture.image is not None
        assert isinstance(capture.image, Image.Image)
        assert capture.width > 0
        assert capture.height > 0
        assert capture.monitor_id == 1
        assert capture.timestamp > 0
        assert capture.capture_id is not None
        assert "provider" in capture.metadata
        assert capture.metadata["provider"] == "mss"

    @skip_if_no_display
    def test_capture_specific_monitor(self, provider):
        """Test capturing a specific monitor."""
        provider.initialize({"monitor_id": 1})
        capture = provider.capture(monitor_id=1)

        assert capture is not None
        assert capture.monitor_id == 1

    def test_capture_without_init(self, provider):
        """Test that capture without init raises error."""
        with pytest.raises(CaptureError):
            provider.capture()

    def test_capture_invalid_monitor(self, provider):
        """Test that invalid monitor ID raises error."""
        provider.initialize({})
        with pytest.raises(CaptureError):
            provider.capture(monitor_id=999)

    def test_cleanup(self, provider):
        """Test that cleanup works correctly."""
        provider.initialize({})
        provider.cleanup()

        # After cleanup, capturing should fail
        with pytest.raises(CaptureError):
            provider.capture()

    @skip_if_no_display
    def test_multiple_captures(self, provider):
        """Test that multiple captures work correctly."""
        provider.initialize({"monitor_id": 1})

        capture1 = provider.capture()
        capture2 = provider.capture()

        assert capture1.capture_id != capture2.capture_id
        assert capture2.timestamp >= capture1.timestamp

    @skip_if_no_display
    def test_image_format(self, provider):
        """Test that captured image is in RGB format."""
        provider.initialize({})
        capture = provider.capture()

        assert capture.image.mode == "RGB"
        assert capture.image.size == (capture.width, capture.height)
