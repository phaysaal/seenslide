"""Tests for deduplication engine."""

import pytest
import time
from unittest.mock import Mock
from PIL import Image

from modules.dedup.engine import DeduplicationEngine
from modules.dedup.strategies.hash_strategy import HashDeduplicationStrategy
from core.bus.event_bus import EventBus
from core.interfaces.events import Event, EventType
from core.models.session import Session
from core.models.slide import RawCapture


class TestDeduplicationEngine:
    """Test cases for DeduplicationEngine."""

    @pytest.fixture
    def strategy(self):
        """Create a hash strategy for testing."""
        strategy = HashDeduplicationStrategy()
        strategy.initialize({"hash_algorithm": "md5"})
        return strategy

    @pytest.fixture
    def session(self):
        """Create a test session."""
        return Session(
            name="Test Session",
            dedup_strategy="hash"
        )

    @pytest.fixture
    def event_bus(self):
        """Create a fresh event bus for testing."""
        bus = EventBus()
        bus.clear_history()
        return bus

    def test_initialization(self, strategy, session):
        """Test engine initialization."""
        engine = DeduplicationEngine(strategy, session)
        assert engine is not None
        assert engine.is_running() is False

    def test_start_engine(self, strategy, session, event_bus):
        """Test starting the engine."""
        engine = DeduplicationEngine(strategy, session, event_bus)
        result = engine.start()

        assert result is True
        assert engine.is_running() is True

        # Clean up
        engine.stop()

    def test_stop_engine(self, strategy, session, event_bus):
        """Test stopping the engine."""
        engine = DeduplicationEngine(strategy, session, event_bus)
        engine.start()

        result = engine.stop()
        assert result is True
        assert engine.is_running() is False

    def test_double_start(self, strategy, session, event_bus):
        """Test that starting already running engine returns False."""
        engine = DeduplicationEngine(strategy, session, event_bus)
        engine.start()

        result = engine.start()
        assert result is False

        engine.stop()

    def test_stop_not_running(self, strategy, session, event_bus):
        """Test that stopping non-running engine returns False."""
        engine = DeduplicationEngine(strategy, session, event_bus)
        result = engine.stop()
        assert result is False

    def test_first_slide_always_unique(self, strategy, session, event_bus):
        """Test that first slide is always marked as unique."""
        engine = DeduplicationEngine(strategy, session, event_bus)
        received_events = []

        def handler(event):
            received_events.append(event)

        event_bus.subscribe(EventType.SLIDE_UNIQUE, handler)
        engine.start()

        # Publish a capture event
        image = Image.new("RGB", (100, 100), color="red")
        capture = RawCapture(
            image=image,
            timestamp=time.time(),
            monitor_id=1,
            width=100,
            height=100
        )

        event_bus.publish(Event(
            type=EventType.SLIDE_CAPTURED,
            data={
                "session_id": session.session_id,
                "capture_id": capture.capture_id,
                "capture": capture,
            },
            source="test"
        ))

        # Give it a moment to process
        time.sleep(0.1)

        # Should have one SLIDE_UNIQUE event
        assert len(received_events) > 0
        assert received_events[0].type == EventType.SLIDE_UNIQUE

        engine.stop()

    def test_identical_slides_marked_duplicate(self, strategy, session, event_bus):
        """Test that identical slides are marked as duplicates."""
        engine = DeduplicationEngine(strategy, session, event_bus)
        unique_events = []
        duplicate_events = []

        def unique_handler(event):
            unique_events.append(event)

        def duplicate_handler(event):
            duplicate_events.append(event)

        event_bus.subscribe(EventType.SLIDE_UNIQUE, unique_handler)
        event_bus.subscribe(EventType.SLIDE_DUPLICATE, duplicate_handler)
        engine.start()

        # Create two identical captures
        image = Image.new("RGB", (100, 100), color="red")
        capture1 = RawCapture(
            image=image.copy(),
            timestamp=time.time(),
            monitor_id=1,
            width=100,
            height=100
        )
        capture2 = RawCapture(
            image=image.copy(),
            timestamp=time.time(),
            monitor_id=1,
            width=100,
            height=100
        )

        # Publish first capture
        event_bus.publish(Event(
            type=EventType.SLIDE_CAPTURED,
            data={
                "session_id": session.session_id,
                "capture": capture1,
            },
            source="test"
        ))

        time.sleep(0.1)

        # Publish second capture (identical)
        event_bus.publish(Event(
            type=EventType.SLIDE_CAPTURED,
            data={
                "session_id": session.session_id,
                "capture": capture2,
            },
            source="test"
        ))

        time.sleep(0.1)

        # First should be unique, second should be duplicate
        assert len(unique_events) == 1
        assert len(duplicate_events) == 1

        engine.stop()

    def test_different_slides_marked_unique(self, strategy, session, event_bus):
        """Test that different slides are both marked as unique."""
        engine = DeduplicationEngine(strategy, session, event_bus)
        unique_events = []

        def unique_handler(event):
            unique_events.append(event)

        event_bus.subscribe(EventType.SLIDE_UNIQUE, unique_handler)
        engine.start()

        # Create two different captures
        image1 = Image.new("RGB", (100, 100), color="red")
        image2 = Image.new("RGB", (100, 100), color="blue")
        capture1 = RawCapture(
            image=image1,
            timestamp=time.time(),
            monitor_id=1,
            width=100,
            height=100
        )
        capture2 = RawCapture(
            image=image2,
            timestamp=time.time(),
            monitor_id=1,
            width=100,
            height=100
        )

        # Publish both captures
        event_bus.publish(Event(
            type=EventType.SLIDE_CAPTURED,
            data={"session_id": session.session_id, "capture": capture1},
            source="test"
        ))
        time.sleep(0.1)

        event_bus.publish(Event(
            type=EventType.SLIDE_CAPTURED,
            data={"session_id": session.session_id, "capture": capture2},
            source="test"
        ))
        time.sleep(0.1)

        # Both should be unique
        assert len(unique_events) == 2

        engine.stop()

    def test_get_statistics(self, strategy, session, event_bus):
        """Test that statistics are tracked correctly."""
        engine = DeduplicationEngine(strategy, session, event_bus)
        engine.start()

        # Create and publish captures
        image = Image.new("RGB", (100, 100), color="red")
        for i in range(3):
            capture = RawCapture(
                image=image.copy(),
                timestamp=time.time(),
                monitor_id=1,
                width=100,
                height=100
            )
            event_bus.publish(Event(
                type=EventType.SLIDE_CAPTURED,
                data={"session_id": session.session_id, "capture": capture},
                source="test"
            ))
            time.sleep(0.05)

        time.sleep(0.1)
        stats = engine.get_statistics()

        assert stats["total_captures"] == 3
        assert stats["unique_slides"] == 1  # First is unique
        assert stats["duplicate_slides"] == 2  # Others are duplicates
        assert stats["strategy"] == "hash"
        assert stats["running"] is True

        engine.stop()

    def test_ignores_different_session(self, strategy, session, event_bus):
        """Test that engine ignores captures from different sessions."""
        engine = DeduplicationEngine(strategy, session, event_bus)
        unique_events = []

        def unique_handler(event):
            unique_events.append(event)

        event_bus.subscribe(EventType.SLIDE_UNIQUE, unique_handler)
        engine.start()

        # Publish capture for different session
        image = Image.new("RGB", (100, 100), color="red")
        capture = RawCapture(
            image=image,
            timestamp=time.time(),
            monitor_id=1,
            width=100,
            height=100
        )

        event_bus.publish(Event(
            type=EventType.SLIDE_CAPTURED,
            data={
                "session_id": "different-session-id",
                "capture": capture,
            },
            source="test"
        ))

        time.sleep(0.1)

        # Should not process it
        assert len(unique_events) == 0

        engine.stop()
