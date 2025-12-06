"""Tests for capture daemon."""

import pytest
import time
from unittest.mock import Mock, MagicMock

from modules.capture.daemon import CaptureDaemon
from core.bus.event_bus import EventBus
from core.interfaces.events import EventType
from core.models.session import Session
from core.models.slide import RawCapture
from PIL import Image


class TestCaptureDaemon:
    """Test cases for CaptureDaemon."""

    @pytest.fixture
    def mock_provider(self):
        """Create a mock capture provider."""
        provider = Mock()
        provider.name = "mock"
        provider.supported_platforms = ["linux"]

        # Create a mock image
        mock_image = Image.new("RGB", (800, 600), color="red")

        # Create a mock capture
        mock_capture = RawCapture(
            image=mock_image,
            timestamp=time.time(),
            monitor_id=1,
            width=800,
            height=600,
            metadata={"provider": "mock"}
        )
        provider.capture.return_value = mock_capture

        return provider

    @pytest.fixture
    def session(self):
        """Create a test session."""
        return Session(
            name="Test Session",
            capture_interval_seconds=0.5  # Short interval for testing
        )

    @pytest.fixture
    def event_bus(self):
        """Create a fresh event bus for testing."""
        bus = EventBus()
        bus.clear_history()
        return bus

    def test_initialization(self, mock_provider, session):
        """Test daemon initialization."""
        daemon = CaptureDaemon(mock_provider, session)
        assert daemon is not None
        assert daemon.is_running() is False
        assert daemon.is_paused() is False

    def test_start_daemon(self, mock_provider, session):
        """Test starting the daemon."""
        daemon = CaptureDaemon(mock_provider, session)
        result = daemon.start()

        assert result is True
        assert daemon.is_running() is True

        # Clean up
        daemon.stop()

    def test_stop_daemon(self, mock_provider, session):
        """Test stopping the daemon."""
        daemon = CaptureDaemon(mock_provider, session)
        daemon.start()

        result = daemon.stop()
        assert result is True
        assert daemon.is_running() is False

    def test_pause_resume(self, mock_provider, session):
        """Test pausing and resuming capture."""
        daemon = CaptureDaemon(mock_provider, session)
        daemon.start()

        # Pause
        daemon.pause()
        assert daemon.is_paused() is True

        # Resume
        daemon.resume()
        assert daemon.is_paused() is False

        # Clean up
        daemon.stop()

    def test_capture_events_published(self, mock_provider, session, event_bus):
        """Test that capture events are published."""
        received_events = []

        def handler(event):
            received_events.append(event)

        event_bus.subscribe(EventType.SLIDE_CAPTURED, handler)
        event_bus.subscribe(EventType.SESSION_STARTED, handler)

        daemon = CaptureDaemon(mock_provider, session, event_bus)
        daemon.start()

        # Wait for a few captures
        time.sleep(1.5)

        daemon.stop()

        # Check that events were published
        assert len(received_events) > 0

        # Check for SESSION_STARTED event
        started_events = [e for e in received_events if e.type == EventType.SESSION_STARTED]
        assert len(started_events) > 0

        # Check for SLIDE_CAPTURED events
        captured_events = [e for e in received_events if e.type == EventType.SLIDE_CAPTURED]
        assert len(captured_events) > 0

    def test_capture_statistics(self, mock_provider, session):
        """Test that capture statistics are tracked."""
        daemon = CaptureDaemon(mock_provider, session)
        daemon.start()

        # Wait for captures
        time.sleep(1.5)

        stats = daemon.get_stats()
        assert stats["capture_count"] > 0
        assert stats["running"] is True
        assert stats["last_capture_time"] > 0

        daemon.stop()

    def test_pause_stops_capturing(self, mock_provider, session):
        """Test that pausing stops capturing."""
        daemon = CaptureDaemon(mock_provider, session)
        daemon.start()

        # Wait for some captures
        time.sleep(1.0)
        stats1 = daemon.get_stats()
        count1 = stats1["capture_count"]

        # Pause
        daemon.pause()
        time.sleep(1.0)

        # Count should not increase while paused
        stats2 = daemon.get_stats()
        count2 = stats2["capture_count"]

        daemon.stop()

        # Count should be same or very close (accounting for timing)
        assert count2 - count1 <= 1

    def test_capture_interval_respected(self, mock_provider, session):
        """Test that capture interval is respected."""
        session.capture_interval_seconds = 1.0
        daemon = CaptureDaemon(mock_provider, session)
        daemon.start()

        # Wait and check captures
        time.sleep(2.5)
        stats = daemon.get_stats()

        daemon.stop()

        # Should have approximately 2-3 captures (2.5 seconds / 1.0 interval)
        assert 1 <= stats["capture_count"] <= 4

    def test_double_start(self, mock_provider, session):
        """Test that starting already running daemon returns False."""
        daemon = CaptureDaemon(mock_provider, session)
        daemon.start()

        result = daemon.start()
        assert result is False

        daemon.stop()

    def test_stop_not_running(self, mock_provider, session):
        """Test that stopping non-running daemon returns False."""
        daemon = CaptureDaemon(mock_provider, session)
        result = daemon.stop()
        assert result is False
