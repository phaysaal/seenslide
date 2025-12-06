"""Tests for storage manager."""

import pytest
import tempfile
import shutil
from pathlib import Path
from PIL import Image
import time

from modules.storage.manager import StorageManager
from core.bus.event_bus import EventBus
from core.interfaces.events import Event, EventType
from core.models.slide import RawCapture, ProcessedSlide
from core.models.session import Session


class TestStorageManager:
    """Test cases for StorageManager."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)

    @pytest.fixture
    def event_bus(self):
        """Create an event bus for testing."""
        return EventBus()

    @pytest.fixture
    def sample_session(self):
        """Create a sample session for testing."""
        return Session(
            name="Test Session",
            description="Test description"
        )

    @pytest.fixture
    def storage_config(self, temp_dir):
        """Create storage configuration."""
        return {
            "base_path": temp_dir,
            "images_subdir": "images",
            "thumbnails_subdir": "thumbnails",
            "database_subdir": "db",
            "create_thumbnails": True,
            "thumbnail_width": 320
        }

    @pytest.fixture
    def manager(self, sample_session, storage_config, event_bus):
        """Create a storage manager for testing."""
        return StorageManager(sample_session, storage_config, event_bus)

    @pytest.fixture
    def sample_capture(self):
        """Create a sample capture for testing."""
        image = Image.new("RGB", (100, 100), color="blue")
        return RawCapture(
            image=image,
            timestamp=time.time(),
            monitor_id=1,
            width=100,
            height=100
        )

    def test_initialization(self, manager, sample_session):
        """Test that manager initializes correctly."""
        assert manager._session == sample_session
        assert manager._running is False
        assert manager._slides_stored == 0

    def test_start(self, manager):
        """Test starting the manager."""
        result = manager.start()
        assert result is True
        assert manager.is_running() is True

        # Cleanup
        manager.stop()

    def test_start_already_running(self, manager):
        """Test starting when already running."""
        manager.start()
        result = manager.start()
        assert result is False

        # Cleanup
        manager.stop()

    def test_stop(self, manager):
        """Test stopping the manager."""
        manager.start()
        result = manager.stop()
        assert result is True
        assert manager.is_running() is False

    def test_stop_not_running(self, manager):
        """Test stopping when not running."""
        result = manager.stop()
        assert result is False

    def test_is_running(self, manager):
        """Test is_running method."""
        assert manager.is_running() is False
        manager.start()
        assert manager.is_running() is True
        manager.stop()
        assert manager.is_running() is False

    def test_get_statistics(self, manager, sample_session):
        """Test getting statistics."""
        stats = manager.get_statistics()
        assert stats["slides_stored"] == 0
        assert stats["session_id"] == sample_session.session_id
        assert stats["running"] is False

    def test_handle_slide_unique_event(self, manager, event_bus, sample_capture, sample_session):
        """Test handling SLIDE_UNIQUE event."""
        manager.start()

        # Track events
        stored_events = []

        def capture_stored_event(event: Event):
            stored_events.append(event)

        event_bus.subscribe(EventType.SLIDE_STORED, capture_stored_event)

        # Publish SLIDE_UNIQUE event
        event_bus.publish(Event(
            type=EventType.SLIDE_UNIQUE,
            data={
                "capture": sample_capture,
                "session_id": sample_session.session_id,
                "sequence_number": 1,
                "similarity_score": 0.85
            },
            source="test"
        ))

        # Give a moment for event processing
        time.sleep(0.1)

        # Check that slide was stored
        assert manager.get_statistics()["slides_stored"] == 1

        # Check that SLIDE_STORED event was published
        assert len(stored_events) == 1
        assert stored_events[0].type == EventType.SLIDE_STORED
        assert stored_events[0].data["session_id"] == sample_session.session_id
        assert stored_events[0].data["sequence_number"] == 1

        # Cleanup
        manager.stop()

    def test_ignore_event_from_different_session(self, manager, event_bus, sample_capture):
        """Test that events from different sessions are ignored."""
        manager.start()

        # Publish event from different session
        event_bus.publish(Event(
            type=EventType.SLIDE_UNIQUE,
            data={
                "capture": sample_capture,
                "session_id": "different-session-id",
                "sequence_number": 1,
                "similarity_score": 0.85
            },
            source="test"
        ))

        # Give a moment for event processing
        time.sleep(0.1)

        # No slides should be stored
        assert manager.get_statistics()["slides_stored"] == 0

        # Cleanup
        manager.stop()

    def test_handle_event_without_capture(self, manager, event_bus, sample_session):
        """Test handling event without capture data."""
        manager.start()

        # Track error events
        error_events = []

        def capture_error_event(event: Event):
            error_events.append(event)

        event_bus.subscribe(EventType.STORAGE_ERROR, capture_error_event)

        # Publish event without capture
        event_bus.publish(Event(
            type=EventType.SLIDE_UNIQUE,
            data={
                "session_id": sample_session.session_id,
                "sequence_number": 1
                # Missing "capture" field
            },
            source="test"
        ))

        # Give a moment for event processing
        time.sleep(0.1)

        # No slides should be stored
        assert manager.get_statistics()["slides_stored"] == 0

        # Cleanup
        manager.stop()

    def test_store_multiple_slides(self, manager, event_bus, sample_session):
        """Test storing multiple slides."""
        manager.start()

        # Create and store 5 slides
        for i in range(5):
            image = Image.new("RGB", (100, 100), color=(i * 50, 0, 0))
            capture = RawCapture(
                image=image,
                timestamp=time.time(),
                monitor_id=1,
                width=100,
                height=100
            )

            event_bus.publish(Event(
                type=EventType.SLIDE_UNIQUE,
                data={
                    "capture": capture,
                    "session_id": sample_session.session_id,
                    "sequence_number": i + 1,
                    "similarity_score": 0.9
                },
                source="test"
            ))

        # Give a moment for event processing
        time.sleep(0.2)

        # Check that all slides were stored
        assert manager.get_statistics()["slides_stored"] == 5

        # Cleanup
        manager.stop()

    def test_get_session(self, manager, sample_session):
        """Test getting the session."""
        session = manager.get_session()
        assert session == sample_session
        assert session.session_id == sample_session.session_id

    def test_get_slides(self, manager, event_bus, sample_session, sample_capture):
        """Test getting slides."""
        manager.start()

        # Store a slide
        event_bus.publish(Event(
            type=EventType.SLIDE_UNIQUE,
            data={
                "capture": sample_capture,
                "session_id": sample_session.session_id,
                "sequence_number": 1,
                "similarity_score": 0.85
            },
            source="test"
        ))

        # Give a moment for event processing
        time.sleep(0.1)

        # Get slides
        slides = manager.get_slides()
        assert len(slides) == 1
        assert slides[0].session_id == sample_session.session_id
        assert slides[0].sequence_number == 1

        # Cleanup
        manager.stop()

    def test_get_slides_with_limit(self, manager, event_bus, sample_session):
        """Test getting slides with limit."""
        manager.start()

        # Store 5 slides
        for i in range(5):
            image = Image.new("RGB", (100, 100), color="blue")
            capture = RawCapture(
                image=image,
                timestamp=time.time(),
                monitor_id=1,
                width=100,
                height=100
            )

            event_bus.publish(Event(
                type=EventType.SLIDE_UNIQUE,
                data={
                    "capture": capture,
                    "session_id": sample_session.session_id,
                    "sequence_number": i + 1,
                    "similarity_score": 0.9
                },
                source="test"
            ))

        # Give a moment for event processing
        time.sleep(0.2)

        # Get slides with limit
        slides = manager.get_slides(limit=3)
        assert len(slides) == 3

        # Cleanup
        manager.stop()

    def test_get_slides_not_running(self, manager):
        """Test getting slides when manager is not running."""
        slides = manager.get_slides()
        assert slides == []

    def test_session_total_slides_updated_on_stop(self, manager, event_bus, sample_session, sample_capture):
        """Test that session total_slides is updated when stopping."""
        manager.start()

        # Store a slide
        event_bus.publish(Event(
            type=EventType.SLIDE_UNIQUE,
            data={
                "capture": sample_capture,
                "session_id": sample_session.session_id,
                "sequence_number": 1,
                "similarity_score": 0.85
            },
            source="test"
        ))

        # Give a moment for event processing
        time.sleep(0.1)

        # Stop manager
        manager.stop()

        # Session should be updated with slide count
        assert sample_session.total_slides == 1

    def test_slide_metadata_preserved(self, manager, event_bus, sample_session):
        """Test that capture metadata is preserved in stored slide."""
        manager.start()

        # Create capture with metadata
        image = Image.new("RGB", (100, 100), color="blue")
        capture = RawCapture(
            image=image,
            timestamp=time.time(),
            monitor_id=2,
            width=100,
            height=100,
            metadata={"custom_key": "custom_value"}
        )

        # Track stored events
        stored_events = []

        def capture_stored_event(event: Event):
            stored_events.append(event)

        event_bus.subscribe(EventType.SLIDE_STORED, capture_stored_event)

        # Store slide
        event_bus.publish(Event(
            type=EventType.SLIDE_UNIQUE,
            data={
                "capture": capture,
                "session_id": sample_session.session_id,
                "sequence_number": 1,
                "similarity_score": 0.95
            },
            source="test"
        ))

        # Give a moment for event processing
        time.sleep(0.1)

        # Check stored slide has metadata
        assert len(stored_events) == 1
        stored_slide = stored_events[0].data["slide"]
        assert stored_slide.metadata == {"custom_key": "custom_value"}

        # Cleanup
        manager.stop()

    def test_error_handling(self, manager, event_bus, sample_session):
        """Test error handling when storage fails."""
        manager.start()

        # Track error events
        error_events = []

        def capture_error_event(event: Event):
            error_events.append(event)

        event_bus.subscribe(EventType.STORAGE_ERROR, capture_error_event)

        # Create invalid capture (e.g., with None image)
        capture = RawCapture(
            image=None,  # Invalid
            timestamp=time.time(),
            monitor_id=1,
            width=100,
            height=100
        )

        # Try to store
        event_bus.publish(Event(
            type=EventType.SLIDE_UNIQUE,
            data={
                "capture": capture,
                "session_id": sample_session.session_id,
                "sequence_number": 1,
                "similarity_score": 0.85
            },
            source="test"
        ))

        # Give a moment for event processing
        time.sleep(0.1)

        # Error event should be published
        assert len(error_events) >= 1
        assert error_events[0].type == EventType.STORAGE_ERROR
        assert error_events[0].data["source"] == "storage_manager"

        # No slides should be stored
        assert manager.get_statistics()["slides_stored"] == 0

        # Cleanup
        manager.stop()
