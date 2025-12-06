"""Tests for the event bus."""

import pytest
from core.bus.event_bus import EventBus
from core.interfaces.events import Event, EventType


class TestEventBus:
    """Test cases for EventBus."""

    def test_singleton(self):
        """Test that EventBus is a singleton."""
        bus1 = EventBus()
        bus2 = EventBus()
        assert bus1 is bus2

    def test_subscribe_and_publish(self):
        """Test subscribing and publishing events."""
        bus = EventBus()
        received_events = []

        def handler(event: Event):
            received_events.append(event)

        # Subscribe to event type
        bus.subscribe(EventType.SLIDE_CAPTURED, handler)

        # Publish event
        event = Event(
            type=EventType.SLIDE_CAPTURED,
            data={"slide_id": "test123"},
            source="test"
        )
        bus.publish(event)

        # Verify handler was called
        assert len(received_events) == 1
        assert received_events[0].type == EventType.SLIDE_CAPTURED
        assert received_events[0].data["slide_id"] == "test123"

    def test_multiple_subscribers(self):
        """Test that multiple subscribers receive the same event."""
        bus = EventBus()
        received1 = []
        received2 = []

        def handler1(event: Event):
            received1.append(event)

        def handler2(event: Event):
            received2.append(event)

        bus.subscribe(EventType.SLIDE_UNIQUE, handler1)
        bus.subscribe(EventType.SLIDE_UNIQUE, handler2)

        event = Event(type=EventType.SLIDE_UNIQUE, data={})
        bus.publish(event)

        assert len(received1) == 1
        assert len(received2) == 1

    def test_unsubscribe(self):
        """Test unsubscribing from events."""
        bus = EventBus()
        received = []

        def handler(event: Event):
            received.append(event)

        bus.subscribe(EventType.SESSION_STARTED, handler)
        bus.unsubscribe(EventType.SESSION_STARTED, handler)

        event = Event(type=EventType.SESSION_STARTED, data={})
        bus.publish(event)

        assert len(received) == 0

    def test_event_history(self):
        """Test that event history is maintained."""
        bus = EventBus()
        bus.clear_history()

        event1 = Event(type=EventType.SESSION_CREATED, data={"id": "1"})
        event2 = Event(type=EventType.SESSION_STARTED, data={"id": "2"})

        bus.publish(event1)
        bus.publish(event2)

        history = bus.get_history(limit=10)
        assert len(history) >= 2
